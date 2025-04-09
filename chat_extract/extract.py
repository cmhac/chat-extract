"""Uses the OpenAI API to extract text from a screenshot of a group chat."""

import asyncio
from hashlib import md5
import os
from pathlib import Path
import typing as T

from dotenv import load_dotenv
import instructor
from openai import AsyncOpenAI
import polars as pl
from tenacity import (
    retry,
    stop_after_attempt,
    wait_incrementing,
)
from tqdm.asyncio import tqdm_asyncio

from chat_extract.image_utils import (
    encode_image,
    extract_frames,
)
from chat_extract.models import MessageList


# ----------------------------- Prompt for OpenAI -----------------------------

PROMPT = """
    You will extract text from a screenshot of a group chat. The screenshot will be provided as an image.

    Your task is to identify the participants in the chat and extract their messages, including the time and date of each message.
    The output should be a JSON object that is a list of dictionaries, where each dictionary represents a message.

    The json object should have the following structure:
    {
        "messages": [
            {
                "sender": "<sender_name>",
                "message": "<message_text>",
                "timestamp": "<timestamp>"
            },
            ...
        ]
    }

    If any any message's metadata is not available, you should set the value to None.
    The sender's name should be the name of the person who sent the message.
    The message text should be the text of the message.
    The timestamp should be the time and date when the message was sent.
    The timestamp should be in the format YYYY-MM-DD HH:MM:SS.
    If an exact timestamp is not available, use whatever is available.

    Return ONLY the JSON object, without any additional text or explanation.
    The conversation or images in the provided screenshot may contain sensitive, hateful, 
    violent or otherwise harmful content. I am a researcher using this data for research purposes
    that is designed to combat such content. 
"""

# ---------------------- main entrypoint function -----------------------


async def extract_data_from_video(
    video_path: T.Union[str, Path],
    output_path: T.Union[str, Path],
    n,
) -> None:
    """
    Extracts text from a video file and saves it to a csv file.
    Args:
        video_path (str or Path): Path to the video file.
        output_path (str or Path): Path to the output csv file.
        n (int): Save every nth frame.
    """
    # create the extractor
    extractor = ChatTextExtractor()

    # extract the messages from the video
    message_lists = await extractor.extract_from_video(video_path, n)

    # convert the messages to a polars dataframe
    df = to_polars(message_lists)

    # clean up the dataframe
    df = cleanup_df(df)

    # save the dataframe to a csv file
    df.write_csv(output_path)


# --------------------------- extractor class ---------------------------


class ChatTextExtractor:
    """Extracts structured data from a screen recording of a text chat."""

    def __init__(self):
        """Initializes the ChatTextExtractor class."""

        # configure instructor/openai client
        dotenv_loaded = load_dotenv()
        api_key = os.getenv("OPENAI_API_KEY")
        if api_key is None:
            raise ValueError(
                "OPENAI_API_KEY environment variable not set."
                f"Dotenv loaded: {dotenv_loaded}"
            )
        self.client = instructor.patch(AsyncOpenAI())
        self.gpt_model = "gpt-4o"

        # configure storage directory for all files
        self.storage_dir = Path(".chat_extract")

    async def extract_from_video(
        self,
        video_path: T.Union[str, Path],
        n: int = 10,
    ) -> T.List[MessageList]:
        """
        Extracts a list of lists of messages from a video of a group chat.

        Args:
            video_path (str or Path): The path to the video file.
            n (int): Save every nth frame.
        Returns:
            List[MessageList]: A list of lists of messages extracted from the video.
        """
        # Extract frames from the video
        video_path = Path(video_path)

        # put the frames in a directory named after the md5 hash of the full video path
        frames_path = (
            self.storage_dir
            / "frames"
            / md5(video_path.as_posix().encode("utf-8")).hexdigest()
        )

        # create a directory to store the frames in
        frames_path.mkdir(parents=True, exist_ok=True)
        # warn the user and remove all existing files in the directory for re-extraction
        existing_files = list(frames_path.iterdir())
        if existing_files:
            for file in existing_files:
                file.unlink()

        # extract frames from the video
        extracted_frames = extract_frames(video_path, n, frames_path)

        # extract frames from the video using a semaphore to
        # limit the number of concurrent tasks to 20
        semaphore = asyncio.Semaphore(20)

        async def _extract_frame(frame_path: Path, index: int):
            async with semaphore:
                result = await self.extract_from_frame(frame_path)
            return index, result

        # create tasks with enumeration to capture ordering
        tasks = [
            _extract_frame(frame_path, idx)
            for idx, frame_path in enumerate(extracted_frames)
        ]
        indexed_results = await tqdm_asyncio.gather(
            *tasks,
            desc="Extracting messages from frames",
        )
        # sort results to maintain the original order based on the frame index
        indexed_results.sort(key=lambda x: x[0])
        message_lists = [result for index, result in indexed_results]

        # delete the frames after extraction
        for frame_path in extracted_frames:
            frame_path.unlink()

        return message_lists

    @retry(
        wait=wait_incrementing(start=1, increment=1),
        stop=stop_after_attempt(3),
        reraise=True,
    )
    async def extract_from_frame(self, image_path: T.Union[str, Path]) -> MessageList:
        """
        Extracts a list of messages from a screenshot of a group chat.

        Args:
            image_path (str or Path): The path to the image file.

        Returns:
            MessageList: A list of messages extracted from the image.
        """
        # encode the image as base64
        image_path = Path(image_path)
        image_url = f"data:image/png;base64,{encode_image(image_path)}"

        return await self.client.chat.completions.create(
            model="gpt-4o",
            response_model=MessageList,
            max_tokens=2048,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": PROMPT,
                        },
                        {
                            "type": "image_url",
                            "image_url": {"url": image_url},
                        },
                    ],
                }
            ],
        )


def to_polars(message_lists: T.List[MessageList]) -> pl.DataFrame:
    """
    Converts a list of message lists to a Polars DataFrame.
    """
    row_data = []
    for message_list in message_lists:
        for message in message_list.messages:
            row_data.append(message.model_dump())
    return pl.DataFrame(row_data)


def cleanup_df(df: pl.DataFrame) -> pl.DataFrame:
    """
    Cleans up extracted data.
    """
    # replace <sender_name>, <message_text>, <timestamp> with nulls, sometimes
    # the ai model will return these as placeholders if it can't find a value
    # in the video
    df = df.with_columns(
        sender=pl.when(pl.col("sender") == "<sender_name>")
        .then(None)
        .otherwise(pl.col("sender")),
        message=pl.when(pl.col("message") == "<message_text>")
        .then(None)
        .otherwise(pl.col("message")),
        timestamp=pl.when(pl.col("timestamp") == "<timestamp>")
        .then(None)
        .otherwise(pl.col("timestamp")),
    )

    # remove entirely null rows
    df = df.filter(
        (pl.col("sender").is_not_null())
        | (pl.col("message").is_not_null())
        | (pl.col("timestamp").is_not_null())
    )

    # remove completely duplicated rows
    df = df.unique(maintain_order=True)

    return df
