import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import yaml
from mkdocs.config import load_config
from mkdocs.structure.files import get_files
from mkdocs.structure.nav import get_navigation

from gui_nav import Config, MkDocsCore
from test_gui_nav import TreeDataAdapter


class AutoNavigationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.docs = self.root / 'docs'
        self.docs.mkdir()
        self.config = self.root / 'mkdocs.yml'
        self.config.write_text('site_name: Test\n', encoding='utf-8')
        paths = patch.multiple(Config, DOCS_DIR=str(self.docs), CONFIG_FILE=str(self.config))
        paths.start()
        self.addCleanup(paths.stop)

    def article(self, path):
        target = self.docs / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text('# Test\n', encoding='utf-8')
        return target

    def rules(self, directory='.', **settings):
        path = self.docs / directory / '.nav.yml'
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(yaml.safe_dump(settings, allow_unicode=True, sort_keys=False), encoding='utf-8')
        return path

    def load_tree(self):
        core = MkDocsCore()
        return core, TreeDataAdapter(core.get_merged_tree_data())

    def site_nav(self):
        from hooks.auto_navigation import on_files
        config = load_config(config_file=str(self.config), plugins=['awesome-nav'], docs_dir=str(self.docs), site_dir=str(self.root / 'site'))
        files = on_files(get_files(config), config=config)
        nav = config.plugins['awesome-nav'].on_nav(get_navigation(files, config), config, files)
        for page in nav.pages:
            page.read_source(config)
        return nav

    def test_editor_reads_directory_rules_and_aliases(self):
        self.article('course/notes.md')
        self.rules(nav=[{'自定义课程': 'course'}], append_unmatched=True)
        self.rules('course', nav=[{'课程笔记': 'notes.md'}])
        _, tree = self.load_tree()
        self.assertEqual(tree.nodes['course']['name'], '自定义课程')
        self.assertEqual(tree.nodes['course/notes.md']['name'], '课程笔记')
        self.assertFalse(tree.nodes['course/notes.md']['is_new'])

    def test_save_writes_directory_rules_without_modifying_mkdocs(self):
        self.article('course/notes.md')
        self.rules(append_unmatched=True)
        original = self.config.read_bytes()
        core, tree = self.load_tree()
        self.assertTrue(core.save_to_yaml(tree))
        self.assertEqual(self.config.read_bytes(), original)
        self.assertTrue((self.docs / 'course/.nav.yml').is_file())

    def test_new_articles_and_folders_are_found_without_editor(self):
        self.article('old.md')
        self.rules(nav=[{'原文章': 'old.md'}], append_unmatched=True)
        self.article('new.md')
        self.article('new-course/lesson.md')
        self.assertEqual({p.file.src_uri for p in self.site_nav().pages}, {'old.md', 'new.md', 'new-course/lesson.md'})

    def test_deleted_articles_and_empty_folders_leave_no_stale_links(self):
        self.article('keep.md')
        self.rules(nav=[{'已删除': 'gone.md'}, {'空目录': 'gone-course'}, {'保留': 'keep.md'}], append_unmatched=True)
        self.assertEqual([i.title for i in self.site_nav().items], ['保留'])

    def test_deleted_folder_with_dotted_name_is_not_kept_as_link(self):
        self.article('keep.md')
        self.rules(nav=[{'旧课程': 'course.v1'}], append_unmatched=True)
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['keep.md'])
        self.assertEqual(len(self.site_nav().items), 1)

    def test_local_pdf_link_survives_editor_save(self):
        self.article('notes.md')
        (self.docs / 'reference.pdf').write_bytes(b'%PDF-test')
        self.rules(nav=[{'资料': 'reference.pdf'}], append_unmatched=True)
        core, tree = self.load_tree()
        core.save_to_yaml(tree)
        self.assertEqual(self.site_nav().items[0].url, 'reference.pdf')

    def test_nested_virtual_sections_survive_editor_save(self):
        self.article('notes.md')
        self.rules(nav=[{'外层': [{'内层': [{'笔记': 'notes.md'}]}]}], append_unmatched=True)
        core, tree = self.load_tree()
        core.save_to_yaml(tree)
        item = self.site_nav().items[0]
        self.assertEqual((item.title, item.children[0].title, item.children[0].children[0].title), ('外层', '内层', '笔记'))

    def test_pattern_flatten_option_does_not_pin_article_outside_its_folder(self):
        self.article('course/old.md')
        self.rules(nav=[{'glob': '*', 'flatten_single_child_sections': True}], append_unmatched=True)
        core, tree = self.load_tree()
        self.assertIn('course', tree.nodes)
        original = (self.docs / '.nav.yml').read_bytes()
        with self.assertRaisesRegex(ValueError, '通配规则'):
            core.save_to_yaml(tree)
        self.assertEqual((self.docs / '.nav.yml').read_bytes(), original)

    def test_pattern_exclusion_is_rejected_before_any_rules_are_overwritten(self):
        self.article('public.md')
        self.article('private.md')
        path = self.rules(nav=[{'glob': '*', 'ignore': ['private.md']}])
        original = path.read_bytes()
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['public.md'])
        core, tree = self.load_tree()
        with self.assertRaisesRegex(ValueError, '通配规则'):
            core.save_to_yaml(tree)
        self.assertEqual(path.read_bytes(), original)
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['public.md'])

    def test_custom_filename_pattern_is_not_replaced_with_include_everything(self):
        self.article('public.md')
        self.article('private.md')
        path = self.rules(nav=['public*.md'])
        original = path.read_bytes()
        core, tree = self.load_tree()
        with self.assertRaisesRegex(ValueError, '通配规则'):
            core.save_to_yaml(tree)
        self.assertEqual(path.read_bytes(), original)

    def test_local_fragment_links_keep_their_full_url(self):
        self.article('notes.md')
        (self.docs / 'reference.pdf').write_bytes(b'%PDF-test')
        path = self.rules(nav=[{'小节': 'notes.md#part'}, {'PDF页码': 'reference.pdf#page=2'}], append_unmatched=True)
        original = path.read_bytes()
        nav = self.site_nav()
        self.assertEqual(nav.items[0].url, 'notes.md#part')
        self.assertEqual(nav.items[1].url, 'reference.pdf#page=2')
        self.assertEqual(path.read_bytes(), original)

    def test_explicit_append_unmatched_false_survives_save(self):
        self.article('public.md')
        self.article('private.md')
        self.rules(nav=[{'公开': 'public.md'}], append_unmatched=False)
        core, tree = self.load_tree()
        core.save_to_yaml(tree)
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['public.md'])

    def test_rules_without_nav_keep_the_default_automatic_discovery(self):
        self.article('first.md')
        self.rules(sort={'type': 'natural'})
        core, tree = self.load_tree()
        core.save_to_yaml(tree)
        with self.assertNoLogs('mkdocs.plugins.awesome-nav', level='WARNING'):
            self.site_nav()
        self.article('later.md')
        self.assertEqual({p.file.src_uri for p in self.site_nav().pages}, {'first.md', 'later.md'})
        _, reloaded = self.load_tree()
        self.assertIn('later.md', reloaded.nodes)

    def test_moved_article_is_rediscovered(self):
        self.article('new-place/article.md')
        self.rules(nav=[{'旧位置': 'old-place/article.md'}], append_unmatched=True)
        nav = self.site_nav()
        self.assertEqual([p.file.src_uri for p in nav.pages], ['new-place/article.md'])
        self.assertEqual(len(nav.items), 1)

    def test_single_article_flattens_and_new_sibling_expands_section(self):
        self.article('course/old.md')
        self.rules(nav=[{'自定义课程': 'course'}], append_unmatched=True, flatten_single_child_sections=True)
        self.rules('course', nav=[{'课程名称': 'old.md'}])
        self.assertEqual(self.site_nav().items[0].title, '课程名称')
        self.article('course/new.md')
        nav = self.site_nav()
        self.assertEqual(nav.items[0].title, '自定义课程')
        self.assertEqual([c.title for c in nav.items[0].children], ['课程名称', 'Test'])

    def test_drag_order_is_used_by_plugin(self):
        self.article('first.md')
        self.article('second.md')
        self.rules(nav=[{'第一': 'first.md'}, {'第二': 'second.md'}], append_unmatched=True)
        core, tree = self.load_tree()
        tree.roots.reverse()
        core.save_to_yaml(tree)
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['second.md', 'first.md'])

    def test_rename_changes_navigation_without_renaming_article(self):
        path = self.article('course/notes.md')
        self.rules(nav=[{'课程': 'course'}], append_unmatched=True, flatten_single_child_sections=True)
        self.rules('course', nav=[{'旧名称': 'notes.md'}])
        original = path.read_bytes()
        core, tree = self.load_tree()
        core.rename_item('course', '新名称')
        core.save_to_yaml(tree)
        self.assertEqual(self.site_nav().items[0].title, '新名称')
        self.assertEqual(path.read_bytes(), original)

    def test_settings_and_backup_survive_save(self):
        self.article('notes.md')
        path = self.rules(nav=[{'笔记': 'notes.md'}], append_unmatched=True, ignore=['assets/'], sort={'type': 'natural'}, flatten_single_child_sections=True)
        original = path.read_bytes()
        core, tree = self.load_tree()
        core.save_to_yaml(tree)
        settings = yaml.safe_load(path.read_text(encoding='utf-8'))
        self.assertEqual(settings['ignore'], ['assets/'])
        self.assertEqual(settings['sort'], {'type': 'natural'})
        self.assertTrue(settings['flatten_single_child_sections'])
        self.assertEqual(Path(str(path) + '.bak').read_bytes(), original)

    def test_new_sibling_stays_automatic_after_saving_order(self):
        self.article('course/old.md')
        self.rules(nav=[{'别名': 'course'}], append_unmatched=True)
        self.rules('course', nav=[{'原笔记': 'old.md'}])
        self.article('course/new.md')
        core, tree = self.load_tree()
        self.assertFalse(tree.nodes['course/old.md']['is_new'])
        self.assertTrue(tree.nodes['course/new.md']['is_new'])
        core.save_to_yaml(tree)
        _, reloaded = self.load_tree()
        self.assertTrue(all(not n['is_new'] for n in reloaded.nodes.values()))
        self.article('course/later.md')
        self.assertIn('course/later.md', [p.file.src_uri for p in self.site_nav().pages])

    def test_ignore_rules_are_respected_by_editor_and_build(self):
        self.article('public.md')
        self.article('hidden/private.md')
        self.rules(append_unmatched=True, ignore=['hidden/'])
        core, tree = self.load_tree()
        self.assertNotIn('hidden/private.md', tree.nodes)
        core.save_to_yaml(tree)
        self.assertEqual([p.file.src_uri for p in self.site_nav().pages], ['public.md'])

    def test_malformed_rules_are_not_overwritten(self):
        self.article('notes.md')
        path = self.docs / '.nav.yml'
        path.write_text('nav: [\n', encoding='utf-8')
        original = path.read_bytes()
        with self.assertRaises(ValueError):
            self.load_tree()
        self.assertEqual(path.read_bytes(), original)

    def test_external_links_survive_build(self):
        self.article('notes.md')
        self.rules(nav=[{'官网': 'https://example.com'}, {'站外页面': '../other/'}], append_unmatched=True)
        nav = self.site_nav()
        self.assertEqual(nav.items[0].url, 'https://example.com')
        self.assertEqual(nav.items[1].url, '../other/')
