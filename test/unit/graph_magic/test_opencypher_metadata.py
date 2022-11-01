import unittest

from graph_notebook.magics.metadata import build_opencypher_metadata_from_query


class TestOCMetadataClassFunctions(unittest.TestCase):
    def test_opencypher_default_query_metadata(self):
        results = {
            "results": [
                {
                    "n": {
                        "~id": "100",
                        "~entityType": "node",
                        "~labels": [
                            "airport"
                        ],
                        "~properties": {
                            "desc": "Manila, Ninoy Aquino International Airport",
                        }
                    }
                }
            ]
        }

        oc_metadata = build_opencypher_metadata_from_query(query_type='query', results=results, query_time=100.0)
        meta_dict = oc_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "query")
        self.assertEqual(meta_dict["Request execution time (ms)"], 100.0)
        self.assertEqual(meta_dict["# of results"], 1)
        self.assertIsInstance(meta_dict["Response size (bytes)"], int)

    def test_opencypher_bolt_query_metadata(self):
        results = [
            {
                "n": {
                    "desc": "Manila, Ninoy Aquino International Airport"
                }
            }
        ]

        oc_metadata = build_opencypher_metadata_from_query(query_type='bolt', results=results, results_type='bolt',
                                                           query_time=100.0)
        meta_dict = oc_metadata.to_dict()

        self.assertEqual(meta_dict["Query mode"], "bolt")
        self.assertEqual(meta_dict["Request execution time (ms)"], 100.0)
        self.assertEqual(meta_dict["# of results"], 1)
        self.assertIsInstance(meta_dict["Response size (bytes)"], int)
