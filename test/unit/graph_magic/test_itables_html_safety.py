"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import pandas as pd
from itables import to_html_datatable

from graph_notebook.magics import graph_magic


SCRIPT_PAYLOAD = "</script><script>alert('graph-notebook')</script>"


def test_itables_default_escapes_raw_html():
    html = to_html_datatable(
        pd.DataFrame({"value": [SCRIPT_PAYLOAD]}),
        connected=False,
    )

    assert SCRIPT_PAYLOAD not in html
    assert "&lt;/script&gt;" in html


def test_pre_encoded_query_results_are_not_escaped_twice(monkeypatch):
    monkeypatch.setattr(graph_magic, "show", to_html_datatable)
    encoded_payload = graph_magic.encode_html_chars(SCRIPT_PAYLOAD)
    html = graph_magic.show_pre_encoded_results(
        pd.DataFrame({"value": [encoded_payload]}),
        connected=False,
    )

    assert "&amp;lt;/script&amp;gt;" not in html
    assert "&lt;/script&gt;" in html


def test_pre_encoded_query_results_escape_column_labels(monkeypatch):
    monkeypatch.setattr(graph_magic, "show", to_html_datatable)
    results_df = pd.DataFrame(
        [["safe"]],
        columns=pd.Index([SCRIPT_PAYLOAD], name=SCRIPT_PAYLOAD),
    )

    html = graph_magic.show_pre_encoded_results(results_df, connected=False)

    assert SCRIPT_PAYLOAD not in html
    assert "&lt;/script&gt;" in html


def test_pre_encoded_query_results_preserve_source_and_range_index(monkeypatch):
    captured = {}

    def capture_show(results_df, **kwargs):
        captured["results_df"] = results_df
        captured["kwargs"] = kwargs

    monkeypatch.setattr(graph_magic, "show", capture_show)
    results_df = pd.DataFrame([["safe"]], columns=[0])

    graph_magic.show_pre_encoded_results(results_df, connected=False)

    assert captured["results_df"] is not results_df
    assert isinstance(results_df.index, pd.RangeIndex)
    assert isinstance(captured["results_df"].index, pd.RangeIndex)
    assert captured["results_df"].columns[0] == 0
    assert captured["kwargs"]["allow_html"] is True
