import os
import sys
import shutil
import sys as _sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import make_unique_filename  # noqa: E402


class TestMakeUniqueFilenameRace(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")
        self._orig_cwd = os.getcwd()
        self._orig_switchinterval = _sys.getswitchinterval()
        _sys.setswitchinterval(1e-6)  # aggressive thread switching to expose race

    def tearDown(self):
        _sys.setswitchinterval(self._orig_switchinterval)
        os.chdir(self._orig_cwd)  # some tests chdir into tmpdir; restore before rmtree
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _base_path(self):
        p = os.path.join(self.tmpdir, "photo.png")
        with open(p, "w") as f:
            f.write("base")
        return p

    def test_race_without_reserve_reproduces_collision(self):
        # Reproduces the bug: reserve=False (default) does NOT reserve the name,
        # so concurrent callers can legitimately get identical results. This is
        # documented default behavior, not asserted to fail here — it exists to
        # prove the pre-patch code path is exercised without raising.
        base = self._base_path()
        results = []
        lock = threading.Lock()

        def worker():
            name = make_unique_filename(base)
            with lock:
                results.append(name)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 20)

    def test_reserve_true_no_collisions(self):
        # After patch: reserve=True must guarantee uniqueness under concurrency.
        base = self._base_path()
        results = []
        lock = threading.Lock()

        def worker():
            name = make_unique_filename(base, reserve=True)
            with lock:
                results.append(name)

        threads = [threading.Thread(target=worker) for _ in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(len(results), 20)
        self.assertEqual(len(set(results)), 20, "reserve=True must return unique names under concurrency")

        fdir = os.path.dirname(base)
        created = [f for f in os.listdir(fdir) if f != "photo.png"]
        self.assertEqual(len(created), 20, "reserve=True must actually create N reserved files on disk")

    def test_default_behavior_unchanged_single_threaded(self):
        # Regression: reserve param defaults to False, single-threaded behavior
        # must be byte-for-byte identical to pre-patch (1.8.5).
        base = self._base_path()
        name1 = make_unique_filename(base)
        self.assertTrue(name1.endswith("photo_00001.png"))
        self.assertFalse(os.path.exists(name1), "default (reserve=False) must NOT create the file")

    def test_exact_prefix_match_not_substring(self):
        # "photo" must not match "my_photo_00001.png" as if it were its own series.
        fdir = self.tmpdir
        base = os.path.join(fdir, "photo.png")
        with open(base, "w") as f:
            f.write("base")
        with open(os.path.join(fdir, "my_photo_00001.png"), "w") as f:
            f.write("x")

        name = make_unique_filename(base)
        self.assertTrue(os.path.basename(name).startswith("photo_"))
        self.assertEqual(os.path.basename(name), "photo_00001.png")

    def _reserve_must_not_hang(self, basename, chdir=False, timeout=5):
        # The discovery regex demands a literal dot + alphanumeric extension, so for
        # some paths it cannot see the file a previous reserve=True call created.
        # The retry loop must still converge (it advances num on O_EXCL collision)
        # instead of recomputing num=1 forever.
        if chdir:
            os.chdir(self.tmpdir)
            path = basename
        else:
            path = os.path.join(self.tmpdir, basename)
        with open(path, "w") as f:
            f.write("base")

        make_unique_filename(path, reserve=True)  # reserves <name>_00001<ext>

        box = {}

        def target():
            try:
                box["result"] = make_unique_filename(path, reserve=True)
            except Exception as e:  # pragma: no cover - surfaced via assertion below
                box["error"] = e

        t = threading.Thread(target=target, daemon=True)
        t.start()
        t.join(timeout)
        self.assertFalse(t.is_alive(), f"reserve=True hung on {basename!r} (infinite retry loop)")
        self.assertNotIn("error", box)
        return box["result"]

    def test_reserve_does_not_hang_without_extension(self):
        result = self._reserve_must_not_hang("photo")
        self.assertTrue(os.path.basename(result).startswith("photo_"))

    def test_reserve_does_not_hang_on_bare_relative_name(self):
        result = self._reserve_must_not_hang("photo.png", chdir=True)
        self.assertTrue(os.path.basename(result).startswith("photo_"))

    def test_reserve_does_not_hang_on_non_alnum_extension(self):
        result = self._reserve_must_not_hang("src.c++")
        self.assertTrue(os.path.basename(result).startswith("src_"))

    def test_number_selection_by_max_int_not_lexicographic(self):
        # Ensure numbering picks max parsed int, not lexicographic max string.
        # NOTE: with uniform case this cannot discriminate -- zero-padded fixed-width
        # numbers sort lexicographically exactly as they do numerically. See the
        # mixed-case test below for the case that actually separates the two.
        fdir = self.tmpdir
        base = os.path.join(fdir, "photo.png")
        with open(base, "w") as f:
            f.write("base")
        for n in (1, 2, 9, 10):
            with open(os.path.join(fdir, f"photo_{str(n).zfill(5)}.png"), "w") as f:
                f.write("x")

        name = make_unique_filename(base)
        self.assertEqual(os.path.basename(name), "photo_00011.png")

    def test_number_selection_survives_mixed_case_series(self):
        # ASCII 'P' < 'p', so a lexicographic max picks the *lower-numbered*
        # lowercase entry and restarts the series; parsing ints avoids that.
        fdir = self.tmpdir
        base = os.path.join(fdir, "photo.png")
        with open(base, "w") as f:
            f.write("base")
        with open(os.path.join(fdir, "PHOTO_00009.png"), "w") as f:
            f.write("x")
        with open(os.path.join(fdir, "photo_00001.png"), "w") as f:
            f.write("x")

        name = make_unique_filename(base)
        self.assertEqual(os.path.basename(name), "photo_00010.png")


if __name__ == "__main__":
    unittest.main()
