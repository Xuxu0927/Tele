import unittest
from pathlib import Path

from jinja2 import Environment, FileSystemLoader


class CommentTemplateTests(unittest.TestCase):
    def setUp(self):
        overrides = Path(__file__).resolve().parents[1] / 'docs/mkdocs/overrides'
        self.template = Environment(loader=FileSystemLoader(overrides)).get_template(
            'partials/comments.html'
        )

    def test_comments_true_loads_giscus(self):
        html = self.template.render(page={'meta': {'comments': True}})
        self.assertTrue('https://giscus.app/client.js' in html)

    def test_comments_false_does_not_load_giscus(self):
        html = self.template.render(page={'meta': {'comments': False}})
        self.assertFalse('https://giscus.app/client.js' in html)

    def test_page_without_comment_setting_does_not_load_giscus(self):
        html = self.template.render(page={'meta': {}})
        self.assertFalse('https://giscus.app/client.js' in html)


if __name__ == '__main__':
    unittest.main()
