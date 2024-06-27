"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.magics.metadata import Metric, Metadata, set_gremlin_profile_metrics


class TestMetadataClassFunctions(unittest.TestCase):

    def test_gremlin_profile_metadata_func(self):
        time_expected = 18.669
        predicates_expected = 18
        results_num_expected = 5
        serialization_expected = 15.464
        serializer_type_expected = "application/vnd.gremlin-v3.0+json"
        results_size_expected = 10162
        query_total_index_ops_expected = 18
        query_unique_index_ops_expected = 18
        query_duplication_ratio_expected = 1
        query_terms_materialized_expected = 0
        seri_total_index_ops_expected = 18
        seri_unique_index_ops_expected = 18
        seri_duplication_ratio_expected = 1.0
        seri_terms_materialized_expected = 0

        gremlin_metadata = Metadata()
        with open('gremlin_profile_sample_response.txt', 'r') as profile_file:
            profile = profile_file.read()
        query_time = Metric('query_time', 'Query execution time (ms)')
        predicates = Metric('predicates', '# of predicates')
        results_metric = Metric('results', '# of results')
        seri_time_metric = Metric('seri_time', 'Serialization execution time (ms)')
        seri_type_metric = Metric('seri_type', 'Serializer type')
        results_size_metric = Metric('results_size', 'Results size (bytes)')
        query_total_index_ops_metric = Metric('query_total_index_ops', '[Query] # of statement index ops')
        query_unique_index_ops_metric = Metric('query_unique_index_ops', '[Query]  # of unique statement index ops')
        query_duplication_ratio_metric = Metric('query_duplication_ratio', '[Query] Duplication ratio')
        query_terms_materialized_metric = Metric('query_terms_materialized', '[Query] # of terms materialized')
        seri_total_index_ops_metric = Metric('seri_total_index_ops', '[Serialization] # of statement index ops')
        seri_unique_index_ops_metric = Metric('seri_unique_index_ops',
                                              '[Serialization] # of unique statement index ops')
        seri_duplication_ratio_metric = Metric('seri_duplication_ratio', '[Serialization] Duplication ratio')
        seri_terms_materialized_metric = Metric('seri_terms_materialized', '[Serialization] # of terms materialized')
        gremlin_metadata.bulk_insert_metrics([query_time, predicates, results_metric, seri_time_metric,
                                              seri_type_metric, results_size_metric, query_total_index_ops_metric,
                                              query_unique_index_ops_metric, query_duplication_ratio_metric,
                                              query_terms_materialized_metric, seri_total_index_ops_metric,
                                              seri_unique_index_ops_metric, seri_duplication_ratio_metric,
                                              seri_terms_materialized_metric])
        gremlin_metadata = set_gremlin_profile_metrics(gremlin_metadata=gremlin_metadata, profile_str=profile)

        self.assertEqual(time_expected, query_time.value)
        self.assertEqual(predicates_expected, predicates.value)
        self.assertEqual(results_num_expected, results_metric.value)
        self.assertEqual(serialization_expected, seri_time_metric.value)
        self.assertEqual(serializer_type_expected, seri_type_metric.value)
        self.assertEqual(results_size_expected, results_size_metric.value)
        self.assertEqual(query_total_index_ops_expected, query_total_index_ops_metric.value)
        self.assertEqual(query_unique_index_ops_expected, query_unique_index_ops_metric.value)
        self.assertEqual(query_duplication_ratio_expected, query_duplication_ratio_metric.value)
        self.assertEqual(query_terms_materialized_expected, query_terms_materialized_metric.value)
        self.assertEqual(seri_total_index_ops_expected, seri_total_index_ops_metric.value)
        self.assertEqual(seri_unique_index_ops_expected, seri_unique_index_ops_metric.value)
        self.assertEqual(seri_duplication_ratio_expected, seri_duplication_ratio_metric.value)
        self.assertEqual(seri_terms_materialized_expected, seri_terms_materialized_metric.value)

    def test_gremlin_profile_metadata_large_results_and_predicates(self):
        predicates_expected = 999999
        results_num_expected = 999999

        gremlin_metadata = Metadata()
        with open('gremlin_profile_large_results_predicates.txt', 'r') as profile_file:
            profile = profile_file.read()
        query_time = Metric('query_time', 'Query execution time (ms)')
        predicates = Metric('predicates', '# of predicates')
        results_metric = Metric('results', '# of results')
        seri_time_metric = Metric('seri_time', 'Serialization execution time (ms)')
        seri_type_metric = Metric('seri_type', 'Serializer type')
        results_size_metric = Metric('results_size', 'Results size (bytes)')
        gremlin_metadata.bulk_insert_metrics([query_time, predicates, results_metric, seri_time_metric,
                                              seri_type_metric, results_size_metric])
        gremlin_metadata = set_gremlin_profile_metrics(gremlin_metadata=gremlin_metadata, profile_str=profile)

        self.assertEqual(predicates_expected, predicates.value)
        self.assertEqual(results_num_expected, results_metric.value)
