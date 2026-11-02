"""Manual Markdown navigation saved to the project's mkdocs.yml."""

import os
import re
import shutil
from pathlib import Path
from urllib.parse import urlsplit

import yaml


class NavigationModel:
    IGNORE_NAMES = {
        'assets', 'img', 'images', 'media', 'static', '.git', '.github',
        'site', 'env', 'venv', '__pycache__', 'node_modules', 'mkdocs', 'dist', 'build',
    }
    IGNORE_SUFFIXES = ('.assets', '.images', '_files')

    def __init__(self, docs_dir, config_file):
        self.docs_dir = Path(docs_dir)
        self.config_file = Path(config_file)
        self.meta_map = {}
        self.known_paths = set()
        self._loaded = False

    @staticmethod
    def _natural_sort(value):
        return [int(part) if part.isdigit() else part.casefold() for part in re.split(r'(\d+)', value)]

    def _read_config(self):
        text = self.config_file.read_text(encoding='utf-8-sig')
        try:
            config = yaml.safe_load(text) or {}
        except yaml.YAMLError as error:
            raise ValueError(f'mkdocs.yml 配置有误：{error}') from error
        if not isinstance(config, dict):
            raise ValueError('mkdocs.yml 必须是配置映射。')
        return text, config

    def _history(self, entries):
        if not isinstance(entries, list):
            raise ValueError('mkdocs.yml 的 nav 必须是列表。')
        result = []
        for entry in entries:
            if isinstance(entry, str):
                name, value = Path(urlsplit(entry).path).stem, entry
            elif isinstance(entry, dict) and len(entry) == 1:
                name, value = next(iter(entry.items()))
            else:
                raise ValueError(f'无法识别导航项目：{entry}')
            if isinstance(value, list):
                result.append({'name': str(name), 'children': self._history(value)})
            elif isinstance(value, str):
                result.append({'name': str(name), 'path': value.replace(chr(92), '/'), 'children': []})
            else:
                raise ValueError(f'无法识别导航目标：{value}')
        return result

    def _references(self, item):
        if 'path' in item:
            value = item['path']
            if not urlsplit(value).scheme and not value.startswith(('/', '#')):
                yield urlsplit(value).path
        for child in item['children']:
            yield from self._references(child)

    def _scan(self, directory):
        result = {}
        for path in sorted(directory.iterdir(), key=lambda p: self._natural_sort(p.name)):
            if path.name.startswith('.') or path.is_symlink():
                continue
            relative = path.relative_to(self.docs_dir).as_posix()
            if path.is_dir():
                if path.name.casefold() in self.IGNORE_NAMES or path.name.endswith(self.IGNORE_SUFFIXES):
                    continue
                children = self._scan(path)
                if children:
                    result[relative] = {'type': 'dir', 'name': path.name, 'children': children}
            elif path.suffix.lower() == '.md':
                result[relative] = {'type': 'file', 'name': path.stem, 'children': {}}
        return result

    def _node(self, item_id, name, kind, *, path=None, children=None):
        node = {'id': item_id, 'name': name, 'type': kind, 'path': path or item_id,
                'is_new': kind in ('file', 'dir') and not any(
                    known == item_id or known.startswith(item_id + '/') for known in self.known_paths),
                'children': children or []}
        self.meta_map[item_id] = node
        return node

    def _merge(self, history, disk, *, add_new=True):
        result = []
        for saved in history:
            references = list(self._references(saved))
            match = next((key for key in disk if references and all(
                ref == key or ref.startswith(key + '/') for ref in references)), None)
            if match is not None:
                data = disk.pop(match)
                node = self._node(match, saved['name'], data['type'], path=saved.get('path') if data['type'] == 'file' else None)
                if data['type'] == 'dir':
                    children = [saved] if 'path' in saved else saved['children']
                    node['children'] = self._merge(children, data['children'])
                result.append(node)
            elif saved['children']:
                children = self._merge(saved['children'], disk, add_new=False)
                if children:
                    result.append(self._node(f'group:{len(self.meta_map)}', saved['name'], 'group', children=children))
            elif 'path' in saved:
                target = saved['path']
                if urlsplit(target).scheme or target.startswith(('/', '#')) or (
                    Path(urlsplit(target).path).suffix.lower() != '.md' and (self.docs_dir / urlsplit(target).path).is_file()
                ):
                    result.append(self._node(f'link:{len(self.meta_map)}', saved['name'], 'link', path=target))
        if add_new:
            for item_id, data in list(disk.items()):
                node = self._node(item_id, '首页' if Path(item_id).name == 'index.md' else data['name'], data['type'])
                if data['type'] == 'dir':
                    node['children'] = self._merge([], data['children'])
                result.append(node)
            disk.clear()
        return result

    def get_merged_tree_data(self):
        if not self.docs_dir.is_dir():
            raise FileNotFoundError(f'找不到目录：{self.docs_dir}')
        _, config = self._read_config()
        history = self._history(config.get('nav') or [])
        disk = self._scan(self.docs_dir)
        known_paths = {path for item in history for path in self._references(item)}
        self.meta_map.clear()
        self.known_paths = known_paths
        result = self._merge(history, disk)
        self._loaded = True
        return result

    def rename_item(self, item_id, name):
        name = name.strip()
        if not name:
            raise ValueError('显示名称不能为空。')
        node = self.meta_map[item_id]
        changed = [item_id]
        # A folder containing one page is displayed as that page on the site.
        if node['type'] == 'dir' and len(node['children']) == 1 and node['children'][0]['type'] == 'file':
            changed.append(node['children'][0]['id'])
        elif node['type'] == 'file':
            for parent in self.meta_map.values():
                if parent['type'] == 'dir' and len(parent['children']) == 1 and parent['children'][0]['id'] == item_id:
                    changed.append(parent['id'])
                    break
        for changed_id in changed:
            self.meta_map[changed_id]['name'] = name
        return changed

    def save_to_yaml(self, tree):
        if not self._loaded:
            raise ValueError('请先成功读取目录，再保存导航。')

        def entries(ids):
            result = []
            for item_id in ids:
                meta = self.meta_map[item_id]
                if meta['type'] in ('file', 'link'):
                    value = meta['path']
                else:
                    children = tree.get_children(item_id)
                    if meta['type'] == 'dir' and len(children) == 1 and self.meta_map[children[0]]['type'] == 'file':
                        value = self.meta_map[children[0]]['path']
                    else:
                        value = entries(children)
                result.append({meta['name']: value})
            return result

        nav = entries(tree.get_roots())
        original, config = self._read_config()
        document = yaml.compose(original)
        nav_yaml = yaml.safe_dump({'nav': nav}, allow_unicode=True, sort_keys=False)
        lines = original.splitlines(keepends=True)
        nav_key = None
        next_key = len(lines)
        if isinstance(document, yaml.MappingNode):
            for index, (key, _) in enumerate(document.value):
                if key.value == 'nav':
                    nav_key = key.start_mark.line
                    if index + 1 < len(document.value):
                        next_key = document.value[index + 1][0].start_mark.line
                    break
        if nav_key is None:
            contents = original.rstrip() + '\n\n' + nav_yaml
        else:
            contents = ''.join(lines[:nav_key]) + nav_yaml + ''.join(lines[next_key:])
        expected = {**config, 'nav': nav}
        if yaml.safe_load(contents) != expected:
            raise ValueError('保存验证失败，原配置未更改。')
        temporary = self.config_file.with_name(self.config_file.name + '.tmp')
        try:
            temporary.write_text(contents, encoding='utf-8')
            shutil.copy2(self.config_file, str(self.config_file) + '.bak')
            os.replace(temporary, self.config_file)
        finally:
            temporary.unlink(missing_ok=True)
        return True
