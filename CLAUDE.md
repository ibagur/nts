# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NTS Radio downloader - a Python CLI tool for downloading NTS Radio episodes with metadata for offline listening. Supports downloading individual episodes, entire shows, or batch downloads from a file list.

## Development Commands

### Setup
```bash
# Install package in editable mode with dependencies
pip install -e .

# Or using pipenv
pipenv install
```

### Running the CLI
```bash
# Run directly (after installation)
nts https://www.nts.live/shows/myshow/episodes/myepisode

# Run as module
python -m nts https://www.nts.live/shows/myshow

# With options
nts -o ~/Desktop/NTS links.txt
nts -q https://www.nts.live/shows/myshow  # quiet mode
nts --mp3 https://www.nts.live/shows/myshow/episodes/myepisode  # convert to MP3 (320kbps)

# Combined options
nts --mp3 -o ~/Desktop/NTS -q https://www.nts.live/shows/myshow
```

### Building for Distribution
```bash
python -m pip install --upgrade pip
python -m pip install -U build
python -m build
```

### Publishing
Package is published to PyPI automatically via GitHub Actions when a release is created. The workflow uses trusted publishing (OIDC) for authentication.

## Architecture

### Entry Points & Flow

1. **CLI Entry (`nts/cli.py`)**: Main entry point via `nts` command
   - Parses command-line arguments (URLs, files, options)
   - Uses regex to distinguish between episode URLs and show URLs
   - For show URLs, fetches all episodes via API and recursively processes them
   - For episode URLs, calls downloader directly
   - For files, reads URLs line-by-line and processes each

2. **Downloader (`nts/downloader.py`)**: Core download and metadata handling
   - Fetches episode data from both HTML page and NTS API (`https://nts.live/api/v2/...`)
   - Attempts to find audio source from Mixcloud or SoundCloud
   - Downloads using `yt-dlp`
   - Optionally converts to MP3 (320kbps) or OGG format using ffmpeg
   - Embeds rich metadata (artists, genres, tracklist, artwork) into audio files

### Key Functions

- `download(url, quiet, save_dir, save=True, mp3_format=False)` in `nts/downloader.py:57`: Main download orchestrator
- `parse_nts_data(bs, api_data)` in `nts/downloader.py:146`: Extracts metadata from NTS API response
- `get_episodes_of_show(show_name)` in `nts/downloader.py:228`: Fetches all episodes for a show via paginated API
- `convert_audio_format(old_file_path, file_name, save_dir, target_format='ogg', quiet=False)` in `nts/downloader.py:270`: Converts audio files to MP3 or OGG format with error handling
- `set_metadata(file_path, parsed, image, image_type)` in `nts/downloader.py:342`: Writes ID3/metadata tags to audio files
- `url_matcher(url)` in `nts/cli.py:59`: Recursive function that routes URLs to appropriate handlers

### Data Flow

```
User Input (URL/File + Options)
  → CLI Parser (cli.py)
    → URL Type Detection (Episode vs Show)
      → Episode: download(mp3_format=...) directly
      → Show: get_episodes_of_show() → recursive url_matcher for each episode
        → HTML + API Fetch
          → Audio Source Discovery (Mixcloud/SoundCloud)
            → yt-dlp Download
              → Format Conversion Decision:
                 • With --mp3: convert all to MP3 (320kbps) via convert_audio_format()
                 • Without --mp3: convert .webm/.opus to OGG (stream copy)
                 • Skip if already target format
                → Metadata Embedding
```

### Audio Format Conversion

The tool supports flexible audio format conversion:

**Default Behavior (no --mp3 flag):**
- `.webm`/`.opus` → `.ogg` (stream copy, no re-encoding)
- Other formats → kept as-is

**With --mp3 Flag:**
- All formats → `.mp3` at 320kbps CBR (libmp3lame encoder, 44.1kHz)
- Already `.mp3` → no conversion (optimization)

**Error Handling:**
- FFmpeg failures → keeps original file, prints warning
- Disk space issues → graceful fallback
- All conversions verify output file before removing original

### Dependencies

- **yt-dlp**: Downloads audio from Mixcloud/SoundCloud
- **beautifulsoup4** + **cssutils**: HTML parsing (minimal usage, mostly for artist extraction)
- **requests**: HTTP requests to NTS API
- **music-tag**: Metadata tagging (supports multiple formats)
- **mutagen**: Low-level metadata handling
- **ffmpeg-python**: Audio format conversion
- **pillow**: Image processing for album artwork

### API Usage

NTS API endpoint pattern: `https://www.nts.live/api/v2/shows/{show_name}/episodes/{episode_alias}`

Key API response fields:
- `name`: Episode title
- `broadcast`: ISO datetime
- `mixcloud`/`audio_sources`: Audio URLs
- `media.picture_large`: Artwork URL
- `genres`: Array of genre objects
- `embeds.tracklist.results`: Track listing

### Version Management

Version is defined in `nts/downloader.py` as `__version__ = '1.3.8'` and must be updated in both:
- `nts/downloader.py:16`
- `setup.py:5`
