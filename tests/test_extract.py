"""Tests the extract module."""

from hashlib import md5
from pathlib import Path

import polars as pl
import pytest

from chat_extract.extract import (
    extract_data_from_video,
    ChatTextExtractor,
    to_polars,
    cleanup_df,
)
from chat_extract.models import Message, MessageList

# --------------------- Test main function ---------------------


@pytest.mark.asyncio
async def test_extract_data_from_video(tmp_path, monkeypatch):
    """
    Test that extract_data_from_video calls the extraction process,
    converts the results to a Polars DataFrame, cleans up the data,
    and writes the expected CSV output.
    """
    # Set a dummy API key for proper initialization.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")

    # Create a dummy video file.
    dummy_video = tmp_path / "dummy_video.mp4"
    dummy_video.write_bytes(b"dummy video content")

    # Specify an output CSV file.
    output_csv = tmp_path / "output.csv"

    # Create dummy message objects.
    dummy_message = Message(
        sender="Alice", message="Hello", timestamp="2022-01-01 12:00:00"
    )
    dummy_message_list = MessageList(messages=[dummy_message])

    # Patch ChatTextExtractor.extract_from_video to bypass actual video processing
    # and simply return our dummy message list.
    async def fake_extract_from_video(
        self, video_path, n  # pylint: disable=unused-argument
    ):
        return [dummy_message_list]

    monkeypatch.setattr(
        ChatTextExtractor, "extract_from_video", fake_extract_from_video
    )

    # Call the function under test.
    await extract_data_from_video(dummy_video, output_csv, n=1)

    # Verify that the output CSV file exists.
    assert output_csv.exists()

    # Read the CSV file using Polars and verify its contents.
    df = pl.read_csv(str(output_csv))
    # Since we only have one dummy message, we expect one row with three columns.
    assert df.height == 1
    row = df.row(0)
    # By default, the DataFrame should have columns "sender", "message", and "timestamp"
    # because dummy_message.model_dump returns a dict with these keys.
    assert row[0] == "Alice"
    assert row[1] == "Hello"
    assert row[2] == "2022-01-01 12:00:00"


# --------------------- Test ChatTextExtractor initialization ---------------------
def test_chat_text_extractor_no_api_key(monkeypatch):
    """Test that ChatTextExtractor raises an error if no API key is set."""
    # Remove the API key environment variable if it exists
    monkeypatch.delenv("OPENAI_API_KEY", raising=False)

    # Patch load_dotenv to return False so that it does not load any .env file
    monkeypatch.setattr("chat_extract.extract.load_dotenv", lambda: False)

    with pytest.raises(ValueError):
        ChatTextExtractor()


# --------------------- Test extract_from_frame ---------------------
@pytest.mark.asyncio
async def test_extract_from_frame(tmp_path, monkeypatch, mocker):
    """Test the extract_from_frame method of ChatTextExtractor."""
    # Set a dummy API key so that extractor initialization passes.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")

    # Create a dummy image file.
    image_file = tmp_path / "dummy_image.png"
    image_file.write_bytes(b"dummy_image_content")

    extractor = ChatTextExtractor()

    # Patch the encode_image function so that it returns a dummy base64 string.
    fake_encoded = "dummy_base64"
    encode_patch = mocker.patch(
        "chat_extract.extract.encode_image", return_value=fake_encoded
    )

    # Create a dummy message list that will be returned by the API call.
    dummy_message = Message(
        sender="Alice", message="Hello", timestamp="2022-01-01 12:34:56"
    )
    dummy_message_list = MessageList(messages=[dummy_message])

    async def fake_create(*args, **kwargs):  # pylint: disable=unused-argument
        return dummy_message_list

    # Patch the API client's chat.completions.create method.
    client_patch = mocker.patch.object(
        extractor.client.chat.completions, "create", side_effect=fake_create
    )

    # Call the asynchronous extraction for one frame.
    result = await extractor.extract_from_frame(image_file)

    # Check that the image file was encoded correctly.
    encode_patch.assert_called_once_with(image_file)

    # Verify that the API was called (the details of the call parameters
    # can be inspected if needed).
    client_patch.assert_called_once()

    # Verify that the returned value is our dummy message list.
    assert result == dummy_message_list


# --------------------- Test extract_from_video ---------------------
@pytest.mark.asyncio
async def test_extract_from_video(tmp_path, monkeypatch, mocker):
    """Test the extract_from_video method of ChatTextExtractor."""
    # Set a dummy API key.
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    extractor = ChatTextExtractor()

    # Create a dummy video file.
    video_file = tmp_path / "dummy_video.mp4"
    video_file.write_bytes(b"dummy video content")

    # Compute the expected hash-based subdirectory.
    video_hash = md5(video_file.as_posix().encode("utf-8")).hexdigest()
    frames_dir = extractor.storage_dir / "frames" / video_hash

    # Patch extract_frames (imported in the module’s global namespace)
    # with a fake that creates dummy frame files.
    def fake_extract_frames(
        video_path, n, frames_path  # pylint: disable=unused-argument
    ):
        # Ensure the frames directory exists
        frames_path.mkdir(parents=True, exist_ok=True)
        dummy_frame_files = []
        for i in range(3):
            frame_path = frames_path / f"frame_{i}.jpg"
            # Create a dummy frame file
            frame_path.write_text(f"frame {i} data")
            dummy_frame_files.append(frame_path)
        return dummy_frame_files

    extract_frames_patch = mocker.patch(
        "chat_extract.extract.extract_frames",
        side_effect=fake_extract_frames,
    )

    # Patch extract_from_frame so that each frame returns a dummy message list.
    async def fake_extract_from_frame(image_path: Path):
        return {"frame": image_path.name}

    extract_from_frame_patch = mocker.patch.object(
        extractor, "extract_from_frame", side_effect=fake_extract_from_frame
    )

    # Call extract_from_video with a dummy n value.
    result = await extractor.extract_from_video(video_file, n=1)

    # Verify that extract_frames was called with the correct parameters.
    extract_frames_patch.assert_called_once()

    # Verify that extract_from_frame was called for each dummy frame (3 calls expected).
    assert extract_from_frame_patch.call_count == 3

    # Verify that the returned list of message lists has the same length and sorted order.
    expected = [{"frame": f"frame_{i}.jpg"} for i in range(3)]
    assert result == expected

    # Verify that each dummy frame file has been deleted (i.e. unlinked).
    for i in range(3):
        frame_file = frames_dir / f"frame_{i}.jpg"
        assert not frame_file.exists()


@pytest.mark.asyncio
async def test_extract_from_video_frames_dir_does_not_exist(
    tmp_path, monkeypatch, mocker
):
    """Test extract_from_video when the frames directory doesn't exist yet."""
    # Ensure API key is present so that extractor initialization passes
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    extractor = ChatTextExtractor()

    # Create a dummy video file
    video_file = tmp_path / "dummy_video_no_dir.mp4"
    video_file.write_bytes(b"dummy video content")

    # Compute the path where frames would be stored, but do NOT create the directory
    video_hash = md5(video_file.as_posix().encode("utf-8")).hexdigest()
    frames_dir = extractor.storage_dir / "frames" / video_hash
    # Intentionally do NOT create frames_dir—this ensures we hit the else branch

    # Patch extract_frames so it creates three dummy frame files
    def fake_extract_frames(
        video_path, n, frames_path  # pylint: disable=unused-argument
    ):
        frames_path.mkdir(parents=True, exist_ok=True)
        dummy_frames = []
        for i in range(3):
            frame_path = frames_path / f"frame_{i}.jpg"
            frame_path.write_text(f"frame {i} data")
            dummy_frames.append(frame_path)
        return dummy_frames

    mocker.patch("chat_extract.extract.extract_frames", side_effect=fake_extract_frames)

    # Patch extract_from_frame
    async def fake_extract_from_frame(frame_path: Path):
        return {"frame": frame_path.name}

    mocker.patch.object(
        extractor, "extract_from_frame", side_effect=fake_extract_from_frame
    )

    # Run extraction
    result = await extractor.extract_from_video(video_file, n=1)

    # We expect 3 frames extracted, then removed
    expected = [{"frame": f"frame_{i}.jpg"} for i in range(3)]
    assert result == expected

    # Verify the directory now exists (created by extract_frames)
    assert frames_dir.exists()

    # Ensure all frames are removed after extraction
    for i in range(3):
        frame_file = frames_dir / f"frame_{i}.jpg"
        assert not frame_file.exists(), f"{frame_file} was not removed"


@pytest.mark.asyncio
async def test_extract_from_video_frames_dir_exists_with_files(
    tmp_path, monkeypatch, mocker
):
    """
    Test extract_from_video when the frames directory already
    exists and has pre-existing files.
    """
    # Ensure API key is present so that extractor initialization passes
    monkeypatch.setenv("OPENAI_API_KEY", "dummy_key")
    extractor = ChatTextExtractor()

    # Create a dummy video file
    video_file = tmp_path / "dummy_video_with_dir.mp4"
    video_file.write_bytes(b"dummy video content")

    # Compute the path for frames
    video_hash = md5(video_file.as_posix().encode("utf-8")).hexdigest()
    frames_dir = extractor.storage_dir / "frames" / video_hash
    frames_dir.mkdir(parents=True, exist_ok=True)

    # Create some pre-existing files in the frames directory
    pre_existing_files = []
    for i in range(2):
        f = frames_dir / f"pre_existing_{i}.jpg"
        f.write_text(f"pre-existing file {i}")
        pre_existing_files.append(f)

    # Patch extract_frames so it creates three new dummy frames
    def fake_extract_frames(
        video_path, n, frames_path  # pylint: disable=unused-argument
    ):
        # At this point, frames_path already exists and has pre-existing files
        dummy_frames = []
        for i in range(3):
            frame_path = frames_path / f"frame_{i}.jpg"
            frame_path.write_text(f"frame {i} data")
            dummy_frames.append(frame_path)
        return dummy_frames

    mocker.patch("chat_extract.extract.extract_frames", side_effect=fake_extract_frames)

    # Patch extract_from_frame
    async def fake_extract_from_frame(frame_path: Path):
        return {"frame": frame_path.name}

    mocker.patch.object(
        extractor, "extract_from_frame", side_effect=fake_extract_from_frame
    )

    # Run extraction
    result = await extractor.extract_from_video(video_file, n=1)

    # Verify we got back 3 frames
    expected = [{"frame": f"frame_{i}.jpg"} for i in range(3)]
    assert result == expected

    # Check that all pre-existing files were removed
    for f in pre_existing_files:
        assert not f.exists(), f"{f} was not removed by extract_from_video"

    # Check that newly extracted frames were also removed
    for i in range(3):
        frame_file = frames_dir / f"frame_{i}.jpg"
        assert not frame_file.exists(), f"{frame_file} was not removed"


# --------------------- Test to_polars ---------------------
def test_to_polars():
    """Test the to_polars function."""
    dummy_message = Message(
        sender="Bob", message="Hi there", timestamp="2022-02-02 14:00:00"
    )
    dummy_message_list = MessageList(messages=[dummy_message])
    df = to_polars([dummy_message_list])
    # Check that the DataFrame contains the expected columns.
    assert set(df.columns) >= {"sender", "message", "timestamp"}
    row = df.to_dicts()[0]
    assert row["sender"] == "Bob"
    assert row["message"] == "Hi there"
    assert row["timestamp"] == "2022-02-02 14:00:00"


# --------------------- Test cleanup_df ---------------------
def test_cleanup_df():
    """Test the cleanup_df function."""
    # Create a sample DataFrame with placeholder values, duplicates, and an entirely null row.
    data = [
        {
            "sender": "<sender_name>",
            "message": "<message_text>",
            "timestamp": "<timestamp>",
        },
        {"sender": "Alice", "message": "Hello", "timestamp": "2022-01-01 12:00:00"},
        {
            "sender": "<sender_name>",
            "message": "<message_text>",
            "timestamp": "<timestamp>",
        },
        {
            "sender": "Alice",
            "message": "Hello",
            "timestamp": "2022-01-01 12:00:00",
        },  # duplicate
        {"sender": None, "message": None, "timestamp": None},  # entirely null row
        {"sender": "Bob", "message": "Hi", "timestamp": None},
    ]
    df = pl.DataFrame(data)
    cleaned_df = cleanup_df(df)
    # After cleanup:
    # - All placeholders become null.
    # - Rows that are entirely null are removed.
    # - Duplicate rows are removed.
    # So we expect only:
    #   {"sender": "Alice", "message": "Hello", "timestamp": "2022-01-01 12:00:00"}
    #   {"sender": "Bob", "message": "Hi", "timestamp": None}
    result_dicts = cleaned_df.to_dicts()
    expected = [
        {"sender": "Alice", "message": "Hello", "timestamp": "2022-01-01 12:00:00"},
        {"sender": "Bob", "message": "Hi", "timestamp": None},
    ]
    assert result_dicts == expected
