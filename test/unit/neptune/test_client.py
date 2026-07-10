"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.neptune.client import (
    ANALYTICS_CONFIG_HOST_IDENTIFIERS,
    NEPTUNE_CONFIG_HOST_IDENTIFIERS,
    is_allowed_neptune_host,
)


class TestIsAllowedNeptuneHost(unittest.TestCase):

    # ----- Positive cases: real Neptune endpoints must be accepted -----

    def test_commercial_cluster_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc123.us-east-1.neptune.amazonaws.com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_commercial_reader_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-ro-abc123.us-east-1.neptune.amazonaws.com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_commercial_instance_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-instance.abc123.us-east-1.neptune.amazonaws.com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_china_cluster_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc123.cn-north-1.neptune.amazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_china_northwest_cluster_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc123.cn-northwest-1.neptune.amazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_analytics_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "g-abcdef.g-abcdef123.us-east-1.neptune-graph.amazonaws.com",
            ANALYTICS_CONFIG_HOST_IDENTIFIERS))

    def test_c2s_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc.us-iso-east-1.c2s.ic.gov",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_sc2s_endpoint(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc.us-isob-east-1.sc2s.sgov.gov",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_bare_suffix_matches_itself(self):
        self.assertTrue(is_allowed_neptune_host(
            "neptune.amazonaws.com", NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_case_insensitive(self):
        self.assertTrue(is_allowed_neptune_host(
            "MyCluster.Cluster-Abc.US-EAST-1.Neptune.AmazonAWS.Com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_trailing_dot_is_normalized(self):
        self.assertTrue(is_allowed_neptune_host(
            "my-cluster.cluster-abc.us-east-1.neptune.amazonaws.com.",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    # ----- Regression cases: attacker bypasses must be rejected -----

    def test_rejects_original_poc_bypass(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune-graph-heli9.requestcatcher.com",
            ANALYTICS_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_neptune_graph_prefix_bypass(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune-graph.attacker.example",
            ANALYTICS_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_neptune_suffix_in_middle(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune.amazonaws.com.evil.example",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_lookalike_without_dot_boundary(self):
        self.assertFalse(is_allowed_neptune_host(
            "xneptune.amazonaws.com", NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_hyphen_prefix_lookalike(self):
        self.assertFalse(is_allowed_neptune_host(
            "xneptune-graph.amazonaws.com",
            ANALYTICS_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_dot_wildcard_bypass_from_old_regex(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptuneXamazonawsYcomZcn", NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_amazonaws_lookalike_com_cn(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune-x.myamazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_url_shaped_input(self):
        self.assertFalse(is_allowed_neptune_host(
            "https://neptune.amazonaws.com/",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_input_with_userinfo(self):
        self.assertFalse(is_allowed_neptune_host(
            "attacker@neptune.amazonaws.com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_input_with_query_string(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune.amazonaws.com?x=1",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_input_with_fragment(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune.amazonaws.com#frag",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_empty_hostname(self):
        self.assertFalse(is_allowed_neptune_host(
            "", NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_none_hostname(self):
        self.assertFalse(is_allowed_neptune_host(
            None, NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_rejects_non_string_hostname(self):
        self.assertFalse(is_allowed_neptune_host(
            12345, NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_empty_allowlist_rejects_everything(self):
        self.assertFalse(is_allowed_neptune_host(
            "my-cluster.us-east-1.neptune.amazonaws.com", []))

    # ----- Custom allowlist handling -----

    def test_custom_allowlist_accepts_subdomain(self):
        self.assertTrue(is_allowed_neptune_host(
            "foo.internal.example.com", ["internal.example.com"]))

    def test_custom_allowlist_rejects_lookalike(self):
        self.assertFalse(is_allowed_neptune_host(
            "internal.example.com.evil.tld", ["internal.example.com"]))

    def test_custom_allowlist_ignores_empty_entries(self):
        self.assertFalse(is_allowed_neptune_host(
            "attacker.example.com", ["", None, "  "]))

    # ----- Single-label wildcard (``*``) handling -----

    def test_wildcard_matches_legacy_china_form(self):
        self.assertTrue(is_allowed_neptune_host(
            "instance.cluster.neptune.cn-north-1.amazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_wildcard_matches_northwest_legacy_china_form(self):
        self.assertTrue(is_allowed_neptune_host(
            "instance.cluster.neptune.cn-northwest-1.amazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_wildcard_matches_pattern_directly(self):
        self.assertTrue(is_allowed_neptune_host(
            "neptune.evil.amazonaws.com.cn",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_wildcard_consumes_exactly_one_label(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune.foo.bar.amazonaws.com.cn",
            ["neptune.*.amazonaws.com.cn"]))
        self.assertFalse(is_allowed_neptune_host(
            "neptune.amazonaws.com.cn",
            ["neptune.*.amazonaws.com.cn"]))

    def test_wildcard_rejects_prefix_lookalike(self):
        self.assertFalse(is_allowed_neptune_host(
            "evilneptune.foo.amazonaws.com.cn",
            ["neptune.*.amazonaws.com.cn"]))

    def test_wildcard_does_not_match_wrong_tail(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune.foo.amazonaws.com",
            ["neptune.*.amazonaws.com.cn"]))
        self.assertFalse(is_allowed_neptune_host(
            "neptune.foo.evilamazonaws.com.cn",
            ["neptune.*.amazonaws.com.cn"]))

    def test_rejects_empty_label(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune..amazonaws.com.cn", NEPTUNE_CONFIG_HOST_IDENTIFIERS))

    def test_wildcard_still_rejects_original_poc(self):
        self.assertFalse(is_allowed_neptune_host(
            "neptune-graph-heli9.requestcatcher.com",
            NEPTUNE_CONFIG_HOST_IDENTIFIERS))


if __name__ == '__main__':
    unittest.main()
