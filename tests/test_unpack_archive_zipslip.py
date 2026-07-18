import os
import shutil
import sys
import tempfile
import unittest
import zipfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "gu_funclib"))
from gu_funclib import unpack_archive  # noqa: E402


class TestUnpackArchiveZipSlip(unittest.TestCase):

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="gufunclib_test_")

    def tearDown(self):
        shutil.rmtree(self.tmpdir, ignore_errors=True)

    def _make_zip_with_member(self, member_name, content=b"evil"):
        arch_path = os.path.join(self.tmpdir, "evil.zip")
        with zipfile.ZipFile(arch_path, "w") as zf:
            zi = zipfile.ZipInfo(member_name)
            zf.writestr(zi, content)
        return arch_path

    def test_relative_traversal_rejected(self):
        arch = self._make_zip_with_member("../evil.txt")
        extr_root = os.path.join(self.tmpdir, "extract_root")
        result_path, err = unpack_archive(arch, extr_root)
        self.assertIsNone(result_path)
        self.assertEqual(err, "Unsafe path in archive!")
        escaped = os.path.join(self.tmpdir, "evil.txt")
        self.assertFalse(os.path.exists(escaped), "traversal file must not land outside extract_path")

    def test_absolute_path_rejected(self):
        abs_target = os.path.join(self.tmpdir, "abs_evil.txt").replace("\\", "/")
        arch = self._make_zip_with_member("/" + abs_target.lstrip("/"))
        extr_root = os.path.join(self.tmpdir, "extract_root2")
        result_path, err = unpack_archive(arch, extr_root)
        self.assertIsNone(result_path)
        self.assertEqual(err, "Unsafe path in archive!")

    def test_unrelated_root_rejected_with_correct_message(self):
        # This vector makes os.path.commonpath() raise ValueError ("paths don't have
        # the same drive") rather than simply compare unequal; it must still be
        # reported as an unsafe path, not leak out as a generic unzip error.
        arch = self._make_zip_with_member("....//evil.txt")
        extr_root = os.path.join(self.tmpdir, "extract_root4")
        result_path, err = unpack_archive(arch, extr_root)
        self.assertIsNone(result_path)
        self.assertEqual(err, "Unsafe path in archive!")

    def test_backslash_and_nested_traversal_rejected(self):
        for member in ("..\\evil.txt", "sub/../../evil.txt"):
            with self.subTest(member=member):
                arch = self._make_zip_with_member(member)
                extr_root = os.path.join(self.tmpdir, "root_" + str(abs(hash(member))))
                result_path, err = unpack_archive(arch, extr_root)
                self.assertIsNone(result_path)
                self.assertEqual(err, "Unsafe path in archive!")

    def test_normal_archive_still_extracts(self):
        arch_path = os.path.join(self.tmpdir, "ok.zip")
        with zipfile.ZipFile(arch_path, "w") as zf:
            zf.writestr("file1.txt", "hello")
            zf.writestr("sub/file2.txt", "world")

        extr_root = os.path.join(self.tmpdir, "extract_root3")
        result_path, err = unpack_archive(arch_path, extr_root)
        self.assertIsNotNone(result_path)
        self.assertEqual(err, "")
        self.assertTrue(os.path.exists(os.path.join(result_path, "file1.txt")))
        self.assertTrue(os.path.exists(os.path.join(result_path, "sub", "file2.txt")))


if __name__ == "__main__":
    unittest.main()
