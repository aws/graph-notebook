"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import sys
import re
from typing import List
from requests import Response
from graph_notebook.visualization.template_retriever import retrieve_template
pre_container_template = retrieve_template("pre_container.html")


# class for individual metadata metric
class Metric(object):
    def __init__(self, name: str, friendly_name: str, default_value: any = "N/A"):
        self.name = name    # used as key metadata.metrics
        self.friendly_name = friendly_name
        self.value = default_value

    def set_value(self, value: any):
        self.value = value


# class for complete metadata object to output
class Metadata(object):
    def __init__(self):
        self.metrics = {}

    def insert_metric(self, new_metric: Metric):
        self.metrics[new_metric.name] = new_metric

    def bulk_insert_metrics(self, new_metrics: List[Metric]):
        for metric in new_metrics:
            self.insert_metric(metric)

    def set_metric_value(self, metric_name, value):
        self.metrics[metric_name].set_value(value)

    def set_request_metrics(self, res: Response):
        self.set_metric_value('request_time', 1000 * res.elapsed.total_seconds())
        self.set_metric_value('status', res.status_code)
        self.set_metric_value('status_ok', res.ok)
        self.set_metric_value('resp_size', sys.getsizeof(res.content))

    def to_dict(self):
        metadata_dict = {}
        for metric in self.metrics.values():
            metadata_dict[metric.friendly_name] = metric.value
        return metadata_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def format_dict(self):
        out_string = ""
        m_dict = self.to_dict()
        metric_name_max_len = max(map(len, self.to_dict().keys()))
        format_string = '{{key:{}}} | {{value}}'.format(metric_name_max_len)
        for metric, value in m_dict.items():
            out_string += format_string.format(key=metric, value=value)
            out_string += "\n"
        return out_string

    def to_html(self):
        return pre_container_template.render(content=self.format_dict())


def set_gremlin_profile_metrics(gremlin_metadata: Metadata, profile_str: str) -> Metadata:
    querytime_regex = re.search(r'Query Execution: (.*?)\n', profile_str)
    predicates_regex = re.search(r'# of predicates: (.*?)\n', profile_str)
    count_regex = re.search(r'Count: (.*?)\n', profile_str)
    serialization_regex = re.search(r'Serialization: (.*?)\n', profile_str)
    results_size_regex = re.search(r'Response size \(bytes\): (.*?)\n', profile_str)
    if querytime_regex:
        gremlin_metadata.set_metric_value('query_time', float(querytime_regex.group(1)))
    if predicates_regex:
        gremlin_metadata.set_metric_value('predicates', int(predicates_regex.group(1)))
    if count_regex:
        gremlin_metadata.set_metric_value('results', int(count_regex.group(1)))
    if serialization_regex:
        gremlin_metadata.set_metric_value('seri_time', float(serialization_regex.group(1)))
    if results_size_regex:
        gremlin_metadata.set_metric_value('results_size', int(results_size_regex.group(1)))
    return gremlin_metadata


def create_gremlin_metadata_obj(q_mode: str) -> Metadata:
    metadata_obj = Metadata()
    mode_metric = Metric('mode', 'Query mode', q_mode)
    query_time = Metric('query_time', 'Query execution time (ms)')
    request_time = Metric('request_time', 'Request execution time (ms)')
    status_metric = Metric('status', 'Status code')
    status_ok_metric = Metric('status_ok', 'Status OK?')
    predicates = Metric('predicates', '# of predicates')
    results_metric = Metric('results', '# of results')
    resp_size_metric = Metric('resp_size', 'Response size (bytes)')
    seri_time_metric = Metric('seri_time', 'Serialization execution time (ms)')
    results_size_metric = Metric('results_size', 'Results size (bytes)')
    if q_mode == 'explain':
        metadata_obj.bulk_insert_metrics([mode_metric, request_time, status_metric, status_ok_metric,
                                          predicates, resp_size_metric])
    elif q_mode == 'profile':
        metadata_obj.bulk_insert_metrics([mode_metric, query_time, request_time, status_metric, status_ok_metric,
                                          predicates, results_metric, resp_size_metric, seri_time_metric,
                                          results_size_metric])
    else:
        metadata_obj.bulk_insert_metrics([mode_metric, request_time, results_metric, resp_size_metric])
    return metadata_obj


def create_sparql_metadata_obj(q_mode: str) -> Metadata:
    metadata_obj = Metadata()
    mode_metric = Metric('mode', 'Query mode', q_mode)
    request_time_metric = Metric('request_time', 'Request execution time (ms)')
    status_metric = Metric('status', 'Status code')
    status_ok_metric = Metric('status_ok', 'Status OK?')
    results_metric = Metric('results', '# of results')
    resp_size_metric = Metric('resp_size', 'Response content size (bytes)')
    if q_mode == 'explain':
        metadata_obj.bulk_insert_metrics([mode_metric, request_time_metric, status_metric, status_ok_metric,
                                          resp_size_metric])
    else:
        metadata_obj.bulk_insert_metrics([mode_metric, request_time_metric, status_metric, status_ok_metric,
                                          results_metric, resp_size_metric])
    return metadata_obj


def build_sparql_metadata_from_query(query_type: str, res: Response, results: any = None, scd_query: bool = False) -> Metadata:
    if query_type == 'explain':
        sparql_metadata = create_sparql_metadata_obj('explain')
        sparql_metadata.set_request_metrics(res)
        return sparql_metadata
    else:  # default Sparql query
        sparql_metadata = create_sparql_metadata_obj('query')
        sparql_metadata.set_request_metrics(res)
        if scd_query:
            sparql_metadata.set_metric_value('results', len(results['results']['bindings']))
        return sparql_metadata


def build_gremlin_metadata_from_query(query_type: str, results: any, res: Response = None, query_time: float = None) -> Metadata:
    if query_type == 'explain':
        gremlin_metadata = create_gremlin_metadata_obj('explain')
        gremlin_metadata.set_request_metrics(res)
        gremlin_metadata.set_metric_value('predicates', int(re.search(r'# of predicates: (.*?)\n', results).group(1)))
        return gremlin_metadata
    elif query_type == 'profile':
        gremlin_metadata = create_gremlin_metadata_obj('profile')
        gremlin_metadata.set_request_metrics(res)
        gremlin_metadata = set_gremlin_profile_metrics(gremlin_metadata=gremlin_metadata, profile_str=results)
        return gremlin_metadata
    else:  # default Gremlin query
        gremlin_metadata = create_gremlin_metadata_obj('query')
        gremlin_metadata.set_metric_value('request_time', query_time)
        gremlin_metadata.set_metric_value('resp_size', sys.getsizeof(results))
        gremlin_metadata.set_metric_value('results', len(results))
        return gremlin_metadata
