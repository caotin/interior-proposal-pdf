import re
from pathlib import Path
import unittest
import yaml

ROOT = Path(__file__).resolve().parents[1]


class PackageTests(unittest.TestCase):
    def test_skill_metadata_and_layout(self):
        text = (ROOT / 'SKILL.md').read_text(encoding='utf-8')
        match = re.match(r'^---\n(.*?)\n---\n', text, re.S)
        self.assertIsNotNone(match)
        data = yaml.safe_load(match.group(1))
        self.assertEqual(data['name'], ROOT.name)
        self.assertRegex(data['name'], r'^[a-z0-9]+(?:-[a-z0-9]+)*$')
        self.assertLessEqual(len(data['name']), 64)
        self.assertTrue(0 < len(data['description']) <= 1024)
        self.assertEqual(data['license'], 'MIT')
        self.assertLess(len(text.splitlines()), 500)
        self.assertTrue(all(isinstance(v, str) for v in data['metadata'].values()))
        for item in ('LICENSE', 'agents/openai.yaml', 'scripts/check_quote.py',
                     'scripts/render_pdf.mjs', 'assets/print.css', 'assets/starter.html'):
            self.assertTrue((ROOT / item).is_file(), item)

    def test_ui_metadata_matches_the_skill(self):
        data = yaml.safe_load((ROOT / 'agents/openai.yaml').read_text())
        ui = data['interface']
        self.assertIn('$interior-proposal-pdf', ui['default_prompt'])
        self.assertTrue(25 <= len(ui['short_description']) <= 64)

    def test_local_markdown_links_exist(self):
        paths = [ROOT / 'README.md', ROOT / 'SKILL.md', ROOT / 'THIRD_PARTY_NOTICES.md']
        paths += list((ROOT / 'references').glob('*.md'))
        for p in paths:
            for target in re.findall(r'\]\(([^)]+)\)', p.read_text()):
                if target.startswith(('https://', 'http://', '#')):
                    continue
                self.assertTrue((p.parent / target.split('#')[0]).exists(), f'{p.name}: {target}')

    def test_public_skill_has_no_private_reference_document(self):
        self.assertFalse((ROOT / 'assets/reference.pdf').exists())
        for p in (ROOT / 'references').glob('*'):
            self.assertNotIn('reference-contact-', p.name)


if __name__ == '__main__':
    unittest.main()
