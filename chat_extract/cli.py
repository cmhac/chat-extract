"""Defines a command-line-interface (CLI) for the chat_extract package."""

import asyncio
from pathlib import Path

import click

from chat_extract.extract import extract_data_from_video


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--output-path",
    type=click.Path(),
    default=None,
    help="Output file to save the extracted data.",
)
@click.option(
    "--n",
    type=int,
    default=10,
    help="Save every nth frame.",
)
def cli(video_path: str, output_path: str, n: int) -> None:
    """Extract text from a video file and save it to a csv file.

    Args:
        video_path (str): Path to the video file.
        output (str): Path to the output csv file.
    """
    video_path = Path(video_path)
    output_path = Path(output_path) if output_path else None

    # if the output path is not provided, use the name of the video file with a .csv extension
    if output_path is None:
        output_path = video_path.with_suffix(".csv")

    # run the extraction in an asyncio event loop
    asyncio.run(
        extract_data_from_video(
            video_path=video_path,
            output_path=output_path,
            n=n,
        )
    )
