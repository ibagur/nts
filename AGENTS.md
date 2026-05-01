# AGENTS.md

Guidance for coding agents working in this repository.

## Project Overview

This repository contains `nts-everdrone`, a Python CLI tool for downloading NTS Radio episodes with metadata for offline listening. It supports individual episode URLs, entire show URLs, and batch downloads from a text file containing URLs.

## Development Commands

### Setup

```bash
pip install -e .
```

Or, using Pipenv:

```bash
pipenv install
```

### Running the CLI

```bash
nts https://www.nts.live/shows/myshow/episodes/myepisode
python -m nts https://www.nts.live/shows/myshow
nts -o ~/Desktop/NTS links.txt
nts -q https://www.nts.live/shows/myshow
nts --mp3 https://www.nts.live/shows/myshow/episodes/myepisode
nts --mp3 -o ~/Desktop/NTS -q https://www.nts.live/shows/myshow
```

Be careful when verifying CLI behavior: real episode/show URLs trigger network requests and audio downloads. Prefer help/version checks, focused unit-style calls, temporary output directories, or mocks unless the user explicitly wants a real download.

### Building

```bash
python -m pip install --upgrade pip
python -m pip install -U build
python -m build
```

### Publishing

PyPI publishing is handled by `.github/workflows/pythonpublish.yml` when a GitHub release is created. The workflow builds the package and publishes through PyPI trusted publishing/OIDC.

## Architecture

### Entry Points

- `nts/cli.py`: Main console entry point for the `nts` command.
- `nts/__main__.py`: Allows `python -m nts`.
- `nts/downloader.py`: Core NTS API parsing, audio source resolution, download, conversion, and metadata tagging.
- `setup.py`: Package metadata and `console_scripts` entry point.

### Main Flow

```text
User input (URL/file + options)
  -> nts/cli.py parses arguments
  -> episode URL: nts.downloader.download(...)
  -> show URL: nts.downloader.get_episodes_of_show(...) then download each episode
  -> downloader fetches NTS HTML and API JSON
  -> audio source is resolved from mixcloud/audio_sources, with Mixcloud search fallback
  -> yt-dlp downloads the audio
  -> ffmpeg optionally converts the audio
  -> music-tag writes metadata
```

### Audio Source Selection

The downloader should prefer NTS-provided `audio_sources` URLs before falling back to the episode `mixcloud` URL. This avoids stale Mixcloud links taking precedence over a valid SoundCloud source.

Source priority:

1. First valid URL in `api_data["audio_sources"]`
2. `api_data["mixcloud"]`
3. Mixcloud search fallback through `mixcloud_try(...)`

For SoundCloud URLs, prefer progressive MP3 formats before HLS formats in `yt-dlp` options:

```text
http_mp3_128/http_mp3/hls_mp3_128/hls_mp3/bestaudio/best
```

This prevents `yt-dlp` from choosing SoundCloud HLS AAC by default, which can delegate downloading to FFmpeg and produce very verbose segment-by-segment terminal output.

### Important Functions

- `download(url, quiet, save_dir, save=True, mp3_format=False)` in `nts/downloader.py`: Main download orchestrator.
- `parse_nts_data(bs, api_data)` in `nts/downloader.py`: Extracts metadata from the NTS API response and page HTML.
- `get_episodes_of_show(show_name)` in `nts/downloader.py`: Fetches all published episodes for a show through the paginated NTS API.
- `get_audio_link(api_data, parsed)` in `nts/downloader.py`: Selects the preferred download URL.
- `get_ytdlp_options(save_dir, file_name, quiet=False)` in `nts/downloader.py`: Builds `yt-dlp` options, including format priority.
- `convert_audio_format(old_file_path, file_name, save_dir, target_format='ogg', quiet=False)` in `nts/downloader.py`: Converts audio to OGG or MP3 using FFmpeg.
- `set_metadata(file_path, parsed, image, image_type)` in `nts/downloader.py`: Writes tags to the downloaded audio file.

## Audio Conversion Behavior

Default behavior:

- `.webm` and `.opus` downloads are converted to `.ogg` using stream copy.
- Other formats are kept as downloaded.

With `--mp3`:

- Non-MP3 downloads are converted to `.mp3` using `libmp3lame`, 320 kbps, 44.1 kHz.
- Existing MP3 files are left as MP3.

Conversion failures keep the original downloaded file and print a warning unless quiet mode is enabled.

## Dependencies

Core runtime dependencies include:

- `yt-dlp`: Audio download backend.
- `requests`: NTS and Mixcloud API requests.
- `beautifulsoup4`: HTML parsing, currently used for artist extraction.
- `music-tag` and `mutagen`: Metadata tagging.
- `ffmpeg-python`: FFmpeg integration.
- `pillow`: Image-related dependency.
- `tqdm`: Conversion progress display.

System FFmpeg must be installed for conversion features to work.

## Versioning

When bumping the package version, update both:

- `nts/downloader.py` (`__version__`)
- `setup.py` (`version=...`)

## Testing Notes

There is currently no dedicated test suite in the repository. For small changes, use targeted checks such as:

```bash
python -m nts --help
python -m nts --version
python -m compileall nts
```

For downloader behavior, prefer isolated tests or mocks around network, filesystem, `yt-dlp`, and FFmpeg behavior. Avoid committing downloaded media or local generated artifacts.

## Repository Hygiene

- Keep changes narrowly scoped.
- Do not modify generated packaging metadata in `nts_everdrone.egg-info/` unless the user explicitly asks.
- Avoid committing local/tooling artifacts such as `.DS_Store`, `.codegraph/`, or `.serena/`.
- Preserve existing public CLI behavior unless the task explicitly asks to change it.
