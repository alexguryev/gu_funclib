import glob
import os
import shutil
import sys
import sys as _sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import write_datelog, get_datetime_str  # noqa: E402


class TestWriteDatelogRotation(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")
        self._orig_switchinterval = _sys.getswitchinterval()
        _sys.setswitchinterval(1e-6)

    def tearDown(self):
        _sys.setswitchinterval(self._orig_switchinterval)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _date_str(self):
        return get_datetime_str(dateonly=True)

    def _main_logfile(self):
        return os.path.join(self.tmpdir, f"{self._date_str()}.log")

    def _all_logfiles(self):
        return sorted(glob.glob(os.path.join(self.tmpdir, f"{self._date_str()}*.log")))

    def test_no_rotation_by_default(self):
        # regression: default max_bytes=0 -> unbounded single file, unchanged from 1.8.5
        for i in range(200):
            write_datelog(self.tmpdir, "x" * 50)
        files = self._all_logfiles()
        self.assertEqual(files, [self._main_logfile()])

    def test_rotation_creates_seq_file_when_exceeded(self):
        write_datelog(self.tmpdir, "a" * 50, max_bytes=100)  # first write, no rotation yet
        write_datelog(self.tmpdir, "b" * 50, max_bytes=100)  # file now > 100 bytes -> next call rotates
        write_datelog(self.tmpdir, "c" * 50, max_bytes=100)

        files = self._all_logfiles()
        self.assertIn(os.path.join(self.tmpdir, f"{self._date_str()}.1.log"), files)

        all_lines = []
        for f in files:
            with open(f, "r", encoding="utf-8") as fh:
                all_lines.extend(fh.readlines())
        self.assertEqual(len(all_lines), 3, "no line lost across rotation")

    def test_rotation_under_concurrent_writes_no_data_loss(self):
        M, K = 6, 40
        errors = []

        def worker(tid):
            try:
                for i in range(K):
                    write_datelog(self.tmpdir, f"thread{tid}-line{i}" + ("x" * 30), max_bytes=500)
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(M)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])

        all_lines = []
        for f in self._all_logfiles():
            with open(f, "r", encoding="utf-8") as fh:
                all_lines.extend(fh.readlines())
        self.assertEqual(len(all_lines), M * K, "no lines lost across concurrent rotation")


if __name__ == "__main__":
    unittest.main()
