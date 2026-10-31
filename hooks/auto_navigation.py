"""Keep removed or moved articles out of generated navigation."""

from importlib import util
from pathlib import Path


# MkDocs exposes the hooks directory on sys.path, but not the project root.
# Resolve our shared module by filename so console commands and -m both work.
_navigation_path = Path(__file__).resolve().parents[1] / 'navigation.py'
_navigation_spec = util.spec_from_file_location('_tele_site_navigation', _navigation_path)
if _navigation_spec is None or _navigation_spec.loader is None:
    raise ImportError(f'Cannot load navigation module: {_navigation_path}')
_navigation = util.module_from_spec(_navigation_spec)
_navigation_spec.loader.exec_module(_navigation)


def on_files(files, *, config):
    return _navigation.prepare_nav_files(files)
