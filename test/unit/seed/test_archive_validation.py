"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import io
import os
import tarfile
import tempfile
import unittest
import zipfile

from graph_notebook.seed.load_query import validate_and_extract_archive


class TestValidateAndExtractArchive(unittest.TestCase):

    def make_tar(self, members, path):
        """Helper to build a tar.gz with given {member_name: content} dict."""
        with tarfile.open(path, 'w:gz') as tar:
            for name, content in members.items():
                info = tarfile.TarInfo(name=name)
                info.size = len(content)
                tar.addfile(info, io.BytesIO(content))

    def make_zip(self, members, path):
        """Helper to build a zip with given {member_name: content} dict."""
        with zipfile.ZipFile(path, 'w') as zf:
            for name, content in members.items():
                zf.writestr(name, content)

    def test_tar_valid_flat_members_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'valid.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_tar({'sample.gremlin': b'g.V().limit(10)'}, archive)
            validate_and_extract_archive(archive, extract_dir)
            self.assertTrue(os.path.exists(os.path.join(extract_dir, 'sample.gremlin')))

    def test_zip_valid_flat_members_extracted(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'valid.zip')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_zip({'sample.gremlin': b'g.V().limit(10)'}, archive)
            validate_and_extract_archive(archive, extract_dir)
            self.assertTrue(os.path.exists(os.path.join(extract_dir, 'sample.gremlin')))

    def test_tar_nested_directory_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'nested.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_tar({'queries/sample.gremlin': b'g.V().limit(10)'}, archive)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('nested inside a subdirectory', str(ctx.exception))

    def test_zip_nested_directory_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'nested.zip')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_zip({'queries/sample.gremlin': b'g.V().limit(10)'}, archive)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('nested inside a subdirectory', str(ctx.exception))

    def test_tar_path_traversal_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'malicious.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_tar({'../traversal.txt': b'PWNED'}, archive)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('../traversal.txt', str(ctx.exception))

    def test_zip_path_traversal_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'malicious.zip')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_zip({'../traversal.txt': b'PWNED'}, archive)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('../traversal.txt', str(ctx.exception))

    def test_tar_absolute_path_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'malicious.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            self.make_tar({'/etc/passwd': b'PWNED'}, archive)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('/etc/passwd', str(ctx.exception))

    def test_tar_symlink_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'symlink.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            with tarfile.open(archive, 'w:gz') as tar:
                info = tarfile.TarInfo(name='link.gremlin')
                info.type = tarfile.SYMTYPE
                info.linkname = '/etc/passwd'
                tar.addfile(info)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('symbolic or hard link', str(ctx.exception))

    def test_tar_hardlink_raises(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'hardlink.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            with tarfile.open(archive, 'w:gz') as tar:
                info = tarfile.TarInfo(name='link.gremlin')
                info.type = tarfile.LNKTYPE
                info.linkname = '/etc/passwd'
                tar.addfile(info)
            with self.assertRaises(ValueError) as ctx:
                validate_and_extract_archive(archive, extract_dir)
            self.assertIn('symbolic or hard link', str(ctx.exception))

    def test_tar_traversal_does_not_write_outside_dir(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive = os.path.join(tmp, 'malicious.tar.gz')
            extract_dir = os.path.join(tmp, 'out')
            os.makedirs(extract_dir)
            victim = os.path.join(tmp, 'victim.txt')
            with open(victim, 'w') as f:
                f.write('ORIGINAL')
            self.make_tar({'../victim.txt': b'PWNED'}, archive)
            with self.assertRaises(ValueError):
                validate_and_extract_archive(archive, extract_dir)
            self.assertEqual(open(victim).read(), 'ORIGINAL')


if __name__ == '__main__':
    unittest.main()
