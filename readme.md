# NTS Radio downloader

Downloads [NTS](https://www.nts.live) episodes (with metadata) for offline listening.

<img src="https://i.postimg.cc/fRfNN8Y6/nts-header.png" />

## Installation

First install all the requirements.

```sh
pip3 install nts-everdrone
```

## Usage

```
Usage: nts [options] args

Options:
  -h, --help            show this help message and exit
  -o DIR, --out-dir=DIR
                        where the files will be downloaded, defaults to
                        ~/Downloads on macOS and %USERPROFILE%\Downloads
  -v, --version         print the version number and quit
  -q, --quiet           only print errors
  --mp3                 convert downloaded files to MP3 format (320kbps)
```

Just paste the episode url and it will be downloaded in your Downloads folder.

```sh
nts https://www.nts.live/shows/myshow/episodes/myepisode
```

Alternatively, you can pass a show/host url to download all its episodes.

```sh
nts https://www.nts.live/shows/myshow
```

If you have multiple urls, write them into a file line by line and pass the file to the script.
Show urls will be expanded and downloaded as well.

```sh
nts links.txt
```

You can also pass files and urls (shows or episodes) at the same time

```sh
nts links.txt https://www.nts.live/shows/myshow
```

To change the output directory use the `--out-dir` option, or the `-o` shorthand

```sh
nts -o ~/Desktop/NTS links.txt
```

### MP3 Conversion

By default, episodes are downloaded in their original format (usually `.m4a`) or converted to `.ogg` for certain formats. Use the `--mp3` flag to convert all downloads to high-quality MP3 format:

```sh
# Download and convert to MP3 (320kbps)
nts --mp3 https://www.nts.live/shows/myshow/episodes/myepisode

# Download entire show as MP3
nts --mp3 https://www.nts.live/shows/myshow

# Combine with other options
nts --mp3 -o ~/Desktop/NTS -q https://www.nts.live/shows/myshow
```

**Note:** MP3 conversion requires [FFmpeg](https://ffmpeg.org/) to be installed on your system.

- **macOS**: `brew install ffmpeg`
- **Linux**: `sudo apt install ffmpeg`
- **Windows**: Download from [ffmpeg.org](https://ffmpeg.org/download.html)
