"""Tests the image_utils module."""

import base64

from chat_extract.image_utils import encode_image, extract_frames


def test_encode_image(tmp_path):
    """Tests the encode_image function."""
    file_content = b"test image data"
    file_path = tmp_path / "test_image.jpg"
    file_path.write_bytes(file_content)

    result = encode_image(file_path)
    expected = base64.b64encode(file_content).decode("utf-8")
    assert result == expected


def test_extract_frames(tmp_path, mocker):
    """Tests the extract_frames function, mocking the video capture and image writing."""

    # Prepare fake frame data and an iterator.
    frames = [
        (True, "frame_data_0"),
        (True, "frame_data_1"),
        (True, "frame_data_2"),
        (True, "frame_data_3"),
        (True, "frame_data_4"),
        (False, None),
    ]
    frame_iter = iter(frames)

    class FakeVideoCapture:
        """Fake class to simulate cv2.VideoCapture."""

        def __init__(self, video_path):
            self.video_path = video_path

        def isOpened(self):  # pylint: disable=invalid-name
            """Check if the video capture is opened."""
            return True

        def read(self):
            """Read a frame from the video capture."""
            return next(frame_iter)

        def release(self):
            """Release the video capture."""

    # Patch cv2.VideoCapture and cv2.imwrite
    mocker.patch(
        "chat_extract.image_utils.cv2.VideoCapture",
        return_value=FakeVideoCapture("dummy_video_path"),
    )
    imwrite_mock = mocker.patch(
        "chat_extract.image_utils.cv2.imwrite", return_value=True
    )

    output_folder = tmp_path / "frames_output"
    extracted_paths = extract_frames("dummy_video_path", 2, output_folder)

    # Verify cv2.imwrite was called three times for frames 0, 2, and 4.
    assert imwrite_mock.call_count == 3

    expected_calls = [
        (str(output_folder / "frame_0.jpg"), "frame_data_0"),
        (str(output_folder / "frame_1.jpg"), "frame_data_2"),
        (str(output_folder / "frame_2.jpg"), "frame_data_4"),
    ]
    for call, (expected_path, expected_data) in zip(
        imwrite_mock.call_args_list, expected_calls
    ):
        args, _ = call
        # Compare file path as string and frame data.
        assert str(args[0]) == expected_path
        assert args[1] == expected_data

    # Verify the list of saved frame paths.
    expected_paths = [output_folder / f"frame_{i}.jpg" for i in range(3)]
    assert extracted_paths == expected_paths
