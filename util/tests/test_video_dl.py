import pytest

from musabi_util.video_dl import (
    DownloadProgress,
    VideoDlError,
    duration_matches,
    parse_ids,
    pick_best,
)


class TestParseIds:
    def test_plain_lines(self):
        assert parse_ids("123-abc\n456-def\n") == ["123-abc", "456-def"]

    def test_strips_comments_and_blanks(self):
        text = "\n".join(
            [
                "# 済み",
                "123-abc",
                "",
                "  456-def  # メモ",
                "   ",
                "789-ghi",
            ]
        )
        assert parse_ids(text) == ["123-abc", "456-def", "789-ghi"]

    def test_dedupes_preserving_order(self):
        assert parse_ids("a\nb\na\n") == ["a", "b"]

    def test_empty(self):
        assert parse_ids("") == []
        assert parse_ids("# 全部コメント\n\n") == []


class TestPickBest:
    def _entry(self, resolution, width, height, url=None):
        return {
            "url": url or f"https://cdn.example/{resolution}.m3u8",
            "resolution": resolution,
            "width": width,
            "height": height,
            "duration_ms": 1470400,
        }

    def test_picks_widest_from_main(self):
        payload = {
            "trial": [self._entry("sd", 640, 360)],
            "main": [
                self._entry("sd", 640, 360),
                self._entry("fhd", 1920, 1080),
                self._entry("hd", 1280, 720),
            ],
        }
        video = pick_best(payload)
        assert video.width == 1920
        assert video.resolution == "fhd"

    def test_ignores_trial_even_when_larger(self):
        # 体験版の方が高解像度でも、尺の短いサンプルなので選んではいけない。
        payload = {
            "trial": [self._entry("fhd", 1920, 1080, "https://cdn.example/trial.m3u8")],
            "main": [self._entry("sd", 640, 360, "https://cdn.example/main.m3u8")],
        }
        assert pick_best(payload).url == "https://cdn.example/main.m3u8"

    def test_does_not_order_by_resolution_string(self):
        # "sd" > "fhd" は文字列比較だと真になる。数値で比較していることを確かめる。
        payload = {
            "main": [self._entry("sd", 640, 360), self._entry("fhd", 1920, 1080)]
        }
        assert pick_best(payload).resolution == "fhd"

    def test_ties_broken_by_height(self):
        payload = {"main": [self._entry("a", 1920, 800), self._entry("b", 1920, 1080)]}
        assert pick_best(payload).height == 1080

    def test_missing_main_raises(self):
        with pytest.raises(VideoDlError, match="main"):
            pick_best({"trial": [self._entry("sd", 640, 360)]})

    def test_empty_main_raises(self):
        with pytest.raises(VideoDlError, match="main"):
            pick_best({"main": []})

    def test_entry_without_url_raises(self):
        with pytest.raises(VideoDlError, match="url"):
            pick_best({"main": [{"resolution": "fhd", "width": 1920, "height": 1080}]})

    def test_tolerates_missing_numeric_fields(self):
        payload = {"main": [{"url": "https://cdn.example/x.m3u8"}]}
        video = pick_best(payload)
        assert (video.width, video.height, video.duration_ms) == (0, 0, 0)


class TestDurationMatches:
    def test_exact(self):
        assert duration_matches(1470.4, 1470400)

    def test_within_tolerance(self):
        assert duration_matches(1469.0, 1470400, tol_s=2.0)
        assert duration_matches(1472.0, 1470400, tol_s=2.0)

    def test_outside_tolerance(self):
        assert not duration_matches(1468.0, 1470400, tol_s=2.0)

    def test_truncated_download_is_rejected(self):
        # 体験版（20 秒）を本編と取り違えた場合を確実に弾く。
        assert not duration_matches(20.0, 1470400)

    def test_skips_check_when_expected_unknown(self):
        assert duration_matches(12.3, 0)


class TestDownloadProgress:
    def test_uses_fragments_when_available(self):
        p = DownloadProgress("123-abc")
        p.hook({"status": "downloading", "fragment_count": 245, "fragment_index": 10})
        assert p.by_fragment
        assert p.bar is not None
        assert p.bar.total == 245
        assert p.bar.n == 10
        p.close()

    def test_falls_back_to_bytes_without_fragment_count(self):
        p = DownloadProgress("123-abc")
        p.hook(
            {
                "status": "downloading",
                "downloaded_bytes": 1024,
                "total_bytes": 4096,
            }
        )
        assert not p.by_fragment
        assert p.bar is not None
        assert (p.bar.total, p.bar.n) == (4096, 1024)
        p.close()

    def test_accepts_estimated_total(self):
        p = DownloadProgress("123-abc")
        p.hook(
            {
                "status": "downloading",
                "downloaded_bytes": 10,
                "total_bytes_estimate": 500,
            }
        )
        assert p.bar is not None
        assert p.bar.total == 500
        p.close()

    def test_reuses_one_bar_across_updates(self):
        p = DownloadProgress("123-abc")
        p.hook({"status": "downloading", "fragment_count": 3, "fragment_index": 1})
        first = p.bar
        p.hook({"status": "downloading", "fragment_count": 3, "fragment_index": 2})
        assert p.bar is first
        assert p.bar is not None
        assert p.bar.n == 2
        p.close()

    def test_finished_closes_bar(self):
        p = DownloadProgress("123-abc")
        p.hook({"status": "downloading", "fragment_count": 3, "fragment_index": 1})
        p.hook({"status": "finished"})
        assert p.bar is None

    def test_error_closes_bar(self):
        p = DownloadProgress("123-abc")
        p.hook({"status": "downloading", "fragment_count": 3, "fragment_index": 1})
        p.hook({"status": "error"})
        assert p.bar is None

    def test_close_is_idempotent(self):
        p = DownloadProgress("123-abc")
        p.close()
        p.hook({"status": "downloading", "fragment_count": 3, "fragment_index": 1})
        p.close()
        p.close()
        assert p.bar is None

    def test_tolerates_missing_position(self):
        # 進捗値がまだ来ていないフックでも落ちないこと。
        p = DownloadProgress("123-abc")
        p.hook({"status": "downloading", "fragment_count": 3})
        assert p.bar is not None
        assert p.bar.n == 0
        p.close()
