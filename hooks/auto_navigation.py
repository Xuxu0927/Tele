"""Keep removed or moved articles out of generated navigation."""

from navigation import prepare_nav_files


def on_files(files, *, config):
    return prepare_nav_files(files)
