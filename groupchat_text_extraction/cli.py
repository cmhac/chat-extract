"""Defines a command-line-interface (CLI) for the groupchat_text_extraction package."""

import asyncio
import click

from groupchat_text_extraction.main import extract_data_from_video


@click.command()
@click.argument("video_path", type=click.Path(exists=True))
@click.option(
    "--output-path",
    type=click.Path(),
    default="extracted_data.csv",
    help="Output file to save the extracted data.",
)
def cli(video_path: str, output_path: str) -> None:
    """Extract text from a video file and save it to a csv file.

    Args:
        video_path (str): Path to the video file.
        output (str): Path to the output csv file.
    """
    asyncio.run(extract_data_from_video(video_path, output_path))
