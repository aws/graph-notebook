"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import json
import logging

from graph_notebook.network.EventfulNetwork import EventfulNetwork
from networkx import MultiDiGraph

logging.basicConfig()
logger = logging.getLogger(__file__)

DEFAULT_LABEL_MAX_LENGTH = 10
ENTITY_KEY = "~entityType"
ID_KEY = "~id"
START_KEY = "~start"
END_KEY = "~end"
PROPERTIES_KEY = "~properties"
VERTEX_TYPE_KEY = "~entityType"
EDGE_TYPE_KEY = "~type"
LABEL_KEY = "~labels"
NODE_ENTITY_TYPE = 'node'
REL_ENTITY_TYPE = 'relationship'
DEFAULT_GRP = 'DEFAULT_GROUP'


class OCNetwork(EventfulNetwork):
    """OCNetwork extends the EventfulNetwork class and uses the add_results method to parse any response that returns
    nodes/relationships as part (or all) of the response.  Currently this only works with HTTPS response format but in
    the future, we will work to support Bolt based responses as well.
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH,
                 rel_label_max_length=DEFAULT_LABEL_MAX_LENGTH, group_by_property=LABEL_KEY,
                 display_property=LABEL_KEY, edge_display_property=EDGE_TYPE_KEY, ignore_groups=False):
        if graph is None:
            graph = MultiDiGraph()

        self.label_max_length = 3 if label_max_length < 3 else label_max_length
        self.rel_label_max_length = 3 if rel_label_max_length < 3 else rel_label_max_length
        try:
            self.group_by_property = json.loads(group_by_property)
        except ValueError:
            self.group_by_property = group_by_property
        try:
            self.display_property = self.convert_multiproperties_to_tuples(json.loads(display_property.strip('\'"')))
        except ValueError:
            self.display_property = self.convert_multiproperties_to_tuples(display_property.strip('\'"'))
        try:
            self.edge_display_property = self.convert_multiproperties_to_tuples(
                json.loads(edge_display_property.strip('\'"')))
        except ValueError:
            self.edge_display_property = self.convert_multiproperties_to_tuples(edge_display_property.strip('\'"'))
        self.ignore_groups = ignore_groups
        super().__init__(graph, callbacks)

    def parse_node(self, node: dict):
        """This parses the node parameter and adds the node to the network diagram

        Args:
            node (dict): The node dictionary to parse
        """
        if LABEL_KEY in node.keys():
            title = node[LABEL_KEY][0]
        else:
            title = ""
            for key in node:
                title += str(node[key])

        if not isinstance(self.group_by_property, dict):  # Handle string format group_by
            try:
                if self.group_by_property in [LABEL_KEY, 'labels'] and len(node[LABEL_KEY]) > 0:
                    group = node[LABEL_KEY][0]
                elif self.group_by_property in [ID_KEY, 'id']:
                    group = node[ID_KEY]
                elif self.group_by_property in node[PROPERTIES_KEY]:
                    group = node[PROPERTIES_KEY][self.group_by_property]
                else:
                    group = DEFAULT_GRP
            except KeyError:
                group = DEFAULT_GRP
        else:  # handle dict format group_by
            try:
                if str(node[LABEL_KEY][0]) in self.group_by_property and len(node[LABEL_KEY]) > 0:
                    key = node[LABEL_KEY][0]
                    if self.group_by_property[key]['groupby'] in [LABEL_KEY, 'labels']:
                        group = node[LABEL_KEY][0]
                    else:
                        group = node[PROPERTIES_KEY][self.group_by_property[key]['groupby']]
                elif ID_KEY in self.group_by_property:
                    group = node[ID_KEY]
                else:
                    group = DEFAULT_GRP
            except KeyError:
                group = DEFAULT_GRP

        props = self.flatten(node)
        try:
            if isinstance(self.display_property, dict):
                if isinstance(self.display_property[title], tuple):
                    if self.display_property[title][0] in props and \
                            isinstance(props[self.display_property[title][0]], list) and \
                            len(props[self.display_property[title][0]]) >= 2:
                        label = props[self.display_property[title][0]][self.display_property[title][1]]
                    else:
                        label = title
                elif self.display_property[title] in props:
                    label = props[self.display_property[title]]
                elif LABEL_KEY in props:
                    label = props[LABEL_KEY]
                else:
                    label = props
            elif isinstance(self.display_property, tuple) and self.display_property[0] in props:
                if isinstance(props[self.display_property[0]], list) and len(props[self.display_property[0]]) >= 2:
                    label = props[self.display_property[0]][self.display_property[1]]
                else:
                    label = title
            elif self.display_property in [ID_KEY, 'id']:
                label = node[ID_KEY]
            elif self.display_property in [LABEL_KEY, 'label']:
                label = node[LABEL_KEY]
            elif self.display_property in [VERTEX_TYPE_KEY, 'type']:
                label = node[VERTEX_TYPE_KEY]
            elif self.display_property in props:
                label = props[self.display_property]
            else:
                label = title
        except (KeyError, IndexError) as e:
            logger.debug(e)
            label = title

        title, label = self.strip_and_truncate_label_and_title(label, self.label_max_length)
        data = {'properties': props, 'label': label, 'title': title, 'group': group}
        if self.ignore_groups:
            data['group'] = DEFAULT_GRP
        self.add_node(node[ID_KEY], data)
    
    def parse_rel(self, rel):
        data = {'properties': self.flatten(rel), 'label': rel[EDGE_TYPE_KEY], 'title': rel[EDGE_TYPE_KEY]}
        if self.edge_display_property is not EDGE_TYPE_KEY:
            try:
                if isinstance(self.edge_display_property, dict):
                    if isinstance(self.edge_display_property[data['label']], tuple) and \
                            self.edge_display_property[data['label']][0] in data['properties']:
                        if isinstance(data['properties'][self.edge_display_property[data['label']][0]], list) and \
                                len(data['properties'][self.edge_display_property[data['label']][0]]) >= 2:
                            display_label = str(data['properties'][self.edge_display_property[data['label']][0]]
                                                [self.edge_display_property[data['label']][1]])
                        else:
                            display_label = rel[EDGE_TYPE_KEY]
                    else:
                        display_label = data['properties'][self.edge_display_property[rel[EDGE_TYPE_KEY]]]
                elif isinstance(self.edge_display_property, tuple) and \
                        self.edge_display_property[0] in data['properties']:
                    display_label = str(data['properties'][self.edge_display_property[0]]
                                        [self.edge_display_property[1]])
                else:
                    display_label = data['properties'][self.edge_display_property]
            except (KeyError, IndexError, TypeError) as e:
                logger.debug(e)
                display_label = rel[EDGE_TYPE_KEY]
        else:
            display_label = rel[EDGE_TYPE_KEY]
        edge_title, edge_label = self.strip_and_truncate_label_and_title(display_label, self.rel_label_max_length)
        data['title'] = edge_title
        data['label'] = edge_label
        self.add_edge(from_id=rel[START_KEY], to_id=rel[END_KEY], edge_id=rel[ID_KEY], label=edge_label,
                      title=edge_title, data=data)

    def process_result(self, res: dict):
        """Determines the type of element passed in and processes it appropriately

        Args:
            res (dict): The dictionary to parse
        """
        if ENTITY_KEY in res:
            if res[ENTITY_KEY] == NODE_ENTITY_TYPE:
                self.parse_node(res)
            else:
                self.parse_rel(res)

    def add_results(self, results):
        """Adds the results parameter to the network

        Args:
            results (Object): Determines the type of the object and processes it appropriately
        """
        for res in results["results"]:
            if type(res) is dict:
                for k in res.keys():
                    if type(res[k]) is dict:
                        self.process_result(res[k]) 
                    elif type(res[k]) is list:
                        for res_sublist in res[k]:
                            try:
                                self.process_result(res_sublist)
                            except TypeError as e:
                                logger.debug(f'Property {res_sublist} in list results set is invalid, skipping')
                                logger.debug(f'Error: {e}')
                                continue
