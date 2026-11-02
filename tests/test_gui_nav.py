import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml

from gui_nav import Config, MkDocsCore


class TreeDataAdapter:
    """Exercise navigation saving without opening a desktop window."""

    def __init__(self, roots):
        self.roots = [node['id'] for node in roots]
        self.nodes = {}

        def collect(nodes):
            for node in nodes:
                self.nodes[node['id']] = node
                collect(node['children'])

        collect(roots)

    def get_roots(self):
        return self.roots

    def get_children(self, item_id):
        return [node['id'] for node in self.nodes[item_id]['children']]


class ManualNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / 'docs'
        self.docs.mkdir()
        self.config = self.root / 'mkdocs.yml'
        self.config.write_text('site_name: Test\nnav:\n- 课程: course/lesson.md\n', encoding='utf-8')
        paths = patch.multiple(Config, DOCS_DIR=str(self.docs), CONFIG_FILE=str(self.config))
        paths.start()
        self.addCleanup(paths.stop)
        self.article('course/lesson.md')

    def article(self, path):
        target = self.docs / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('# Test\n', encoding='utf-8')

    def load(self):
        core = MkDocsCore()
        return core, TreeDataAdapter(core.get_merged_tree_data())

    def test_flattened_alias_is_recognized_as_existing_after_reload(self):
        core, tree = self.load()
        self.assertEqual(tree.nodes['course']['name'], '课程')
        self.assertFalse(tree.nodes['course/lesson.md']['is_new'])
        core.save_to_yaml(tree)
        _, reloaded = self.load()
        self.assertFalse(reloaded.nodes['course/lesson.md']['is_new'])
        self.assertEqual(yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav'],
                         [{'课程': 'course/lesson.md'}])

    def test_new_pages_are_only_added_when_editor_saves(self):
        self.article('course/new2.md')
        self.article('course/new10.md')
        core, tree = self.load()
        self.assertEqual(tree.get_children('course'), ['course/lesson.md', 'course/new2.md', 'course/new10.md'])
        self.assertTrue(tree.nodes['course/new2.md']['is_new'])
        self.assertEqual(yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav'],
                         [{'课程': 'course/lesson.md'}])
        core.save_to_yaml(tree)
        saved = yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav']
        self.assertEqual(saved, [{'课程': [{'课程': 'course/lesson.md'},
                                          {'new2': 'course/new2.md'}, {'new10': 'course/new10.md'}]}])
        self.assertEqual(list(self.docs.rglob('.nav.yml')), [])

    def test_saved_names_and_order_survive_when_folder_label_differs(self):
        self.article('course/second.md')
        self.config.write_text('site_name: Test\nnav:\n- 自定义分组:\n  - 第二篇: course/second.md\n  - 第一篇: course/lesson.md\n', encoding='utf-8')
        core, tree = self.load()
        self.assertEqual(tree.nodes['course']['name'], '自定义分组')
        self.assertEqual(tree.get_children('course'), ['course/second.md', 'course/lesson.md'])
        self.assertTrue(all(not node['is_new'] for node in tree.nodes.values()))
        core.rename_item('course/second.md', '名称: [示例]')
        tree.nodes['course']['children'].reverse()
        core.save_to_yaml(tree)
        saved = yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav']
        self.assertEqual(saved, [{'自定义分组': [{'第一篇': 'course/lesson.md'},
                                                {'名称: [示例]': 'course/second.md'}]}])

    def test_save_preserves_other_settings_comments_and_backup(self):
        original = '# 保留注释\nsite_name: Test\nnav: [{课程: course/lesson.md}]\nextra:\n  nav: nested value\n  footer: keep\n'
        self.config.write_text(original, encoding='utf-8')
        core, tree = self.load()
        core.save_to_yaml(tree)
        saved = self.config.read_text(encoding='utf-8')
        self.assertIn('# 保留注释', saved)
        self.assertEqual(yaml.safe_load(saved)['extra'], {'nav': 'nested value', 'footer': 'keep'})
        self.assertEqual(Path(str(self.config) + '.bak').read_text(encoding='utf-8'), original)

    def test_deleted_pages_are_removed_and_assets_are_ignored(self):
        (self.docs / 'course/lesson.md').unlink()
        self.article('keep.md')
        self.article('assets/hidden.md')
        self.article('note.assets/hidden.md')
        core, tree = self.load()
        self.assertEqual(tree.get_roots(), ['keep.md'])
        core.save_to_yaml(tree)
        self.assertEqual(yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav'], [{'keep': 'keep.md'}])

    def test_invalid_config_is_not_overwritten(self):
        original = 'site_name: Test\nnav: [invalid\n'
        self.config.write_text(original, encoding='utf-8')
        with self.assertRaises(ValueError):
            self.load()
        self.assertEqual(self.config.read_text(encoding='utf-8'), original)

    def test_renaming_only_article_updates_flattened_navigation_label(self):
        core, tree = self.load()
        core.rename_item('course/lesson.md', '新名称')
        core.save_to_yaml(tree)
        self.assertEqual(yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav'],
                         [{'新名称': 'course/lesson.md'}])

    def test_failed_rescan_keeps_loaded_tree_metadata(self):
        core, tree = self.load()
        original = dict(core.meta_map)
        with patch.object(core, '_scan', side_effect=PermissionError('cannot read folder')):
            with self.assertRaises(PermissionError):
                core.get_merged_tree_data()
        self.assertEqual(core.meta_map, original)
        core.save_to_yaml(tree)
        self.assertEqual(yaml.safe_load(self.config.read_text(encoding='utf-8'))['nav'],
                         [{'课程': 'course/lesson.md'}])

    def test_cannot_save_before_a_successful_load(self):
        core = MkDocsCore()
        original = self.config.read_bytes()
        with self.assertRaises(ValueError):
            core.save_to_yaml(TreeDataAdapter([]))
        self.assertEqual(self.config.read_bytes(), original)


if __name__ == '__main__':
    unittest.main()


