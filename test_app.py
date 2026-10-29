import pytest
from streamlit.testing.v1 import AppTest


def sidebar_widget(widgets, label):
    return next(widget for widget in widgets if widget.label == label)


@pytest.fixture
def app():
    at = AppTest.from_file("app.py", default_timeout=30).run()
    assert not at.exception
    return at


def add_song(at, title, artist):
    sidebar_widget(at.sidebar.text_input, "Title").set_value(title)
    sidebar_widget(at.sidebar.text_input, "Artist").set_value(artist)
    sidebar_widget(at.sidebar.button, "Add to playlist").click().run()
    assert not at.exception


def sidebar_warnings(at):
    return [warning.value for warning in at.sidebar.warning]


def test_app_starts_with_default_songs(app):
    assert len(app.session_state.songs) == 22
    assert sidebar_warnings(app) == []


def test_new_song_is_added(app):
    add_song(app, "Brand New Song", "New Artist")
    assert len(app.session_state.songs) == 23
    assert sidebar_warnings(app) == []


def test_duplicate_of_default_song_is_rejected(app):
    add_song(app, " THUNDERSTRUCK ", "Ac/Dc ")
    assert len(app.session_state.songs) == 22
    assert any("already in the playlist" in text for text in sidebar_warnings(app))


def test_duplicate_of_added_song_is_rejected(app):
    add_song(app, "Brand New Song", "New Artist")
    add_song(app, "brand new song", "NEW ARTIST")
    assert len(app.session_state.songs) == 23
    assert any("already in the playlist" in text for text in sidebar_warnings(app))


@pytest.mark.parametrize(
    "title, artist",
    [
        ("   ", "Some Artist"),
        ("Some Title", "   "),
        ("", "Some Artist"),
        ("Some Title", ""),
        ("", ""),
    ],
)
def test_missing_or_blank_title_or_artist_is_rejected(app, title, artist):
    add_song(app, title, artist)
    assert len(app.session_state.songs) == 22
    assert any("title and an artist" in text for text in sidebar_warnings(app))
