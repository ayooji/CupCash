#!/usr/bin/env python3
"""
Video Clipper - A Python program to clip videos into smaller segments.

This script provides multiple ways to clip videos:
1. Split into equal-duration clips
2. Extract specific time ranges
3. Create clips at regular intervals

Requirements: pip install moviepy

Usage:
    python video_clipper.py <input_video> [options]

Examples:
    # Split video into 30-second clips
    python video_clipper.py input.mp4 --duration 30

    # Extract a specific segment (from 1:30 to 2:45)
    python video_clipper.py input.mp4 --start 1:30 --end 2:45

    # Split into 5 equal parts
    python video_clipper.py input.mp4 --parts 5

    # Extract multiple clips from a timestamps file
    python video_clipper.py input.mp4 --timestamps clips.txt
"""

import argparse
import os
import sys
from pathlib import Path
from typing import List, Tuple, Optional


def parse_time(time_str: str) -> float:
    """
    Parse time string to seconds.

    Supports formats:
        - "90" or "90.5" (seconds)
        - "1:30" (minutes:seconds)
        - "1:30:00" (hours:minutes:seconds)

    Args:
        time_str: Time string to parse

    Returns:
        Time in seconds as float
    """
    parts = time_str.strip().split(':')

    if len(parts) == 1:
        return float(parts[0])
    elif len(parts) == 2:
        minutes, seconds = parts
        return int(minutes) * 60 + float(seconds)
    elif len(parts) == 3:
        hours, minutes, seconds = parts
        return int(hours) * 3600 + int(minutes) * 60 + float(seconds)
    else:
        raise ValueError(f"Invalid time format: {time_str}")


def format_time(seconds: float) -> str:
    """
    Format seconds to readable time string.

    Args:
        seconds: Time in seconds

    Returns:
        Formatted time string (HH:MM:SS or MM:SS)
    """
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = seconds % 60

    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:05.2f}"
    return f"{minutes:02d}:{secs:05.2f}"


def get_video_duration(video_path: str) -> float:
    """
    Get the duration of a video file.

    Args:
        video_path: Path to the video file

    Returns:
        Duration in seconds
    """
    from moviepy.editor import VideoFileClip

    with VideoFileClip(video_path) as video:
        return video.duration


def create_clip(
    input_path: str,
    output_path: str,
    start_time: float,
    end_time: float,
    verbose: bool = True
) -> bool:
    """
    Create a single video clip.

    Args:
        input_path: Path to input video
        output_path: Path for output clip
        start_time: Start time in seconds
        end_time: End time in seconds
        verbose: Print progress messages

    Returns:
        True if successful, False otherwise
    """
    from moviepy.editor import VideoFileClip

    try:
        if verbose:
            print(f"  Creating clip: {format_time(start_time)} -> {format_time(end_time)}")
            print(f"  Output: {output_path}")

        with VideoFileClip(input_path) as video:
            clip = video.subclip(start_time, end_time)
            clip.write_videofile(
                output_path,
                codec='libx264',
                audio_codec='aac',
                verbose=False,
                logger=None
            )

        if verbose:
            print(f"  ✓ Clip created successfully\n")
        return True

    except Exception as e:
        print(f"  ✗ Error creating clip: {e}\n")
        return False


def split_by_duration(
    input_path: str,
    output_dir: str,
    clip_duration: float,
    verbose: bool = True
) -> List[str]:
    """
    Split video into clips of specified duration.

    Args:
        input_path: Path to input video
        output_dir: Directory for output clips
        clip_duration: Duration of each clip in seconds
        verbose: Print progress messages

    Returns:
        List of created clip paths
    """
    video_duration = get_video_duration(input_path)
    input_name = Path(input_path).stem
    extension = Path(input_path).suffix

    clips_created = []
    clip_num = 1
    start_time = 0

    if verbose:
        num_clips = int((video_duration + clip_duration - 1) // clip_duration)
        print(f"\nSplitting into {num_clips} clips of {clip_duration}s each...")
        print(f"Video duration: {format_time(video_duration)}\n")

    while start_time < video_duration:
        end_time = min(start_time + clip_duration, video_duration)
        output_path = os.path.join(
            output_dir,
            f"{input_name}_clip{clip_num:03d}{extension}"
        )

        if create_clip(input_path, output_path, start_time, end_time, verbose):
            clips_created.append(output_path)

        start_time = end_time
        clip_num += 1

    return clips_created


def split_into_parts(
    input_path: str,
    output_dir: str,
    num_parts: int,
    verbose: bool = True
) -> List[str]:
    """
    Split video into a specified number of equal parts.

    Args:
        input_path: Path to input video
        output_dir: Directory for output clips
        num_parts: Number of parts to split into
        verbose: Print progress messages

    Returns:
        List of created clip paths
    """
    video_duration = get_video_duration(input_path)
    clip_duration = video_duration / num_parts

    if verbose:
        print(f"\nSplitting into {num_parts} equal parts...")
        print(f"Video duration: {format_time(video_duration)}")
        print(f"Each part: ~{format_time(clip_duration)}\n")

    input_name = Path(input_path).stem
    extension = Path(input_path).suffix

    clips_created = []

    for i in range(num_parts):
        start_time = i * clip_duration
        end_time = (i + 1) * clip_duration if i < num_parts - 1 else video_duration
        output_path = os.path.join(
            output_dir,
            f"{input_name}_part{i + 1:03d}{extension}"
        )

        if create_clip(input_path, output_path, start_time, end_time, verbose):
            clips_created.append(output_path)

    return clips_created


def extract_range(
    input_path: str,
    output_dir: str,
    start_time: float,
    end_time: Optional[float] = None,
    output_name: Optional[str] = None,
    verbose: bool = True
) -> Optional[str]:
    """
    Extract a specific time range from video.

    Args:
        input_path: Path to input video
        output_dir: Directory for output clip
        start_time: Start time in seconds
        end_time: End time in seconds (None = until end)
        output_name: Custom output filename (without extension)
        verbose: Print progress messages

    Returns:
        Path to created clip, or None if failed
    """
    video_duration = get_video_duration(input_path)

    if end_time is None:
        end_time = video_duration

    if start_time >= video_duration:
        print(f"Error: Start time ({format_time(start_time)}) is beyond video duration ({format_time(video_duration)})")
        return None

    if end_time > video_duration:
        print(f"Warning: End time adjusted to video duration ({format_time(video_duration)})")
        end_time = video_duration

    input_name = Path(input_path).stem
    extension = Path(input_path).suffix

    if output_name:
        output_path = os.path.join(output_dir, f"{output_name}{extension}")
    else:
        start_str = format_time(start_time).replace(':', '-')
        end_str = format_time(end_time).replace(':', '-')
        output_path = os.path.join(
            output_dir,
            f"{input_name}_{start_str}_to_{end_str}{extension}"
        )

    if verbose:
        print(f"\nExtracting range: {format_time(start_time)} -> {format_time(end_time)}\n")

    if create_clip(input_path, output_path, start_time, end_time, verbose):
        return output_path
    return None


def extract_from_timestamps(
    input_path: str,
    output_dir: str,
    timestamps_file: str,
    verbose: bool = True
) -> List[str]:
    """
    Extract multiple clips from a timestamps file.

    File format (each line):
        start_time end_time [optional_name]

    Example:
        0:00 0:30 intro
        1:00 2:30 main_content
        5:00 5:45

    Args:
        input_path: Path to input video
        output_dir: Directory for output clips
        timestamps_file: Path to timestamps file
        verbose: Print progress messages

    Returns:
        List of created clip paths
    """
    clips_created = []
    input_name = Path(input_path).stem
    extension = Path(input_path).suffix

    if verbose:
        print(f"\nProcessing timestamps from: {timestamps_file}\n")

    with open(timestamps_file, 'r') as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            parts = line.split()
            if len(parts) < 2:
                print(f"Warning: Skipping invalid line {line_num}: {line}")
                continue

            try:
                start_time = parse_time(parts[0])
                end_time = parse_time(parts[1])
                clip_name = parts[2] if len(parts) > 2 else f"clip{line_num:03d}"

                output_path = os.path.join(
                    output_dir,
                    f"{input_name}_{clip_name}{extension}"
                )

                if create_clip(input_path, output_path, start_time, end_time, verbose):
                    clips_created.append(output_path)

            except ValueError as e:
                print(f"Warning: Error on line {line_num}: {e}")
                continue

    return clips_created


def main():
    parser = argparse.ArgumentParser(
        description='Clip videos into smaller segments',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
Examples:
  %(prog)s video.mp4 --duration 30
      Split into 30-second clips

  %(prog)s video.mp4 --start 1:30 --end 2:45
      Extract segment from 1:30 to 2:45

  %(prog)s video.mp4 --parts 5
      Split into 5 equal parts

  %(prog)s video.mp4 --timestamps clips.txt
      Extract clips defined in timestamps file

Time formats supported:
  90        (seconds)
  1:30      (minutes:seconds)
  1:30:00   (hours:minutes:seconds)
'''
    )

    parser.add_argument(
        'input',
        help='Input video file path'
    )

    parser.add_argument(
        '-o', '--output-dir',
        default=None,
        help='Output directory (default: same as input file)'
    )

    parser.add_argument(
        '-d', '--duration',
        type=float,
        help='Split into clips of specified duration (seconds)'
    )

    parser.add_argument(
        '-p', '--parts',
        type=int,
        help='Split into specified number of equal parts'
    )

    parser.add_argument(
        '-s', '--start',
        help='Start time for single clip extraction'
    )

    parser.add_argument(
        '-e', '--end',
        help='End time for single clip extraction'
    )

    parser.add_argument(
        '-n', '--name',
        help='Output filename (without extension) for single clip'
    )

    parser.add_argument(
        '-t', '--timestamps',
        help='File containing timestamps for multiple clips'
    )

    parser.add_argument(
        '-q', '--quiet',
        action='store_true',
        help='Suppress progress output'
    )

    args = parser.parse_args()

    # Validate input file
    if not os.path.exists(args.input):
        print(f"Error: Input file not found: {args.input}")
        sys.exit(1)

    # Set output directory
    if args.output_dir:
        output_dir = args.output_dir
        os.makedirs(output_dir, exist_ok=True)
    else:
        output_dir = os.path.dirname(args.input) or '.'

    verbose = not args.quiet

    if verbose:
        print(f"\n{'='*50}")
        print(f"Video Clipper")
        print(f"{'='*50}")
        print(f"Input: {args.input}")
        print(f"Output directory: {output_dir}")

    # Determine operation mode
    clips_created = []

    if args.timestamps:
        # Extract from timestamps file
        if not os.path.exists(args.timestamps):
            print(f"Error: Timestamps file not found: {args.timestamps}")
            sys.exit(1)
        clips_created = extract_from_timestamps(
            args.input, output_dir, args.timestamps, verbose
        )

    elif args.start:
        # Extract single range
        start_time = parse_time(args.start)
        end_time = parse_time(args.end) if args.end else None
        result = extract_range(
            args.input, output_dir, start_time, end_time, args.name, verbose
        )
        if result:
            clips_created = [result]

    elif args.parts:
        # Split into equal parts
        if args.parts < 1:
            print("Error: Number of parts must be at least 1")
            sys.exit(1)
        clips_created = split_into_parts(
            args.input, output_dir, args.parts, verbose
        )

    elif args.duration:
        # Split by duration
        if args.duration <= 0:
            print("Error: Duration must be positive")
            sys.exit(1)
        clips_created = split_by_duration(
            args.input, output_dir, args.duration, verbose
        )

    else:
        print("Error: Please specify an operation mode:")
        print("  --duration SECONDS  : Split into clips of specified duration")
        print("  --parts N          : Split into N equal parts")
        print("  --start TIME       : Extract from start time (optionally with --end)")
        print("  --timestamps FILE  : Extract multiple clips from timestamps file")
        print("\nUse --help for more information")
        sys.exit(1)

    # Summary
    if verbose:
        print(f"{'='*50}")
        print(f"Summary: {len(clips_created)} clip(s) created")
        if clips_created:
            print("\nCreated files:")
            for clip in clips_created:
                print(f"  - {clip}")
        print(f"{'='*50}\n")

    sys.exit(0 if clips_created else 1)


if __name__ == '__main__':
    main()
