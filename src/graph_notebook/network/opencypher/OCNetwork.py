"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import logging

from graph_notebook.network.EventfulNetwork import EventfulNetwork, DEFAULT_GRP, DEPTH_GRP_KEY, DEFAULT_RAW_GRP_KEY
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


class OCNetwork(EventfulNetwork):
    """OCNetwork extends the EventfulNetwork class and uses the add_results method to parse any response that returns
    nodes/relationships as part (or all) of the response.  Currently this only works with HTTPS response format but in
    the future, we will work to support Bolt based responses as well.
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH,
                 edge_label_max_length=DEFAULT_LABEL_MAX_LENGTH, group_by_property=LABEL_KEY,
                 display_property=LABEL_KEY, edge_display_property=EDGE_TYPE_KEY,
                 tooltip_property=None, edge_tooltip_property=None,
                 ignore_groups=False, 
                 group_by_depth=False, group_by_raw=False):
        if graph is None:
            graph = MultiDiGraph()
        if group_by_depth:
            group_by_property = DEPTH_GRP_KEY
        super().__init__(graph, callbacks, label_max_length, edge_label_max_length, group_by_property,
                         display_property, edge_display_property, tooltip_property, edge_tooltip_property,
                         ignore_groups, group_by_raw)

    def get_node_property_value(self, node: dict, props: dict, title, custom_property):
        try:
            if isinstance(custom_property, dict):
                if isinstance(custom_property[title], tuple):
                    if custom_property[title][0] in props and \
                            isinstance(props[custom_property[title][0]], list) and \
                            len(props[custom_property[title][0]]) >= 2:
                        label = props[custom_property[title][0]][custom_property[title][1]]
                    else:
                        label = title
                elif custom_property[title] in props:
                    label = props[custom_property[title]]
                elif LABEL_KEY in props:
                    label = props[LABEL_KEY]
                else:
                    label = props
            elif isinstance(custom_property, tuple) and custom_property[0] in props:
                if isinstance(props[custom_property[0]], list) and len(props[custom_property[0]]) >= 2:
                    label = props[custom_property[0]][custom_property[1]]
                else:
                    label = title
            elif custom_property in [ID_KEY, 'id']:
                label = node[ID_KEY]
            elif custom_property in [LABEL_KEY, 'label']:
                label = node[LABEL_KEY]
            elif custom_property in [VERTEX_TYPE_KEY, 'type']:
                label = node[VERTEX_TYPE_KEY]
            elif custom_property in props:
                label = props[custom_property]
            else:
                label = title
        except (KeyError, IndexError) as e:
            logger.debug(e)
            label = title

        return label

    def get_edge_property_value(self, data: dict, rel: dict, custom_property):
        if custom_property is not EDGE_TYPE_KEY:
            try:
                if isinstance(custom_property, dict):
                    if isinstance(custom_property[data['label']], tuple) and \
                            custom_property[data['label']][0] in data['properties']:
                        if isinstance(data['properties'][custom_property[data['label']][0]], list) and \
                                len(data['properties'][custom_property[data['label']][0]]) >= 2:
                            display_label = str(data['properties'][custom_property[data['label']][0]]
                                                [custom_property[data['label']][1]])
                        else:
                            display_label = rel[EDGE_TYPE_KEY]
                    else:
                        display_label = data['properties'][custom_property[rel[EDGE_TYPE_KEY]]]
                elif isinstance(custom_property, tuple) and \
                        custom_property[0] in data['properties']:
                    display_label = str(data['properties'][custom_property[0]]
                                        [custom_property[1]])
                else:
                    display_label = data['properties'][custom_property]
            except (KeyError, IndexError, TypeError) as e:
                logger.debug(e)
                display_label = rel[EDGE_TYPE_KEY]
        else:
            display_label = rel[EDGE_TYPE_KEY]

        return display_label

    def parse_node(self, node: dict, path_index: int = -2):
        """This parses the node parameter and adds the node to the network diagram

        Args:
            node (dict): The node dictionary to parse
            path_index: Position of the element in the path traversal order
        """

        depth_group = "__DEPTH-" + str(path_index//2) + "__"

        # generate placeholder tooltip from label; if not present, amalgamate node property values instead
        if LABEL_KEY in node.keys():
            if len(node[LABEL_KEY]) > 0:
                title_plc = node[LABEL_KEY][0]
                create_title_placeholder = False
            else:
                create_title_placeholder = True
        else:
            create_title_placeholder = True

        if create_title_placeholder:
            title_plc = ""
            for key in node:
                title_plc += str(node[key])

        if not isinstance(self.group_by_property, dict):  # Handle string format group_by
            try:
                if self.group_by_property == DEPTH_GRP_KEY:
                    group = depth_group
                elif self.group_by_property == DEFAULT_RAW_GRP_KEY:
                    group = str(node)
                elif self.group_by_property in [LABEL_KEY, 'labels'] and len(node[LABEL_KEY]) > 0:
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
                    if self.group_by_property[key] == DEPTH_GRP_KEY:
                        group = depth_group
                    elif self.group_by_property[key] == DEFAULT_RAW_GRP_KEY:
                        group = str(node)
                    elif self.group_by_property[key] in [LABEL_KEY, 'labels']:
                        group = node[LABEL_KEY][0]
                    elif self.group_by_property[key] in [ID_KEY, 'id']:
                        group = node[ID_KEY]
                    else:
                        group = node[PROPERTIES_KEY][self.group_by_property[key]]
                else:
                    group = DEFAULT_GRP
            except KeyError:
                group = DEFAULT_GRP

        props = self.flatten(node)
        label = self.get_node_property_value(node, props, title_plc, self.display_property)
        if not label:
            label = node[ID_KEY]
        title, label = self.strip_and_truncate_label_and_title(label, self.label_max_length)
        if self.tooltip_property and self.tooltip_property != self.display_property:
            title, label_plc = self.strip_and_truncate_label_and_title(
                self.get_node_property_value(node, props, title_plc, self.tooltip_property))
        data = {'properties': props, 'label': label, 'title': title, 'group': group}
        if self.ignore_groups:
            data['group'] = DEFAULT_GRP
        self.add_node(node[ID_KEY], data)
    
    def parse_rel(self, rel):
        data = {'properties': self.flatten(rel), 'label': rel[EDGE_TYPE_KEY], 'title': rel[EDGE_TYPE_KEY]}
        display_label = self.get_edge_property_value(data, rel, self.edge_display_property)
        edge_title, edge_label = self.strip_and_truncate_label_and_title(display_label, self.edge_label_max_length)
        if self.edge_tooltip_property and self.edge_tooltip_property != self.edge_display_property:
            edge_title = self.get_edge_property_value(data, rel, self.edge_tooltip_property)
        data['title'] = edge_title
        data['label'] = edge_label
        self.add_edge(from_id=rel[START_KEY], to_id=rel[END_KEY], edge_id=rel[ID_KEY], label=edge_label,
                      title=edge_title, data=data)

    def process_result(self, res: dict, path_index: int = -2):
        """Determines the type of element passed in and processes it appropriately

        Args:
            res (dict): The dictionary to parse
            path_index: Position of the element in the path traversal order
        """
        if ENTITY_KEY in res:
            if res[ENTITY_KEY] == NODE_ENTITY_TYPE:
                self.parse_node(res, path_index)
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
                        for path_index, res_sublist in enumerate(res[k]):
                            try:
                                self.process_result(res_sublist, path_index)
                            except TypeError as e:
                                logger.debug(f'Property {res_sublist} in list results set is invalid, skipping')
                                logger.debug(f'Error: {e}')
                                continue
