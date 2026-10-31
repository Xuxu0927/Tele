"""Shared navigation rules for MkDocs builds and the desktop editor."""

import os
import posixpath
import re
import shutil
from pathlib import Path, PurePosixPath
from urllib.parse import urlsplit

import yaml
from mkdocs.structure.files import File, Files, InclusionLevel
from mkdocs.utils.meta import get_data
from mkdocs_awesome_nav.nav.config import ConfigModel
from mkdocs_awesome_nav.nav.context import MkdocsFilesContext
from mkdocs_awesome_nav.nav.directory import RootNavDirectory
from mkdocs_awesome_nav.nav.link import NavLink
from mkdocs_awesome_nav.nav.page import NavPage


NAV_FILENAME = '.nav.yml'


def read_rules(contents, path):
    try:
        settings = yaml.safe_load(contents) or {}
        ConfigModel.model_validate(settings)
    except (yaml.YAMLError, ValueError) as error:
        raise ValueError(f'导航配置有误：{path}\n{error}') from error
    return settings


def _local_reference(value):
    return (
        not urlsplit(value).scheme
        and not value.startswith(('/', '#', '../'))
        and not any(char in value for char in '*?[]{}!@')
    )


def prepare_nav_files(files, *, unflatten=False):
    """Discard obsolete local entries in memory, without changing saved rules."""
    existing = {file.src_uri for file in files if file.inclusion.is_included()}
    for file in files.documentation_pages(inclusion=InclusionLevel.is_in_nav):
        path = PurePosixPath(file.src_uri)
        existing.add(path.as_posix())
        existing.update(parent.as_posix() for parent in path.parents)

    def prune(entries, directory):
        result = []
        for entry in entries:
            if isinstance(entry, str):
                target = posixpath.normpath(posixpath.join(directory, urlsplit(entry).path))
                if not _local_reference(entry) or target in existing:
                    result.append(entry)
            elif 'glob' in entry:
                result.append({**entry, 'flatten_single_child_sections': False} if unflatten else entry)
            else:
                label, value = next(iter(entry.items()))
                if isinstance(value, list):
                    children = prune(value, directory)
                    if children:
                        result.append({label: children})
                else:
                    target = posixpath.normpath(posixpath.join(directory, urlsplit(value).path))
                    if not _local_reference(value) or target in existing:
                        result.append(entry)
        return result

    for file in files:
        if PurePosixPath(file.src_uri).name != NAV_FILENAME:
            continue
        settings = read_rules(file.content_string, file.src_uri)
        if 'nav' in settings:
            settings['nav'] = prune(settings['nav'], posixpath.dirname(file.src_uri))
        if unflatten:
            # The editor shows folders so a new sibling never changes its structure.
            settings['flatten_single_child_sections'] = False
        file.content_string = yaml.safe_dump(settings, allow_unicode=True, sort_keys=False)
    return files


class NavigationModel:
    def __init__(self, docs_dir):
        self.docs_dir = Path(docs_dir)
        self.meta_map = {}
        self.known_paths = set()
        self._settings = {}
        self._nodes = {}

    def get_merged_tree_data(self):
        if not self.docs_dir.is_dir():
            raise FileNotFoundError(f'找不到目录：{self.docs_dir}')
        self.meta_map.clear()
        self.known_paths.clear()
        self._settings.clear()
        self._nodes.clear()
        files = []
        for path in self.docs_dir.rglob('*'):
            relative = path.relative_to(self.docs_dir)
            if not path.is_file() or any(part.startswith('.') for part in relative.parts[:-1]):
                continue
            if path.name == NAV_FILENAME:
                settings = read_rules(path.read_text(encoding='utf-8-sig'), path)
                directory = relative.parent.as_posix()
                self._settings[directory] = settings
                self._collect_explicit_paths(settings.get('nav', []), directory)
            elif path.name.startswith('.'):
                continue
            files.append(File(relative.as_posix(), str(self.docs_dir), str(self.docs_dir), True))

        if '.' not in self._settings:
            self._settings['.'] = {'append_unmatched': True}
            virtual = File(NAV_FILENAME, str(self.docs_dir), str(self.docs_dir), True)
            virtual.content_string = yaml.safe_dump(self._settings['.'])
            files.append(virtual)
        collection = prepare_nav_files(Files(files), unflatten=True)
        context = MkdocsFilesContext(collection, NAV_FILENAME)
        resolved = RootNavDirectory(context.root).resolve(context)
        return self._convert_nodes(resolved.children, '.')

    def _collect_explicit_paths(self, entries, directory):
        for entry in entries:
            if isinstance(entry, str):
                value = entry
            elif 'glob' in entry:
                continue
            else:
                value = next(iter(entry.values()))
                if isinstance(value, list):
                    self._collect_explicit_paths(value, directory)
                    continue
            if _local_reference(value):
                self.known_paths.add(posixpath.normpath(posixpath.join(directory, value)))

    def _convert_nodes(self, items, directory, parent_id='root'):
        result = []
        for index, item in enumerate(items):
            if isinstance(item, NavPage):
                path = item.page.path.as_posix()
                markdown, meta = get_data(item.page.file.content_string)
                heading = re.search(r'^#\s+(.+?)\s*#*\s*$', markdown, re.MULTILINE)
                name = item.title or meta.get('title') or (heading.group(1) if heading else Path(path).stem)
                node = self._node(path, str(name), 'file', path)
            elif isinstance(item, NavLink):
                node = self._node(f'link:{parent_id}:{index}', item.title, 'link', item.url)
            else:
                path = item.path.as_posix()
                virtual = path == directory
                item_id = f'group:{parent_id}:{index}' if virtual else path
                node = self._node(item_id, item.title, 'group' if virtual else 'dir', path)
                node['children'] = self._convert_nodes(item.children, path, item_id)
            result.append(node)
        return result

    def _node(self, item_id, name, kind, path):
        if item_id in self.meta_map:
            raise ValueError(f'导航重复引用了 {path}，请先在 .nav.yml 中调整重复项。')
        meta = {'name': name, 'type': kind, 'path': path}
        self.meta_map[item_id] = meta
        node = {'id': item_id, **meta, 'is_new': kind in ('file', 'dir') and path not in self.known_paths, 'children': []}
        self._nodes[item_id] = node
        return node

    def _flatten_enabled(self, directory):
        path = PurePosixPath(directory)
        for candidate in (path, *path.parents):
            value = self._settings.get(candidate.as_posix(), {}).get('flatten_single_child_sections')
            if value is not None:
                return value
        return False

    def rename_item(self, item_id, name):
        name = name.strip()
        if not name:
            raise ValueError('显示名称不能为空。')
        changed = []
        while True:
            self.meta_map[item_id]['name'] = name
            self._nodes[item_id]['name'] = name
            changed.append(item_id)
            node = self._nodes[item_id]
            if node['type'] != 'dir' or len(node['children']) != 1 or not self._flatten_enabled(node['path']):
                return changed
            item_id = node['children'][0]['id']

    def save_to_yaml(self, tree):
        pending = []

        def check_editable(entries, directory, *, nested=False):
            for entry in entries:
                if isinstance(entry, str):
                    pattern = any(char in entry for char in '*?[]{}!@')
                    supported = entry == '*' and not nested
                    literal = (self.docs_dir / directory / entry).exists()
                    unsupported = pattern and not supported and not literal
                elif 'glob' in entry:
                    unsupported = (nested or entry['glob'] != '*'
                                   or bool(set(entry) - {'glob', 'ignore_no_matches'}))
                else:
                    value = next(iter(entry.values()))
                    if isinstance(value, list):
                        check_editable(value, directory, nested=True)
                    unsupported = False
                if unsupported:
                    raise ValueError(
                        f'{directory}/{NAV_FILENAME} 使用了自定义通配规则。'
                        '请直接编辑该配置文件；原配置未更改。'
                    )

        def entries(ids, directory):
            result = []
            for item_id in ids:
                meta = self.meta_map[item_id]
                if meta['type'] == 'group':
                    value = entries(tree.get_children(item_id), directory)
                elif meta['type'] == 'link':
                    value = meta['path']
                else:
                    value = posixpath.relpath(meta['path'], directory)
                    if meta['type'] == 'dir':
                        save_directory(meta['path'], tree.get_children(item_id))
                result.append({meta['name']: value})
            return result

        def save_directory(directory, ids):
            settings = dict(self._settings.get(directory, {}))
            original_entries = settings.get('nav', [])
            check_editable(original_entries, directory)
            settings['nav'] = entries(ids, directory)
            # Keep simple catch-all patterns and inherited append settings intact.
            settings['nav'].extend(entry for entry in original_entries
                                   if entry == '*' or isinstance(entry, dict) and 'glob' in entry)
            if 'nav' not in self._settings.get(directory, {}):
                settings['nav'].append({'glob': '*', 'ignore_no_matches': True})
            pending.append((self.docs_dir / directory / NAV_FILENAME, settings))

        save_directory('.', tree.get_roots())
        # Validate and serialize everything before changing any configuration file.
        outputs = [(path, yaml.safe_dump(settings, allow_unicode=True, sort_keys=False)) for path, settings in pending]
        for path, contents in outputs:
            read_rules(contents, path)
        for path, contents in outputs:
            temporary = path.with_name(path.name + '.tmp')
            try:
                temporary.write_text(contents, encoding='utf-8')
                if path.exists():
                    shutil.copy2(path, str(path) + '.bak')
                os.replace(temporary, path)
            finally:
                temporary.unlink(missing_ok=True)
        return True
