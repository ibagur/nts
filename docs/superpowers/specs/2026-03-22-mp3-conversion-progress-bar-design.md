# MP3 Conversion Progress Bar — Design Spec

**Date:** 2026-03-22
**Status:** Approved

## Problem

When `nts` converts a downloaded audio file to MP3 (via `--mp3`), the conversion can take tens of seconds with no visible feedback. The terminal prints `Converting to MP3...` and then goes silent until done, leaving the user uncertain whether the tool is working or hanging.

## Goal

Show a real percentage progress bar during audio format conversion so the user can see how far along the conversion is at any point.

## Scope

- Applies to all conversions in `convert_audio_format()`: MP3 (re-encode) and OGG (stream copy)
- Progress bar always visible, even when `--quiet` / `-q` is active (tqdm writes to stderr by default, stdout is never contaminated)
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

Add `tqdm` to `install_requires` in `setup.py`. Pin to a specific version for consistency with the project's other pinned dependencies:
```python
'tqdm==4.66.4',
```

### 2. Import

Add to `nts/downloader.py`:
```python
from tqdm import tqdm
```
(`re` is already imported)

### 3. `convert_audio_format()` changes

The entire conversion block stays inside the existing `try/except ffmpeg.Error` handler.
Replace the `.run(capture_stdout=True, capture_stderr=True)` call with the following (all within the existing try block):

```python
# Get total duration for the progress bar.
# KeyError/ValueError fallback: if duration is missing (e.g. corrupt or
# container-less file), tqdm shows a spinner instead of a percentage bar.
probe = ffmpeg.probe(old_file_path)
try:
    duration = float(probe['format']['duration'])
except (KeyError, ValueError):
    duration = None

# run_async with pipe_stderr=True, pipe_stdout=False (default),
# pipe_stdin=False (default). ffmpeg-python 0.2.0 does not pipe stdout or
# stdin unless explicitly requested, so no deadlock risk.
process = (
    ffmpeg.input(old_file_path)
    .output(new_file_path, **ffmpeg_kwargs)
    .run_async(pipe_stderr=True, overwrite_output=True)
)

time_pattern = re.compile(r'time=(\d+):(\d+):(\d+\.\d+)')

# Accumulate stderr lines for use in error reporting if ffmpeg fails.
stderr_lines = []
with tqdm(total=duration, unit='s', unit_scale=True,
          desc=f'Converting to {target_format.upper()}',
          miniters=1) as pbar:
    prev = 0.0
    for line in process.stderr:
        line = line.decode('utf-8', errors='replace')
        stderr_lines.append(line)
        match = time_pattern.search(line)
        if match:
            h, m, s = int(match.group(1)), int(match.group(2)), float(match.group(3))
            current = h * 3600 + m * 60 + s
            pbar.update(current - prev)
            prev = current

process.wait()

# Raise so the existing except ffmpeg.Error handler catches it.
# Pass accumulated stderr so the handler can print actual ffmpeg error output.
if process.returncode != 0:
    raise ffmpeg.Error('ffmpeg', None, ''.join(stderr_lines).encode())
```

### 4. Remove the old print

Remove the line:
```python
if not quiet:
    print(f'Converting to {target_format.upper()}...')
```
The tqdm bar's `desc` replaces it. The `if not quiet: print(...)` on the unsupported-format early-return path (~line 319) is **not** removed — only this one print is affected.

### 5. Error handling

No structural changes. `ffmpeg.probe()` is inside the `try/except ffmpeg.Error` block, so probe failures are caught the same way as conversion failures. The `ffmpeg.Error('ffmpeg', None, ...)` constructor uses positional arguments matching the `(cmd, stdout, stderr)` signature. The existing `e.stderr.decode()` in the except handler will receive the real accumulated ffmpeg output rather than a generic string.

### 6. `quiet` flag

The tqdm bar is unconditional. tqdm writes to `sys.stderr` by default, so stdout is never polluted. Users running in CI or piping stdout will not see noise. If a future requirement asks to suppress the bar in quiet mode, add `disable=quiet` to the tqdm constructor — out of scope here.

## Data Flow

```
convert_audio_format() called
  → [try block]
  → ffmpeg.probe() → get total duration (seconds), fallback to None
  → ffmpeg run_async(pipe_stderr=True, pipe_stdout=False, pipe_stdin=False)
  → loop: read stderr line → accumulate in stderr_lines → parse time= → tqdm.update(delta)
  → process.wait() → check returncode
  → if non-zero: raise ffmpeg.Error with accumulated stderr → caught by existing except
  → verify output file exists and has content
  → remove original on success
  → return (new_file_path, new_ext)
```

## Non-Goals

- No changes to yt-dlp download progress (already handled by yt-dlp itself)
- No changes to OGG-specific behavior (stream copy still uses same function, just completes fast)
- No new CLI flags
