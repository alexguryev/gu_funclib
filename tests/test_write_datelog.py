import os
import re
import shutil
import sys
import sys as _sys
import tempfile
import threading
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import write_datelog, get_datetime_str  # noqa: E402


class TestWriteDatelogRace(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")
        self._orig_switchinterval = _sys.getswitchinterval()
        _sys.setswitchinterval(1e-6)  # aggressive thread switching to expose race

    def tearDown(self):
        _sys.setswitchinterval(self._orig_switchinterval)
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _logfile_path(self):
        return os.path.join(self.tmpdir, f"{get_datetime_str(dateonly=True)}.log")

    def test_concurrent_writes_no_lost_or_corrupted_lines(self):
        M, K = 8, 50  # M threads x K lines each
        errors = []

        def worker(tid):
            try:
                for i in range(K):
                    write_datelog(self.tmpdir, f"thread{tid}-line{i}")
            except Exception as e:
                errors.append(e)

        threads = [threading.Thread(target=worker, args=(t,)) for t in range(M)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        self.assertEqual(errors, [])

        fpath = self._logfile_path()
        with open(fpath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        self.assertEqual(len(lines), M * K, "no lines lost or merged")
        pattern = re.compile(r"^thread\d+-line\d+\n$")
        for line in lines:
            self.assertRegex(line, pattern, "no corrupted/interleaved line")

    def test_format_and_filename_unchanged(self):
        write_datelog(self.tmpdir, "hello", indent=1)
        fpath = self._logfile_path()
        self.assertTrue(os.path.exists(fpath))
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        self.assertEqual(content, "    hello\n")


if __name__ == "__main__":
    unittest.main()
