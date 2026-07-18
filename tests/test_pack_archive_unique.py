import os
import shutil
import sys
import tempfile
import time
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import pack_archive_unique  # noqa: E402


class TestPackArchiveUnique(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_duplicate_named_files(self, n):
        # n files across n subdirs, all sharing the same basename "dup.txt"
        paths = []
        for i in range(n):
            d = os.path.join(self.tmpdir, f"src{i}")
            os.makedirs(d, exist_ok=True)
            p = os.path.join(d, "dup.txt")
            with open(p, "w") as f:
                f.write(f"content-{i}")
            paths.append(p)
        return paths

    def test_names_deduplicated_correctly(self):
        files = self._make_duplicate_named_files(30)
        out = os.path.join(self.tmpdir, "out.zip")
        ok = pack_archive_unique(files, out)
        self.assertTrue(ok)

        with zipfile.ZipFile(out, "r") as zf:
            names = zf.namelist()

        self.assertEqual(len(names), 30)
        self.assertEqual(len(set(names)), 30, "all archive entry names must be unique")
        self.assertIn("dup.txt", names)
        for i in range(1, 30):
            self.assertIn(f"dup_{str(i).zfill(4)}.txt", names)

    def test_performance_scales_reasonably(self):
        # Not a strict timing assertion (flaky on CI), but a sanity bound:
        # O(n^2) namelist()-rescans made larger batches drag noticeably;
        # this just ensures a moderately large batch completes quickly.
        files = self._make_duplicate_named_files(400)
        out = os.path.join(self.tmpdir, "out.zip")
        start = time.perf_counter()
        ok = pack_archive_unique(files, out)
        elapsed = time.perf_counter() - start
        self.assertTrue(ok)
        self.assertLess(elapsed, 5.0, "packing 400 duplicate-named files took too long")


if __name__ == "__main__":
    unittest.main()
