import unittest
from unittest.mock import patch

from nts import downloader


class AudioSourceSelectionTest(unittest.TestCase):
    def test_prefers_audio_source_over_mixcloud_when_both_are_available(self):
        api_data = {
            "mixcloud": "https://www.mixcloud.com/NTSRadio/kranky-30th-april-2026/",
            "audio_sources": [
                {
                    "url": "https://soundcloud.com/user-202286394-991268468/kranky-300426",
                    "source": "soundcloud",
                }
            ],
        }

        self.assertEqual(
            downloader.get_audio_link(api_data, {"title": "Kranky"}),
            "https://soundcloud.com/user-202286394-991268468/kranky-300426",
        )

    def test_uses_mixcloud_when_no_audio_sources_are_available(self):
        api_data = {
            "mixcloud": "https://www.mixcloud.com/NTSRadio/some-episode/",
            "audio_sources": [],
        }

        self.assertEqual(
            downloader.get_audio_link(api_data, {"title": "Some Episode"}),
            "https://www.mixcloud.com/NTSRadio/some-episode/",
        )

    def test_searches_mixcloud_when_api_has_no_sources(self):
        with patch.object(
            downloader,
            "mixcloud_try",
            return_value="https://www.mixcloud.com/NTSRadio/found-episode/",
        ) as mixcloud_try:
            self.assertEqual(
                downloader.get_audio_link({}, {"title": "Found Episode"}),
                "https://www.mixcloud.com/NTSRadio/found-episode/",
            )

        mixcloud_try.assert_called_once_with({"title": "Found Episode"})


class YoutubeDLOptionsTest(unittest.TestCase):
    def test_prefers_progressive_audio_formats_before_hls(self):
        options = downloader.get_ytdlp_options("/tmp/downloads", "Kranky")

        self.assertEqual(
            options["format"],
            "http_mp3_128/http_mp3/hls_mp3_128/hls_mp3/bestaudio/best",
        )


class DownloadedFileSelectionTest(unittest.TestCase):
    def test_ignores_partial_download_files(self):
        files = [
            "Kranky - 2026-4-29.aac.part",
            "Kranky - 2026-4-29.mp3",
            "Other Episode.mp3",
        ]

        self.assertEqual(
            downloader.get_downloaded_files(files, "Kranky - 2026-4-29"),
            ["Kranky - 2026-4-29.mp3"],
        )


if __name__ == "__main__":
    unittest.main()
