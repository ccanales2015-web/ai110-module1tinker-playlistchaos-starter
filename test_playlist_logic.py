import copy
import random

import pytest

from playlist_logic import (
    DEFAULT_PROFILE,
    build_playlists,
    classify_song,
    compute_playlist_stats,
    lucky_pick,
    merge_playlists,
    search_songs,
)


def make_song(title, artist, energy=5):
    return {"title": title, "artist": artist, "genre": "rock", "energy": energy, "tags": []}


SONGS = [
    make_song("Bohemian Rhapsody", "queen"),
    make_song("Smells Like Teen Spirit", "nirvana"),
    make_song("Feeling Good", "nina simone"),
]


def artists(songs):
    return [song["artist"] for song in songs]


# search_songs


def test_search_matches_prefix():
    assert artists(search_songs(SONGS, "que")) == ["queen"]


def test_search_matches_middle_of_value():
    assert artists(search_songs(SONGS, "simo")) == ["nina simone"]


def test_search_is_case_insensitive():
    assert artists(search_songs(SONGS, "QUE")) == ["queen"]


def test_search_ignores_surrounding_whitespace():
    assert artists(search_songs(SONGS, "  queen  ")) == ["queen"]


def test_search_query_longer_than_value_does_not_match():
    assert search_songs(SONGS, "queen rocks") == []


def test_search_empty_query_returns_all_songs():
    assert search_songs(SONGS, "") == SONGS


def test_search_other_field():
    result = search_songs(SONGS, "SPIRIT", field="title")
    assert [song["title"] for song in result] == ["Smells Like Teen Spirit"]


# compute_playlist_stats


def sample_playlists():
    return {
        "Hype": [make_song("A", "x", energy=9), make_song("B", "y", energy=8)],
        "Chill": [make_song("C", "z", energy=2)],
        "Mixed": [make_song("D", "w", energy=5)],
    }


def test_stats_total_songs_counts_all_playlists():
    assert compute_playlist_stats(sample_playlists())["total_songs"] == 4


def test_stats_hype_ratio_divides_by_all_songs():
    assert compute_playlist_stats(sample_playlists())["hype_ratio"] == pytest.approx(0.5)


def test_stats_avg_energy_uses_all_songs():
    # (9 + 8 + 2 + 5) / 4
    assert compute_playlist_stats(sample_playlists())["avg_energy"] == pytest.approx(6.0)


def test_stats_empty_playlists():
    stats = compute_playlist_stats({"Hype": [], "Chill": [], "Mixed": []})
    assert stats["total_songs"] == 0
    assert stats["hype_ratio"] == 0.0
    assert stats["avg_energy"] == 0.0


# classify_song / build_playlists


def mid_energy_pop_song(title):
    # pop is not the default favorite genre and energy 5 sits between the
    # default thresholds, so only a title keyword can make this song Chill.
    return {"title": title, "artist": "x", "genre": "pop", "energy": 5, "tags": []}


@pytest.mark.parametrize("title", ["sleep tight", "SLEEP Tight", "Deep Sleep", "LoFi Beats"])
def test_chill_keyword_match_is_case_insensitive(title):
    assert classify_song(mid_energy_pop_song(title), DEFAULT_PROFILE) == "Chill"


def test_title_without_chill_keyword_stays_mixed():
    assert classify_song(mid_energy_pop_song("Sunny Day"), DEFAULT_PROFILE) == "Mixed"


def test_build_playlists_preserves_title_capitalization():
    playlists = build_playlists([mid_energy_pop_song("Deep SLEEP Mix")], DEFAULT_PROFILE)
    assert [song["title"] for song in playlists["Chill"]] == ["Deep SLEEP Mix"]


# lucky_pick


def mood_playlists():
    return {
        "Hype": [make_song("Hype Song", "h")],
        "Chill": [make_song("Chill Song", "c")],
        "Mixed": [make_song("Mixed Song", "m")],
    }


@pytest.fixture
def candidates(monkeypatch):
    """Record the list lucky_pick chooses from, and pick its first item."""
    seen = []

    def fake_choice(songs):
        seen.extend(song["title"] for song in songs)
        return songs[0]

    monkeypatch.setattr(random, "choice", fake_choice)
    return seen


@pytest.mark.parametrize("mode", ["any", "hype", "chill"])
def test_lucky_pick_empty_playlists_returns_none(mode):
    assert lucky_pick({"Hype": [], "Chill": [], "Mixed": []}, mode=mode) is None


def test_lucky_pick_missing_playlists_returns_none():
    assert lucky_pick({}, mode="any") is None


def test_lucky_pick_hype_mode_uses_only_hype(candidates):
    lucky_pick(mood_playlists(), mode="hype")
    assert candidates == ["Hype Song"]


def test_lucky_pick_chill_mode_uses_only_chill(candidates):
    lucky_pick(mood_playlists(), mode="chill")
    assert candidates == ["Chill Song"]


def test_lucky_pick_any_mode_includes_mixed(candidates):
    lucky_pick(mood_playlists(), mode="any")
    assert sorted(candidates) == ["Chill Song", "Hype Song", "Mixed Song"]


def test_lucky_pick_any_mode_with_only_mixed_songs():
    playlists = {"Hype": [], "Chill": [], "Mixed": [make_song("Only Mixed", "m")]}
    assert lucky_pick(playlists, mode="any")["title"] == "Only Mixed"


def test_lucky_pick_hype_mode_ignores_other_playlists_when_empty():
    playlists = {"Hype": [], "Chill": [make_song("C", "c")], "Mixed": [make_song("M", "m")]}
    assert lucky_pick(playlists, mode="hype") is None


# merge_playlists


def test_merge_does_not_mutate_inputs():
    a = {"Hype": [make_song("A", "x")], "Chill": [make_song("B", "y")]}
    b = {"Hype": [make_song("C", "z")]}
    a_before = copy.deepcopy(a)
    b_before = copy.deepcopy(b)

    merged = merge_playlists(a, b)
    merged["Hype"].append(make_song("D", "w"))

    assert a == a_before
    assert b == b_before
    assert merged["Hype"] is not a["Hype"]
    assert merged["Chill"] is not a["Chill"]


def test_merge_combines_shared_keys_in_order():
    a = {"Hype": [make_song("A", "x")]}
    b = {"Hype": [make_song("B", "y")]}
    merged = merge_playlists(a, b)
    assert [song["title"] for song in merged["Hype"]] == ["A", "B"]


def test_merge_with_different_keys():
    a = {"Hype": [make_song("A", "x")]}
    b = {"Chill": [make_song("B", "y")]}
    merged = merge_playlists(a, b)
    assert list(merged) == ["Hype", "Chill"]
    assert [song["title"] for song in merged["Hype"]] == ["A"]
    assert [song["title"] for song in merged["Chill"]] == ["B"]


def test_merge_with_empty_second_map_copies_first():
    a = mood_playlists()
    merged = merge_playlists(a, {})
    assert merged == a
    assert all(merged[key] is not a[key] for key in a)
