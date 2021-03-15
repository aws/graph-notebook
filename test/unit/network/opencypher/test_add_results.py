import unittest

from graph_notebook.network.opencypher.OpenCypherNetwork import OpenCypherNetwork


class TestOpenCypherAddResults(unittest.TestCase):
    def test_add_materialized_nodes_and_edges(self):
        """
        Placeholder test while we get response formats sorted out for OC.
        As of now, a fully materialized node would look something like:

        {
            "~id": "a7111ba7-0ea1-43c9-b6b2-efc5e3aea4c0",
            "~label": "person",
            "~type": "vertex",
            "firstName": "Dave",
            "lastName": "Bechberger",
            "age": 41,
            "hobbies": ["skiing", "hiking", "biking"],
        }

        And a materialized edge:
        {
            "~id" : "<id>",
            "~label" : "[<label(s)>]", //Should always be a list of strings
            "~type" : "edge",
            "~inV" : "<node id>",
            "~outV" : "<node id>",
            "stringProperty" :  "name",
            "numberProperty" :  1,
            "booleanProperty" :  true/false,
            "arrayProperty": ["this", "is", "an", "array"],
            "objectProperty": {"name": "dave"},
            "arrayOfObjects": [{"name": "dave"}, {"name": "kelvin"}, {"name": "max"}]
        }
        """
        oc_network = OpenCypherNetwork()

    def test_ensure_comments_deleted(self):
        # TODO: review comments in opencypher integration to ensure everything is
        # cleaned up.
        self.assertTrue(False)
