# MP3 Conversion Progress Bar — Design Spec

**Date:** 2026-03-22
**Status:** Approved

## Problem

When `nts` converts a downloaded audio file to MP3 (via `--mp3`), the conversion can take tens of seconds with no visible feedback. The terminal prints `Converting to MP3...` and then goes silent until done, leaving the user uncertain whether the tool is working or hanging.

## Goal

Show a real percentage progress bar during audio format conversion so the user can see how far along the conversion is at any point.

## Scope

- Applies to all conversions in `convert_audio_format()`: MP3 (re-encode) and OGG (stream copy)
- Progress bar always visible, even when `--quiet` / `-q` is active
- No changes to function signature or return values
- No changes to error handling logic

## Approach

**tqdm + ffmpeg.probe() + run_async(pipe_stderr=True)**

ffmpeg writes real-time progress lines to stderr in the format:
```
frame=  432 fps=200 q=-0.0 size=    3072kB time=00:00:18.05 bitrate=1394.0kbits/s speed=8.36x
```

We parse `time=HH:MM:SS.ss` to get the current position, compare it to the total duration from `ffmpeg.probe()`, and drive a tqdm progress bar.

## Implementation

### 1. Dependency

Add `tqdm` to `install_requires` in `setup.py`:
```python
'tqdm>=4.0.0',
```

### 2. Import

Add to `nts/downloader.py`:
```python
import re
from tqdm import tqdm
```
(`re` is already imported)

### 3. `convert_audio_format()` changes

Replace the `.run(capture_stdout=True, capture_stderr=True)` block with:

```python
# Get total duration for progress calculation
probe = ffmpeg.probe(old_file_path)
duration = float(probe['format']['duration'])

# Run async with stderr piped for real-time progress parsing
process = (
    ffmpeg.input(old_file_path)
    .output(new_file_path, **ffmpeg_kwargs)
    .run_async(pipe_stderr=True, overwrite_output=True)
)

time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')

with tqdm(total=duration, unit='s', unit_scale=True,
          desc=f'Converting to {target_format.upper()}',
          bar_format='{l_bar}{bar}| {n:.1f}/{total:.1f}s [{elapsed}<{remaining}]') as pbar:
    prev = 0.0
    for line in process.stderr:
        line = line.decode('utf-8', errors='replace')
        match = time_pattern.search(line)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
            current = h * 3600 + m * 60 + s
            pbar.update(current - prev)
            prev = current

process.wait()

if process.returncode != 0:
    raise ffmpeg.Error('ffmpeg', stdout=None, stderr=b'non-zero return code')
```

### 4. Error handling

Wrap the async block in the same `try/except ffmpeg.Error` and `except Exception` already present. The `process.wait()` returncode check maps to the existing error path.

### 5. `quiet` flag

The existing `if not quiet: print(f'Converting to {target_format.upper()}...')` line is removed (the tqdm bar's `desc` replaces it). The tqdm bar itself is unconditional — it always renders.

## Data Flow

```
convert_audio_format() called
  → ffmpeg.probe() → get total duration (seconds)
  → ffmpeg run_async(pipe_stderr=True)
  → loop: read stderr line → parse time= → tqdm.update(delta)
  → process.wait() → check returncode
  → verify output file exists and has content
  → remove original on success
  → return (new_file_path, new_ext)
```

## Non-Goals

- No changes to yt-dlp download progress (already handled by yt-dlp itself)
- No changes to OGG-specific behavior (stream copy still uses same function, just completes fast)
- No new CLI flags
