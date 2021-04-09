"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.magics.metadata import Metric, Metadata


class TestMetadataClassFunctions(unittest.TestCase):

    def test_gremlin_profile_metadata_func(self):
        time_expected = 392.686
        predicates_expected = 16
        results_num_expected = 100
        serialization_expected = 2636.380
        results_size_expected = 23566

        gremlin_metadata = Metadata()
        with open('gremlin_profile_sample_response.txt', 'r') as profile_file:
            profile = profile_file.read()
        query_time = Metric('query_time', 'Query execution time (ms)')
        predicates = Metric('predicates', '# of predicates')
        results_metric = Metric('results', '# of results')
        seri_time_metric = Metric('seri_time', 'Serialization execution time (ms)')
        results_size_metric = Metric('results_size', 'Results size (bytes)')
        gremlin_metadata.bulk_insert_metrics([query_time, predicates, results_metric, seri_time_metric, results_size_metric])
        gremlin_metadata.set_gremlin_profile_metrics(profile)

        self.assertEqual(time_expected, query_time.value)
        self.assertEqual(predicates_expected, predicates.value)
        self.assertEqual(results_num_expected, results_metric.value)
        self.assertEqual(serialization_expected, seri_time_metric.value)
        self.assertEqual(results_size_expected, results_size_metric.value)
