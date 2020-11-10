import unittest

from graph_notebook import __version__
from graph_notebook.widgets import get_package_json


class TestPackageVersion(unittest.TestCase):
    def test_package_versions_match(self):
        """
        Verify that the version in package.json matches the version found under src/graph_notebook/__init__.py
        """

        package_json = get_package_json()
        self.assertEqual(__version__, package_json['version'])
