"""Utilities for image processing and frame extraction from videos."""

import base64
from pathlib import Path
import typing as T

import cv2


def encode_image(image_path: Path):
    """Encodes the image at the given path as a base64 string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")


def extract_frames(
    video_path: T.Union[str, Path], n: int, output_folder: T.Union[str, Path]
) -> T.List[Path]:
    """
    Extracts every nth frame from the video at video_path and saves them to output_folder.

    Parameters:
        video_path (str): Path to the video file.
        n (int): Save every nth frame.
        output_folder (str): Directory where the frames will be saved.

    Returns:
        List[Path]: List of paths to the saved frames.
    """
    video_path = Path(video_path)
    output_folder = Path(output_folder)
    output_folder.mkdir(parents=True, exist_ok=True)

    cap = cv2.VideoCapture(video_path)  # pylint: disable=no-member
    frame_count = 0
    saved_count = 0

    extracted_frames = []
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        # Save the frame if it's an nth frame
        if frame_count % n == 0:
            frame_filename = output_folder / f"frame_{saved_count}.jpg"
            cv2.imwrite(frame_filename, frame)  # pylint: disable=no-member
            saved_count += 1
            extracted_frames.append(frame_filename)

        frame_count += 1

    cap.release()

    return extracted_frames
