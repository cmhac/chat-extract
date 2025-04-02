"""Uses the OpenAI API to extract text from a screenshot of a group chat."""

import asyncio
import base64
import os
from pathlib import Path
import re
import typing as T

import aiofiles
import cv2
from dotenv import load_dotenv
from openai import AsyncOpenAI
import orjson
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_incrementing,
)
from tqdm.asyncio import tqdm_asyncio


class OpenAIResponseError(Exception):
    """Custom exception for OpenAI API response errors."""


async def extract_data_from_video(
    video_path: T.Union[str, Path], output_path: T.Union[str, Path]
) -> T.Dict[str, T.Any]:
    """Extracts text from the video at the given path using OpenAI's API."""
    frame_dir = Path("frames")
    if not frame_dir.exists():
        os.makedirs(frame_dir)

    # frames dir must be empty
    if any(frame_dir.iterdir()):
        confirm = input(
            "Frames directory is not empty. Do you want to delete its contents? (y/n): "
        )
        if confirm.strip().lower() == "y":
            for file in frame_dir.iterdir():
                file.unlink()
        else:
            raise ValueError(
                "Frames directory must be empty. Please delete existing frames first."
            )

    # Extract frames from the video
    extract_frames(video_path, 30, frame_dir)

    # Get the list of frames
    frames = sorted(frame_dir.glob("*.png"))
    if not frames:
        raise ValueError("No frames found in the directory")

    # Set up OpenAI client
    dotenv_loaded = load_dotenv()
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError(
            "OPENAI_API_KEY not found in environment variables. "
            f".env file loaded: {dotenv_loaded}"
        )
    client = AsyncOpenAI(api_key=api_key)

    # Process each frame concurrently with a limit of 10 at a time
    semaphore = asyncio.Semaphore(10)

    async def process_frame(frame: Path):
        async with semaphore:
            try:
                data = await extract_data_from_image(frame, client)
            except Exception as e:  # pylint: disable=broad-except
                print(f"Error processing frame {frame}: {e}")
                data = None
            finally:
                os.remove(frame)
        return data

    tasks = [process_frame(frame) for frame in frames]
    extracted_results = await tqdm_asyncio.gather(*tasks)

    # Filter out any None results and combine the extracted data
    extracted_data = []
    for data in extracted_results:
        if data is None:
            continue
        if isinstance(data, list):
            extracted_data.extend(data)
        else:
            extracted_data.append(data)

    # Clean up the frames directory
    os.rmdir(frame_dir)

    # Save the combined data to a JSON file
    output_path = Path(output_path)
    if not output_path.parent.exists():
        os.makedirs(output_path.parent)

    async with aiofiles.open(output_path, "w") as output_file:
        await output_file.write(orjson.dumps(extracted_data).decode("utf-8"))


PROMPT = """
    You will extract text from a screenshot of a group chat. The screenshot will be provided as an image.

    Your task is to identify the participants in the chat and extract their messages, including the time and date of each message.
    The output should be a JSON object that is a list of dictionaries, where each dictionary represents a message.

    The json object should have the following structure:
    [
        {
            "sender": "<sender_name>",
            "message": "<message_text>",
            "timestamp": "<timestamp>"
        },
        ...
    ]

    If any any message's metadata is not available, you should set the value to None.
    The sender's name should be the name of the person who sent the message.
    The message text should be the text of the message.
    The timestamp should be the time and date when the message was sent.
    The timestamp should be in the format YYYY-MM-DD HH:MM:SS.
    If an exact timestamp is not available, use whatever is available.
"""


@retry(
    retry=retry_if_exception_type(OpenAIResponseError),
    stop=stop_after_attempt(3),
    wait=wait_incrementing(start=1, increment=10, max=50),
)
async def extract_data_from_image(
    image_path: T.Union[str, Path], client: AsyncOpenAI
) -> T.Dict[str, T.Any]:
    """Extracts text from the image at the given path using OpenAI's API."""
    # Call OpenAI's API to extract data
    response = await client.responses.create(
        model="gpt-4o-mini",
        input=[
            {
                "role": "developer",
                "content": [{"type": "input_text", "text": PROMPT}],
            },
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": "\n"},
                    {
                        "type": "input_image",
                        "image_url": f"data:image/png;base64,{encode_image(image_path)}",
                    },
                ],
            },
        ],
        text={"format": {"type": "json_object"}},
        tools=[],
        store=True,
    )
    data = get_json(response)
    return data


def encode_image(image_path: Path):
    """Encodes the image at the given path as a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_json_from_text(response_text: str) -> T.Dict[str, T.Any]:
    """Extracts the JSON object from the given OpenAI response."""
    json_match = re.search(r"\{.*\}", response_text)
    if json_match is None:
        raise OpenAIResponseError(
            "Extraction failed with fallback method. JSON object not found."
        )

    return orjson.loads(json_match.group(0))


def get_json(response: T.Any, output_index: int = 0) -> T.Dict[str, T.Any]:
    """Extracts the JSON object from the given OpenAI response."""
    try:
        response_text = response.output[output_index].content[0].text
        try:
            json_data = orjson.loads(response_text)
        except orjson.JSONDecodeError:
            # try to extract JSON object from the response
            json_data = extract_json_from_text(response_text)

    except (AttributeError, IndexError, OpenAIResponseError) as exc:
        raise OpenAIResponseError(
            f"Failed to extract JSON object from OpenAI response: {response}"
        ) from exc

    return json_data


def extract_frames(
    video_path: T.Union[str, Path], n: int, output_folder: T.Union[str, Path]
) -> None:
    """
    Extracts every nth frame from the video at video_path and saves them to output_folder.

    Parameters:
        video_path (str): Path to the video file.
        n (int): Save every nth frame.
        output_folder (str): Directory where the frames will be saved.

    Returns:
        int: The number of frames saved.
    """
    video_path = Path(video_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)  # pylint: disable=no-member
    frame_count = 0
    saved_count = 0

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Save the frame if it's an nth frame
        if frame_count % n == 0:
            frame_filename = os.path.join(output_folder, f"frame_{frame_count:06d}.png")
            cv2.imwrite(frame_filename, frame)  # pylint: disable=no-member
            saved_count += 1

        frame_count += 1

    cap.release()
