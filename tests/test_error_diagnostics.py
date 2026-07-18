import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import unpack_archive, check_archive, pack_archive_unique, rem_arch_tmp  # noqa: E402


class TestErrorDiagnostics(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _broken_zip(self):
        p = os.path.join(self.tmpdir, "broken.zip")
        with open(p, "wb") as f:
            f.write(b"not a real zip file at all")
        return p

    def test_unpack_archive_error_includes_exception_text(self):
        arch = self._broken_zip()
        extr_root = os.path.join(self.tmpdir, "extract_root")
        result_path, err = unpack_archive(arch, extr_root)
        self.assertIsNone(result_path)
        self.assertNotEqual(err, "Unzip error!", "message must include original exception text, not a static string")
        self.assertIn("Unzip error:", err)

    def test_check_archive_error_includes_exception_text(self):
        arch = self._broken_zip()
        count, err = check_archive(arch, {".txt"})
        self.assertEqual(count, 0)
        self.assertNotEqual(err, "Unzip error!", "message must include original exception text, not a static string")
        self.assertIn("Unzip error:", err)

    def test_pack_archive_unique_return_type_unchanged(self):
        # contract stays bool-only -> no message to embed str(e) into
        ok = pack_archive_unique(["/no/such/file.txt"], os.path.join(self.tmpdir, "out.zip"))
        self.assertIs(ok, False)

    def test_rem_arch_tmp_return_type_unchanged(self):
        ok = rem_arch_tmp(os.path.join(self.tmpdir, "does_not_exist_dir"))
        self.assertIs(ok, False)


if __name__ == "__main__":
    unittest.main()
