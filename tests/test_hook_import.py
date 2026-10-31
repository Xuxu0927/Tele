import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml


class HookImportTests(unittest.TestCase):
    def test_console_build_loads_project_hook_without_project_on_python_path(self):
        source = Path(__file__).resolve().parents[1]
        console = shutil.which('mkdocs', path=str(Path(sys.executable).parent))
        self.assertIsNotNone(console, 'The environment must provide the mkdocs command')
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            project = root / 'project'
            docs = project / 'docs'
            docs.mkdir(parents=True)
            (project / 'hooks').mkdir()
            shutil.copy2(source / 'navigation.py', project / 'navigation.py')
            shutil.copy2(source / 'hooks/auto_navigation.py', project / 'hooks/auto_navigation.py')
            (docs / 'index.md').write_text('# Home\n', encoding='utf-8')
            (docs / '.nav.yml').write_text(yaml.safe_dump({
                'nav': [{'Removed': 'removed.md'}, {'Home': 'index.md'}],
                'append_unmatched': True,
            }), encoding='utf-8')
            configuration = project / 'mkdocs.yml'
            configuration.write_text(yaml.safe_dump({
                'site_name': 'Hook import regression',
                'plugins': ['awesome-nav'],
                'hooks': ['hooks/auto_navigation.py'],
            }), encoding='utf-8')
            outside = root / 'outside'
            outside.mkdir()
            environment = os.environ.copy()
            environment.pop('PYTHONPATH', None)
            environment['PYTHONSAFEPATH'] = '1'
            result = subprocess.run(
                [console, 'build', '--config-file', str(configuration)],
                cwd=outside, env=environment, capture_output=True,
                text=True, encoding='utf-8', timeout=60,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            html = (project / 'site/index.html').read_text(encoding='utf-8')
            self.assertNotIn('removed.md', html)


if __name__ == '__main__':
    unittest.main()
