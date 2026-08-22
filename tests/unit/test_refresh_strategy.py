"""Unit tests for pure refresh-strategy helpers (no I/O, no network, no DB)."""

from datetime import UTC, datetime, timedelta

from ayne.data_collection.refresh_strategy import (
    RefreshThresholds,
    has_meaningful_change,
    should_freeze_movie,
)


class TestHasMeaningfulChange:
    def test_first_time_fetch_always_counts_as_change(self):
        assert has_meaningful_change(None, {"budget": 100}, ["budget"]) is True

    def test_no_change_when_values_identical(self):
        before = {"budget": 1000, "revenue": 5000}
        after = {"budget": 1000, "revenue": 5000}
        assert has_meaningful_change(before, after, ["budget", "revenue"]) is False

    def test_change_detected_on_differing_field(self):
        before = {"vote_count": 100}
        after = {"vote_count": 150}
        assert has_meaningful_change(before, after, ["vote_count"]) is True

    def test_small_float_difference_within_tolerance_is_not_a_change(self):
        before = {"vote_average": 7.501}
        after = {"vote_average": 7.502}
        assert has_meaningful_change(before, after, ["vote_average"], float_tolerance=0.01) is False

    def test_float_difference_beyond_tolerance_is_a_change(self):
        before = {"vote_average": 7.0}
        after = {"vote_average": 7.5}
        assert has_meaningful_change(before, after, ["vote_average"], float_tolerance=0.01) is True

    def test_none_to_value_is_a_change(self):
        before = {"status": None}
        after = {"status": "Released"}
        assert has_meaningful_change(before, after, ["status"]) is True

    def test_both_none_is_not_a_change(self):
        before = {"status": None}
        after = {"status": None}
        assert has_meaningful_change(before, after, ["status"]) is False

    def test_ignores_fields_not_in_compare_list(self):
        before = {"budget": 100, "unrelated": "a"}
        after = {"budget": 100, "unrelated": "b"}
        assert has_meaningful_change(before, after, ["budget"]) is False


class TestShouldFreezeMovie:
    def _old_release_date(self) -> datetime:
        return datetime.now(UTC) - timedelta(days=RefreshThresholds.FREEZE_MIN_AGE_DAYS + 10)

    def test_young_movie_is_never_frozen(self):
        recent_release = datetime.now(UTC) - timedelta(days=10)
        assert (
            should_freeze_movie(
                recent_release,
                last_tmdb_update=datetime.now(UTC),
                last_omdb_update=datetime.now(UTC),
                consecutive_unchanged_cycles=99,
            )
            is False
        )

    def test_old_movie_never_updated_is_not_frozen(self):
        assert (
            should_freeze_movie(
                self._old_release_date(),
                last_tmdb_update=None,
                last_omdb_update=None,
                consecutive_unchanged_cycles=99,
            )
            is False
        )

    def test_old_stable_movie_is_frozen(self):
        assert (
            should_freeze_movie(
                self._old_release_date(),
                last_tmdb_update=datetime.now(UTC),
                last_omdb_update=datetime.now(UTC),
                consecutive_unchanged_cycles=RefreshThresholds.FREEZE_STABLE_CYCLES,
            )
            is True
        )

    def test_old_movie_missing_omdb_data_is_not_frozen(self):
        assert (
            should_freeze_movie(
                self._old_release_date(),
                last_tmdb_update=datetime.now(UTC),
                last_omdb_update=None,
                consecutive_unchanged_cycles=RefreshThresholds.FREEZE_STABLE_CYCLES,
            )
            is False
        )

    def test_old_movie_not_yet_stable_is_not_frozen(self):
        assert (
            should_freeze_movie(
                self._old_release_date(),
                last_tmdb_update=datetime.now(UTC),
                last_omdb_update=datetime.now(UTC),
                consecutive_unchanged_cycles=RefreshThresholds.FREEZE_STABLE_CYCLES - 1,
            )
            is False
        )
