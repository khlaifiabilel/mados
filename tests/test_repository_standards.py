# -*- coding: utf-8 -*-
"""Repository-level compliance checks enforced by CI.

Kept deliberately dependency-free (stdlib + Numpy) so it runs on a stock
runner without the torch / mmcv / mmseg training stack.
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

WORKFLOW_PATH = REPO_ROOT / '.github' / 'workflows' / 'ci.yml'

REQUIRED_FILES = [
    'README.md',
    'SECURITY.md',
    'CONTRIBUTING.md',
    'LICENSE',
    'requirements.txt',
    'environment.yml',
    '.github/workflows/ci.yml',
]

# Sections mandated by the handbook "README Standards".
REQUIRED_README_SECTIONS = [
    'Quick Start',
    'Prerequisites',
    'Installation',
    'Usage',
    'Configuration',
    'Testing',
    'Deployment',
    'Contributing',
    'Contact',
]

SCANNED_SUFFIXES = {
    '.py', '.yml', '.yaml', '.toml', '.cfg', '.ini', '.sh', '.txt', '.md', '.env',
}

SECRET_PATTERNS = [
    ('private key block', re.compile(r'-----BEGIN [A-Z0-9 ]*PRIVATE KEY-----')),
    ('AWS access key id', re.compile(r'\bAKIA[0-9A-Z]{16}\b')),
    ('GitHub token', re.compile(r'\bgh[pousr]_[A-Za-z0-9]{30,}\b')),
    ('Slack token', re.compile(r'\bxox[baprs]-[A-Za-z0-9-]{10,}\b')),
    (
        'hardcoded credential assignment',
        re.compile(
            r"(?i)\b(?:password|passwd|secret|api[_-]?key|access[_-]?token"
            r"|auth[_-]?token)\s*[:=]\s*[\"'][^\"']{8,}[\"']"
        ),
    ),
]


def tracked_files():
    """Return the files tracked by Git, relative to the repository root."""
    result = subprocess.run(
        ['git', 'ls-files', '-z'],
        cwd=REPO_ROOT,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        check=True,
    )
    return [entry for entry in result.stdout.decode('utf-8').split('\0') if entry]


class RequiredFilesTest(unittest.TestCase):
    """Handbook documentation deliverables must ship with the repository."""

    def test_required_files_exist(self):
        for relative_path in REQUIRED_FILES:
            with self.subTest(path=relative_path):
                self.assertTrue((REPO_ROOT / relative_path).is_file(), relative_path)


class ReadmeStandardsTest(unittest.TestCase):
    """README.md must carry every section required by the handbook."""

    @classmethod
    def setUpClass(cls):
        cls.readme = (REPO_ROOT / 'README.md').read_text(encoding='utf-8')
        cls.headings = [
            line[3:].strip()
            for line in cls.readme.splitlines()
            if line.startswith('## ')
        ]

    def test_readme_starts_with_project_title(self):
        first_line = self.readme.splitlines()[0].strip()
        self.assertTrue(first_line.startswith('# '), first_line)
        self.assertGreater(len(first_line), 1)

    def test_readme_contains_title_and_description(self):
        lines = [line for line in self.readme.splitlines() if line.strip()]
        self.assertTrue(lines[0].startswith('# '))
        self.assertGreater(len(lines[1]), 40, 'description under the title')

    def test_readme_contains_every_required_section(self):
        for section in REQUIRED_README_SECTIONS:
            with self.subTest(section=section):
                self.assertIn(section, self.headings, f'missing "## {section}"')


class ContinuousIntegrationTest(unittest.TestCase):
    """CI stays least-privilege, main-only, pinned and secret-free."""

    @classmethod
    def setUpClass(cls):
        cls.workflow = WORKFLOW_PATH.read_text(encoding='utf-8')

    def test_workflow_triggers_on_push_and_pull_request_to_main(self):
        self.assertGreaterEqual(self.workflow.count('branches: [main]'), 2)
        self.assertIn('push:', self.workflow)
        self.assertIn('pull_request:', self.workflow)

    def test_workflow_is_read_only(self):
        self.assertIn('permissions:', self.workflow)
        self.assertIn('contents: read', self.workflow)

    def test_workflow_pins_actions_to_major_versions(self):
        self.assertIn('actions/checkout@v4', self.workflow)
        self.assertIn('actions/setup-python@v5', self.workflow)
        self.assertNotRegex(self.workflow, r'uses:\s*\S+@(main|master|HEAD)\b')

    def test_workflow_uses_concurrency_cancellation(self):
        self.assertIn('concurrency:', self.workflow)
        self.assertIn('cancel-in-progress: true', self.workflow)

    def test_workflow_references_no_secrets(self):
        self.assertNotIn('${{ secrets.', self.workflow)

    def test_workflow_does_not_install_training_stack(self):
        for forbidden in ('torch', 'mmcv', 'mmseg', 'cuda'):
            self.assertNotIn(forbidden, self.workflow.lower())

    def test_workflow_byte_compiles_tracked_sources_and_runs_tests(self):
        self.assertIn("git ls-files -z '*.py' | xargs -0 -r python -m py_compile", self.workflow)
        self.assertIn('python -m pytest tests/ -q', self.workflow)


class NoSecretsInSourcesTest(unittest.TestCase):
    """Handbook rule: no credentials, tokens or keys in code or config."""

    def test_tracked_sources_contain_no_hardcoded_credentials(self):
        findings = []
        for relative_path in tracked_files():
            path = REPO_ROOT / relative_path
            if not path.is_file():
                continue
            if path.suffix not in SCANNED_SUFFIXES and path.name not in {'.gitignore', '.env'}:
                continue
            try:
                text = path.read_text(encoding='utf-8')
            except UnicodeDecodeError:
                continue
            for name, pattern in SECRET_PATTERNS:
                if pattern.search(text):
                    findings.append(f'{relative_path}: {name}')
        self.assertEqual(findings, [], 'hardcoded credentials found:\n' + '\n'.join(findings))


if __name__ == '__main__':
    unittest.main()
