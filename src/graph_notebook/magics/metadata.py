"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
from typing import List
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

    def to_dict(self):
        metadata_dict = {}
        for metric in self.metrics.values():
            metadata_dict[metric.friendly_name] = metric.value
        return metadata_dict

    def to_json(self):
        return json.dumps(self.to_dict(), indent=4)

    def to_html(self):
        return pre_container_template.render(content=self.to_json())
