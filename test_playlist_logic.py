import pytest

from playlist_logic import compute_playlist_stats, search_songs


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
