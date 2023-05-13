"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from collections import defaultdict, abc
import collections
import re
import json
from networkx import MultiDiGraph
from .Network import Network
from typing import Tuple
from graph_notebook.decorators.decorators import check_if_access_regex, \
    get_variable_injection_name_and_indices

EVENT_ADD_NODE = 'add_node'
EVENT_ADD_NODE_DATA = 'add_node_data'
EVENT_ADD_NODE_PROPERTY = 'add_node_property'
EVENT_ADD_EDGE = 'add_edge'
EVENT_ADD_EDGE_DATA = 'add_edge_data'
DEFAULT_GRP = 'DEFAULT_GROUP'
DEFAULT_RAW_GRP_KEY = '__RAW_RESULT__'
DEFAULT_LABEL_MAX_LENGTH = 10
DEPTH_GRP_KEY = 'TRAVERSAL_DEPTH'

VALID_EVENTS = [EVENT_ADD_NODE, EVENT_ADD_NODE_DATA, EVENT_ADD_NODE_PROPERTY, EVENT_ADD_EDGE, EVENT_ADD_EDGE_DATA]


class EventfulNetwork(Network):
    """
    EventfulNetwork provides hooks to receive notifications of changes
    which have taken place due to method invocations. For each method in
    the base class Network, any callbacks which are registered to the method will
    be invoked, packaging the arguments of the method invoked into a payload for
    subscribers to see/take action on.

    All method signatures for callbacks should follow the form callback(network, event_name, data)
    Callbacks will happen after the method is finished being invoked. For instance, if add_node is called,
    the EventfulNetwork will call super().add_node(...) then look for callbacks to dispatch.
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks: dict = None,
                 label_max_length: int = DEFAULT_LABEL_MAX_LENGTH,
                 edge_label_max_length: int = DEFAULT_LABEL_MAX_LENGTH, group_by_property: str = '',
                 display_property: str = '', edge_display_property: str = '',
                 tooltip_property: str = '', edge_tooltip_property: str = '',
                 ignore_groups=False, group_by_raw=False):
        if callbacks is None:
            callbacks = defaultdict(list)
        self.callbacks = callbacks
        self.label_max_length = 3 if label_max_length < 3 else label_max_length
        self.edge_label_max_length = 3 if edge_label_max_length < 3 else edge_label_max_length
        if group_by_raw:
            self.group_by_property = DEFAULT_RAW_GRP_KEY
        else:
            try:
                self.group_by_property = json.loads(group_by_property)
            except (TypeError, ValueError) as e:
                self.group_by_property = group_by_property
        self.display_property = self.convert_property_name(display_property)
        self.edge_display_property = self.convert_property_name(edge_display_property)
        self.tooltip_property = self.convert_property_name(tooltip_property) if tooltip_property \
            else self.display_property
        self.edge_tooltip_property = self.convert_property_name(edge_tooltip_property) if edge_tooltip_property \
            else self.edge_display_property
        self.ignore_groups = ignore_groups
        if graph is None:
            graph = MultiDiGraph()
        super().__init__(graph)

    def strip_and_truncate_label_and_title(self, old_label, max_len: int = 10) -> Tuple[str, str]:
        if isinstance(old_label, list) and len(old_label) == 1:
            title = str(old_label).strip("[]'")
        else:
            title = str(old_label)
        if len(title) <= max_len:
            label = title
        else:
            label = title[:max_len - 3] + '...'
        return title, label

    def single_subproperty_check_and_convert_to_tuple(self, property_with_index):
        """
        Converts a string formatted as a dict variable with an index operator to a tuple.

        Ex. "names[2]" -> (names, 2)
        """
        if re.match(check_if_access_regex, property_with_index):
            property_name, property_index = get_variable_injection_name_and_indices(raw_var=property_with_index,
                                                                                    keys_are_str=False)
            if property_name and property_index:
                property_indices_list = [property_name]
                property_indices_list.extend(property_index)
                return tuple(property_indices_list)
        return None

    def convert_multiproperties_to_tuples(self, display_params):
        if isinstance(display_params, dict):
            for k, v in display_params.items():
                converted_property = self.single_subproperty_check_and_convert_to_tuple(v)
                if converted_property:
                    display_params[k] = converted_property
        elif isinstance(display_params, str):
            converted_property = self.single_subproperty_check_and_convert_to_tuple(display_params)
            if converted_property:
                display_params = converted_property
        return display_params

    def convert_property_name(self, property_name):
        try:
            return self.convert_multiproperties_to_tuples(json.loads(property_name.strip('\'"')))
        except ValueError:
            return self.convert_multiproperties_to_tuples(property_name.strip('\'"'))

    def flatten(self, d: dict, parent_key='', sep='_') -> dict:
        """Flattens dictionaries including nested dictionaries

        Args:
            d (dict): The dictionary to flatten
            parent_key (str, optional): The parent key name to append. Defaults to ''.
            sep (str, optional): The seperator between the parent and sub key. Defaults to '_'.

        Returns:
            [dict]: The flattened dictionary
        """
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.abc.MutableMapping):
                items.extend(self.flatten(v).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def register_universal_callback(self, callback):
        """
        Registers the given callback to all events which can be emitted by the Eventful Network
        """
        if not callable(callback):
            raise ValueError("callback must be callable")

        for event_name in VALID_EVENTS:
            self.register_callback(event_name, callback)

    def register_callback(self, event, callback):
        if not callable(callback):
            raise ValueError("callback must be callable.")

        self.callbacks[event].append(callback)

    def dispatch_callbacks(self, event_name, data):
        if event_name in self.callbacks:
            for c in self.callbacks[event_name]:
                c(self, event_name, data)

    def add_node_property(self, node_id: str, key: str, value: str):
        super().add_node_property(node_id, key, value)
        data = {
            'node_id': node_id,
            'key': key,
            'value': value
        }
        self.dispatch_callbacks(EVENT_ADD_NODE_PROPERTY, data)

    def add_node(self, node_id: str, data: dict = None):
        if data is None:
            data = {}
        super().add_node(node_id, data)
        payload = {
            'node_id': node_id,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_NODE, payload)

    def add_edge(self, from_id: str, to_id: str, edge_id: str, label: str, title: str = None, data: dict = None):
        if data is None:
            data = {}
        super().add_edge(from_id, to_id, edge_id, label, data)
        payload = {
            'from_id': from_id,
            'to_id': to_id,
            'edge_id': edge_id,
            'label': label,
            'title': title,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_EDGE, payload)

    def add_node_data(self, node_id: str, data: dict = None):
        if data is None:
            data = {}
        super().add_node_data(node_id, data)
        d = {
            'node_id': node_id,
            'data': data
        }
        self.dispatch_callbacks(EVENT_ADD_NODE_DATA, d)

    def add_edge_data(self, from_id: str, to_id: str, edge_id, data: dict = None):
        if data is None:
            data = {}
        super().add_edge_data(from_id, to_id, edge_id, data)
        d = {
            'from_id': from_id,
            'to_id': to_id,
            'edge_id': edge_id,
            'data': data
        }

        self.dispatch_callbacks(EVENT_ADD_EDGE_DATA, d)
