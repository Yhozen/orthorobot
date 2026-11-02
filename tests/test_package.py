import importlib.util
import tempfile
import unittest
from pathlib import Path
from zipfile import ZipFile
spec = importlib.util.spec_from_file_location('package', Path(__file__).resolve().parents[1] / 'scripts/package.py')
package = importlib.util.module_from_spec(spec)
spec.loader.exec_module(package)

class PackageTests(unittest.TestCase):
    def test_archive_is_reproducible_and_safe(self):
        with tempfile.TemporaryDirectory() as tmp:
            a, b = Path(tmp) / 'a.love', Path(tmp) / 'b.love'
            package.package(a)
            package.package(b)
            self.assertEqual(a.read_bytes(), b.read_bytes())
            with ZipFile(a) as z:
                names = z.namelist()
                self.assertEqual(names, sorted(names))
                self.assertIn('main.lua', names)
                self.assertIn('maps/16.png', names)
                self.assertEqual(len([n for n in names if n.startswith('maps/') and n.endswith('.txt')]), 17)
                self.assertFalse(any(n.startswith('.') or 'save.txt' in n or 'node_modules' in n for n in names))
                self.assertIsNone(z.testzip())
