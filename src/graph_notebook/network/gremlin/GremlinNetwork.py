"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import hashlib
import json
import uuid
import logging
from decimal import *
from enum import Enum

from graph_notebook.network.EventfulNetwork import EventfulNetwork, DEFAULT_GRP, DEPTH_GRP_KEY, DEFAULT_RAW_GRP_KEY
from gremlin_python.process.traversal import T, Direction
from gremlin_python.structure.graph import Path, Vertex, Edge
from networkx import MultiDiGraph

logging.basicConfig()
logger = logging.getLogger(__file__)

T_LABEL = 'T.label'
T_ID = 'T.id'

INVALID_PATH_ERROR = ValueError("results must be a path with the pattern Vertex -> Edge -> Vertex.")
INVALID_VERTEX_ERROR = ValueError("when adding a vertex, object must be of type Vertex or Dict")
INVALID_VERTEX_PATH_PATTERN_ERROR = ValueError("found vertex pattern on an Edge object")
SAME_DIRECTION_ADJACENT_VERTICES = ValueError("Found two vertices with the same direction")

DEFAULT_LABEL_MAX_LENGTH = 10
TO_DISABLED = {"to": {"enabled": False}}
UNDIRECTED_EDGE = {
    "arrows": TO_DISABLED
}


class PathPattern(Enum):
    V = "V"
    IN_V = "INV"
    OUT_V = "OUTV"
    E = "E"
    IN_E = "INE"
    OUT_E = "OUTE"


def parse_pattern_list_str(pattern_str: str) -> list:
    pattern_list = []
    patterns = pattern_str.split(',')
    for p in patterns:
        pattern_list.append(PathPattern(p.strip().upper()))
    return pattern_list


V_PATTERNS = [PathPattern.V, PathPattern.IN_V, PathPattern.OUT_V]
E_PATTERNS = [PathPattern.E, PathPattern.IN_E, PathPattern.OUT_E]


def generate_id_from_dict(data: dict) -> str:
    # Handle cases where user requests '~label' in valueMap step, since json can't serialize non-string keys
    if T.label in data.keys():
        data['label'] = data[T.label]
        del data[T.label]
    for k in data.keys():
        if isinstance(data[k], dict):
            if T.id in data[k]:
                data[k]['id'] = data[k][T.id]
                del data[k][T.id]
            if T.label in data[k]:
                data[k]['label'] = data[k][T.label]
                del data[k][T.label]
    data_str = json.dumps(data, default=str)
    hashed = hashlib.md5(data_str.encode())
    generate_id = hashed.hexdigest()
    return f'graph_notebook-{generate_id}'


def get_id(element):
    """
    extract id from a given element for use in the GremlinNetwork
    """
    if isinstance(element, Vertex):
        element_id = str(element.id)
    elif isinstance(element, Edge):
        element_id = str(element.label)
    elif isinstance(element, dict):
        if T.id in element:
            element_id = element[T.id]
        elif 'id' in element:
            element_id = element['id']
        else:
            element_id = generate_id_from_dict(element)
    else:
        element_id = str(element)

    if isinstance(element_id, uuid.UUID):
        element_id = str(element_id)

    return element_id


class GremlinNetwork(EventfulNetwork):
    """
    GremlinNetwork extends the Network class and uses the add_results method to parse two specific types of responses

    1. A query which returns in the format of a path whose objects are in the order Vertex -> Edge -> Vertex.
    2. A query which returns a path as a valueMap. In this case, we will assume that the order is Vertex -> Edge -> Vertex.
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH,
                 edge_label_max_length=DEFAULT_LABEL_MAX_LENGTH, group_by_property=None, display_property=None,
                 edge_display_property=None, tooltip_property=None, edge_tooltip_property=None, ignore_groups=False,
                 group_by_depth=False, group_by_raw=False, using_http=False):
        if graph is None:
            graph = MultiDiGraph()
        if group_by_depth:
            group_by_property = DEPTH_GRP_KEY
        if not group_by_property:
            group_by_property = 'label' if using_http else T_LABEL
        if not display_property:
            display_property = 'label' if using_http else T_LABEL
        if not edge_display_property:
            edge_display_property = 'label' if using_http else T_LABEL
        super().__init__(graph, callbacks, label_max_length, edge_label_max_length, group_by_property,
                         display_property, edge_display_property, tooltip_property, edge_tooltip_property,
                         ignore_groups, group_by_raw)

    def get_dict_element_property_value(self, element, k, temp_label, custom_property):
        property_value = None
        if isinstance(custom_property, dict):
            try:
                if isinstance(custom_property[temp_label], tuple) and isinstance(element[k], list):
                    if str(k) == custom_property[temp_label][0]:
                        try:
                            property_value = element[k][custom_property[temp_label][1]]
                        except (TypeError, IndexError):
                            logger.debug(f"Failed to index into sub-property for: {element[k]} and "
                                         f"{custom_property[temp_label]}")
                            return
                elif str(k) == custom_property[temp_label]:
                    property_value = element[k]
            except KeyError:
                return
        elif isinstance(custom_property, tuple):
            if str(k) == custom_property[0] and isinstance(element[k], list):
                try:
                    property_value = element[k][custom_property[1]]
                except IndexError:
                    logger.debug(f"Failed to index into sub-property for: {element[k]} and "
                                 f"{custom_property[0]}")
                    return
        elif str(k) == custom_property:
            property_value = element[k]

        return property_value

    def get_explicit_vertex_property_value(self, node_id, temp_label, custom_property):
        property_value = None
        if custom_property in [T_ID, 'id']:
            property_value = str(node_id)
        elif isinstance(custom_property, dict):
            try:
                if custom_property[temp_label] in [T_ID, 'id']:
                    property_value = str(node_id)
            except KeyError:
                return
        return property_value

    def get_explicit_edge_property_value(self, data, edge, custom_property):
        property_value = None
        if isinstance(custom_property, dict):
            try:
                property_value = data['properties'][custom_property[edge.label]]
            except KeyError:
                return
        else:
            if custom_property in [T_LABEL, 'label']:
                property_value = edge.label
            else:
                try:
                    property_value = data['properties'][custom_property]
                except KeyError:
                    return
        return property_value

    def add_results_with_pattern(self, results, pattern_list: list):
        """
        Allow an expression of a path pattern along with results to help parse the direction a path is flowing.
        Valid patterns are V, inV, outV, E, inE, outE. No two edges may be adjacent, however, two vertices can be.
        This alternate way of parsing results is to prevent the behavior of an edge which is represented by string
        being unable to be discerned from a node, leading to a rendered query showing blank edges with an intermediary
        node originally meant to be an edge label. For example:

        g.V().outE().inV().path().by('code').by('dist')

        The above will give back something such as:
        => path[FLL, 982, BQN]

        We want 982 to show as the label between FLL and BQN. For this, we could use the pattern V,outE,inV
        :param results: The list of path results
        :param pattern_list: The list of patterns to be used in order while traversing a path
        :return:
        """
        if not isinstance(results, list):
            raise ValueError("results must be a list of paths")

        for path in results:
            if not isinstance(path, Path):
                raise ValueError("all entries in results must be paths")

            if type(path[0]) is Edge or type(path[-1]) is Edge:
                raise INVALID_PATH_ERROR

            path_index = 0
            while path_index < len(path):
                for i in range(len(pattern_list)):
                    if path_index >= len(path):
                        break

                    path_pattern = pattern_list[i]
                    previous_pattern = pattern_list[i - 1] if i != 0 else pattern_list[-1]
                    next_pattern = pattern_list[i + 1] if i < len(pattern_list) - 1 else pattern_list[0]

                    current_node_id = str(get_id(path[path_index]))
                    try:
                        prev_node_id = str(get_id(path[path_index - 1]))
                    except IndexError:
                        prev_node_id = None
                    try:
                        next_node_id = str(get_id(path[path_index + 1]))
                    except IndexError:
                        next_node_id = None

                    # the current pattern is V, inV, or outV
                    if path_pattern in V_PATTERNS:
                        # we cannot reconcile an edge type with a node
                        if type(path[path_index]) is Edge:
                            raise INVALID_VERTEX_PATH_PATTERN_ERROR

                        # add the vertex, no matter what patterns border a vertex pattern, it will always be added.
                        self.add_vertex(path[path_index], path_index=i)
                        # if the path index is over 0, we need to handle edges between this node and the previous one
                        if path_index > 0:
                            if path_pattern == PathPattern.V:
                                # two V patterns next to each other is an undirected, unlabeled edge
                                if previous_pattern == PathPattern.V:
                                    self.add_blank_edge(prev_node_id,
                                                        current_node_id,
                                                        undirected=True)
                                # IN_V -> V will draw an outgoing edge from the current element to the previous one.
                                elif previous_pattern == PathPattern.IN_V:
                                    self.add_blank_edge(path[path_index], path[path_index - 1], undirected=False)
                                # OUT_V -> V will draw an outgoing edge from the previous element to the current one.
                                elif previous_pattern == PathPattern.OUT_V:
                                    self.add_blank_edge(path[path_index - 1], path[path_index], undirected=False)
                            # path_pattern (IN_V) <- previous_pattern (V, OUT_V)
                            elif path_pattern == PathPattern.IN_V and previous_pattern not in E_PATTERNS:
                                # draw an unlabeled, directed edge from previous -> current
                                # we can only process V and OUT_V as no two adjacent vertices can both be incoming.
                                if (previous_pattern == PathPattern.V or PathPattern.OUT_V) and path_index > 0:
                                    self.add_blank_edge(prev_node_id, current_node_id, undirected=False)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                            # path_pattern (OUT_V) -> previous_pattern (V, IN_V)
                            elif path_pattern == PathPattern.OUT_V and previous_pattern not in E_PATTERNS:
                                # draw an unlabeled, directed edge from current -> previous
                                # we can only process V and IN_V as no two adjacent vertices can both be outgoing.
                                if (previous_pattern == PathPattern.V or PathPattern.IN_V) and path_index > 0:
                                    self.add_blank_edge(current_node_id, prev_node_id, undirected=False)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                    elif path_pattern in E_PATTERNS:
                        # if the type of the given path element is not Edge,
                        # draw an undirected edge using this element for edge data
                        edge = path[path_index]

                        if path_pattern == PathPattern.E:
                            # V -> V where the Vertex pattern is identical on either side of the edge
                            if next_pattern == previous_pattern:
                                # this is only valid if both are V, two connected vertices cannot have same direction
                                if next_pattern == PathPattern.V:
                                    self.add_path_edge(edge, prev_node_id, next_node_id, UNDIRECTED_EDGE)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                            # IN_V -> E -> V
                            elif previous_pattern == PathPattern.IN_V:
                                self.add_path_edge(edge, next_node_id, prev_node_id)
                            # OUT_V -> E -> V
                            elif previous_pattern == PathPattern.OUT_V:
                                self.add_path_edge(edge, prev_node_id, next_node_id)
                        # If the edge direction is specified, use it as the source of truth
                        elif path_pattern == PathPattern.IN_E:
                            self.add_path_edge(edge, from_id=next_node_id, to_id=prev_node_id)
                        elif path_pattern == PathPattern.OUT_E:
                            self.add_path_edge(edge, from_id=prev_node_id, to_id=next_node_id)
                    else:
                        raise INVALID_PATH_ERROR
                    path_index += 1

        return

    def add_results(self, results, is_http=False):
        """
        receives path results and traverses them to add nodes and edges to the network graph.
        We will look at sets of three in a path to form a vertex -> edge -> vertex pattern. All other
        patters will be considered invalid at this time.

        :param results: the data to be processed. Must be of type :type Path
        :param is_http: A flag indicating the type of token keys returned
        :return:
        """
        if not isinstance(results, list):
            raise ValueError("results must be a list of paths")

        if is_http:
            gremlin_id = 'id'
            gremlin_label = 'label'
        else:
            gremlin_id = T.id
            gremlin_label = T.label

        for path_index, path in enumerate(results):
            if isinstance(path, Path):
                if type(path[0]) is Edge or type(path[-1]) is Edge:
                    raise INVALID_PATH_ERROR

                for i in range(len(path)):
                    if isinstance(path[i], dict):
                        is_elementmap = False
                        if gremlin_id in path[i] and gremlin_label in path[i]:
                            for prop, value in path[i].items():
                                # ID and/or Label property keys could be renamed by a project() step
                                if isinstance(value, str) and prop not in [gremlin_id, gremlin_label]:
                                    is_elementmap = True
                                    break
                                elif isinstance(value, dict):
                                    if prop in [Direction.IN, Direction.OUT]:
                                        is_elementmap = True
                                        break
                                elif isinstance(value, list):
                                    break
                                elif not isinstance(value, (str, list, dict)):
                                    is_elementmap = True
                                    break
                        if is_elementmap:
                            self.insert_elementmap(path[i], check_emap=True, path_element=path, index=i)
                        else:
                            self.insert_path_element(path, i)
                    else:
                        self.insert_path_element(path, i)
            elif isinstance(path, dict) and gremlin_id in path.keys() and gremlin_label in path.keys():
                self.insert_elementmap(path, index=path_index)
            else:
                raise ValueError("all entries in results must be paths or elementMaps")

    def add_vertex(self, v, path_index: int = -1):
        """
        Adds a vertex to the network. If v is of :type Vertex, we will gather its id and label.
        If v comes from a valueMap, it will be a dict, with the keys T.label and T.ID being present in
        the dict for gathering the label and id, respectively.

        :param v: The vertex taken from a path traversal object.
        :param path_index: Position of the element in the path traversal order
        """
        depth_group = "__DEPTH-" + str(path_index) + "__"
        node_id = ''
        if type(v) is Vertex:
            if isinstance(v.id, uuid.UUID):
                node_id = str(v.id)
            else:
                node_id = v.id
            title = v.label
            label_full = ''
            tooltip_display_is_set = True
            using_custom_tooltip = False
            if self.tooltip_property and self.tooltip_property != self.display_property:
                tooltip_display_is_set = False
                using_custom_tooltip = True
            vertex_dict = v.__dict__
            if not isinstance(self.group_by_property, dict):  # Handle string format group_by
                if str(self.group_by_property) == DEFAULT_RAW_GRP_KEY:
                    group = str(v)
                elif str(self.group_by_property) in [T_LABEL, 'label']:  # this handles if it's just a string
                    # This sets the group key to the label if either "label" is passed in or
                    # T.label is set in order to handle the default case of grouping by label
                    # when no explicit key is specified
                    group = v.label
                elif str(self.group_by_property) in [T_ID, 'id']:
                    group = v.id
                elif self.group_by_property == DEPTH_GRP_KEY:
                    group = depth_group
                else:
                    group = DEFAULT_GRP
            else:  # handle dict format group_by
                try:
                    if str(v.label) in self.group_by_property:
                        if self.group_by_property[str(v.label)] == DEFAULT_RAW_GRP_KEY:
                            group = str(v)
                        elif self.group_by_property[str(v.label)] in [T_LABEL, 'label']:
                            group = v.label
                        elif self.group_by_property[str(v.label)] in [T_ID, 'id']:
                            group = v.id
                        elif self.group_by_property[str(v.label)] == DEPTH_GRP_KEY:
                            group = depth_group
                        else:
                            group = vertex_dict[self.group_by_property[str(v.label)]]
                    else:
                        group = DEFAULT_GRP
                except KeyError:
                    group = DEFAULT_GRP

            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'

            if self.display_property:
                label_property_raw_value = self.get_explicit_vertex_property_value(node_id, title,
                                                                                   self.display_property)
                if label_property_raw_value:
                    label_full, label = self.strip_and_truncate_label_and_title(label_property_raw_value,
                                                                                self.label_max_length)
                    if not using_custom_tooltip:
                        title = label_full

            if using_custom_tooltip:
                tooltip_property_raw_value = self.get_explicit_vertex_property_value(node_id, title,
                                                                                      self.tooltip_property)
                if tooltip_property_raw_value:
                    title, label_plc = self.strip_and_truncate_label_and_title(tooltip_property_raw_value,
                                                                               self.label_max_length)
                    tooltip_display_is_set = True

            if not tooltip_display_is_set and label_full:
                title = label_full

            data = {'label': str(label).strip("[]'"), 'title': title, 'group': group,
                    'properties': {'id': node_id, 'label': label_full}}
        elif type(v) is dict:
            properties = {}
            title = ''
            label = ''
            label_full = ''
            group = ''
            display_is_set = False
            using_custom_tooltip = False
            tooltip_display_is_set = True
            group_is_set = False
            if self.tooltip_property and self.tooltip_property != self.display_property:
                using_custom_tooltip = True
                tooltip_display_is_set = False
            # Before looping though properties, we first search for T.label in vertex dict, then set title = T.label
            # Otherwise, we will hit KeyError if we don't iterate through T.label first to set the title
            # Since it is needed for checking for the vertex label's desired grouping behavior in group_by_property
            if T.label in v.keys() or 'label' in v.keys():
                label_key = T.label if T.label in v.keys() else 'label'
                title_plc = str(v[label_key])
                title, label = self.strip_and_truncate_label_and_title(title_plc, self.label_max_length)
            else:
                title_plc = ''
                group = DEFAULT_GRP

            if str(self.group_by_property) == DEFAULT_RAW_GRP_KEY:
                group = str(v)
                group_is_set = True
            for k in v:
                if str(k) in [T_ID, 'id']:
                    node_id = str(v[k])

                if isinstance(v[k], dict):
                    properties[k] = str(v[k])
                elif isinstance(v[k], list):
                    copy_val = v[k]
                    for i, subvalue in enumerate(copy_val):
                        if isinstance(subvalue, Decimal):
                            copy_val[i] = float(subvalue)
                    properties[k] = copy_val
                elif isinstance(v[k], Decimal):
                    properties[k] = float(v[k])
                elif isinstance(v[k], uuid.UUID):
                    properties[k] = str(v[k])
                else:
                    properties[k] = v[k]

                if not group_is_set:
                    if isinstance(self.group_by_property, dict):
                        try:
                            if DEPTH_GRP_KEY == self.group_by_property[title_plc]:
                                group = depth_group
                                group_is_set = True
                            elif DEFAULT_RAW_GRP_KEY == self.group_by_property[title_plc]:
                                group = str(v)
                                group_is_set = True
                            elif str(k) == self.group_by_property[title_plc]:
                                group = str(v[k])
                                group_is_set = True
                        except KeyError:
                            pass
                    else:
                        if DEPTH_GRP_KEY == self.group_by_property:
                            group = depth_group
                            group_is_set = True
                        elif str(k) == self.group_by_property:
                            group = str(v[k])
                            group_is_set = True
                if not display_is_set:
                    label_property_raw_value = self.get_dict_element_property_value(v, k, title_plc,
                                                                                    self.display_property)
                    if label_property_raw_value:
                        label_full, label = self.strip_and_truncate_label_and_title(label_property_raw_value,
                                                                                    self.label_max_length)
                        if not using_custom_tooltip:
                            title = label_full
                        display_is_set = True
                if not tooltip_display_is_set:
                    tooltip_property_raw_value = self.get_dict_element_property_value(v, k, title_plc,
                                                                                      self.tooltip_property)
                    if tooltip_property_raw_value:
                        title, label_plc = self.strip_and_truncate_label_and_title(tooltip_property_raw_value,
                                                                                   self.label_max_length)
                        tooltip_display_is_set = True

            if not tooltip_display_is_set and label_full:
                title = label_full

            if not group and not group_is_set:
                group = DEFAULT_GRP

            # handle when there is no id in a node. In this case, we will generate one which
            # is consistently regenerated so that duplicate dicts will be reduced to the same vertex.
            if node_id == '':
                node_id = f'{generate_id_from_dict(v)}'

            # similarly, if there is no label, we must generate one. This will be a concatenation
            # of all values in the dict
            if title == '':
                for key in v:
                    title += str(v[key])
            if label == '':
                label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
            data = {'properties': properties, 'label': label, 'title': title, 'group': group}
        else:
            node_id = str(v)
            title = str(v)
            if self.group_by_property == DEPTH_GRP_KEY:
                group = depth_group
            elif self.group_by_property == DEFAULT_RAW_GRP_KEY:
                group = str(v)
            else:
                group = DEFAULT_GRP
            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
            data = {'title': title, 'label': label, 'group': group}

        if self.ignore_groups:
            data['group'] = DEFAULT_GRP
        self.add_node(node_id, data)

    def add_path_edge(self, edge, from_id='', to_id='', data=None):
        if data is None:
            data = {}

        if type(edge) is Edge:
            from_id = from_id if from_id != '' else edge.outV.id
            if isinstance(from_id, uuid.UUID):
                from_id = str(from_id)
            to_id = to_id if to_id != '' else edge.inV.id
            if isinstance(to_id, uuid.UUID):
                to_id = str(to_id)
            edge_id = str(edge.id) if isinstance(edge.id, uuid.UUID) else edge.id
            edge_label_full = ''
            using_custom_tooltip = False
            tooltip_display_is_set = True
            edge_title = edge.label
            if self.edge_tooltip_property and self.edge_tooltip_property != self.edge_display_property:
                using_custom_tooltip = True
                tooltip_display_is_set = False
            data['properties'] = {'id': edge_id, 'label': edge.label, 'outV': str(edge.outV), 'inV': str(edge.inV)}

            edge_label = edge_title if len(edge_title) <= self.edge_label_max_length \
                else edge_title[:self.edge_label_max_length - 3] + '...'

            if self.edge_display_property:
                label_property_raw_value = self.get_explicit_edge_property_value(data, edge, self.edge_display_property)
                if label_property_raw_value:
                    edge_label_full, edge_label = self.strip_and_truncate_label_and_title(label_property_raw_value,
                                                                                          self.edge_label_max_length)
                    if not using_custom_tooltip:
                        edge_title = edge_label_full

            if using_custom_tooltip:
                tooltip_property_raw_value = self.get_explicit_edge_property_value(data, edge,
                                                                                   self.edge_tooltip_property)
                if tooltip_property_raw_value:
                    edge_title, label_plc = self.strip_and_truncate_label_and_title(tooltip_property_raw_value,
                                                                                    self.edge_label_max_length)
                    tooltip_display_is_set = True

            if not tooltip_display_is_set and edge_label_full:
                edge_title = edge_label_full

            self.get_explicit_edge_property_value(data, edge, self.edge_tooltip_property)

            data['title'] = edge_title
            self.add_edge(from_id=from_id, to_id=to_id, edge_id=edge_id, label=edge_label, title=edge_title,
                          data=data)
        elif type(edge) is dict:
            properties = {}
            edge_id = ''
            edge_label = ''
            edge_label_full = ''
            edge_title = ''
            display_is_set = False
            tooltip_display_is_set = True
            using_custom_tooltip = False
            if self.edge_tooltip_property and self.edge_tooltip_property != self.edge_display_property:
                using_custom_tooltip = True
                tooltip_display_is_set = False
            if T.label in edge.keys() or 'label' in edge.keys():
                label_key = T.label if T.label in edge.keys() else 'label'
                edge_title_plc = str(edge[label_key])
                edge_title, edge_label = self.strip_and_truncate_label_and_title(edge_title_plc,
                                                                                 self.edge_label_max_length)
            else:
                edge_title_plc = ''
            for k in edge:
                if str(k) in [T_ID, 'id']:
                    edge_id = str(edge[k])

                if isinstance(edge[k], dict):  # Handle Direction properties, where the value is a map
                    properties[k] = get_id(edge[k])
                elif isinstance(edge[k], Decimal):
                    properties[k] = float(edge[k])
                elif isinstance(edge[k], uuid.UUID):
                    properties[k] = str(edge[k])
                else:
                    properties[k] = edge[k]

                if self.edge_display_property not in [T_LABEL, 'label'] and not display_is_set:
                    label_property_raw_value = self.get_dict_element_property_value(edge, k, edge_title_plc,
                                                                                    self.edge_display_property)
                    if label_property_raw_value:
                        edge_label_full, edge_label = self.strip_and_truncate_label_and_title(
                            label_property_raw_value, self.edge_label_max_length)
                        if not using_custom_tooltip:
                            edge_title = edge_label_full
                        display_is_set = True
                if not tooltip_display_is_set:
                    tooltip_property_raw_value = self.get_dict_element_property_value(edge, k, edge_title_plc,
                                                                                      self.edge_tooltip_property)
                    if tooltip_property_raw_value:
                        edge_title, label_plc = self.strip_and_truncate_label_and_title(tooltip_property_raw_value,
                                                                                        self.edge_label_max_length)
                        tooltip_display_is_set = True

            if not tooltip_display_is_set and edge_label_full:
                edge_title = edge_label_full

            data['properties'] = properties
            data['title'] = edge_title
            self.add_edge(from_id=from_id, to_id=to_id, edge_id=edge_id, label=edge_label, title=edge_title, data=data)
        else:
            edge_title, edge_label = self.strip_and_truncate_label_and_title(edge, self.edge_label_max_length)
            data['title'] = edge_title
            self.add_edge(from_id=from_id, to_id=to_id, edge_id=edge, label=edge_label, title=edge_title, data=data)

    def add_blank_edge(self, from_id, to_id, edge_id=None, undirected=True, label=''):
        """
        Add a blank edge with no label and no direction between two nodes.
        In gremlin, we can only be sure that a given object is an edge if that is
        its given type. This method will add an edge with a generated id between two
        nodes. The edge will have no label, and it will have its arrow disabled.

        NOTE: this may mark something as undirected, but the networkx graph
        will still treat the edge as if it were. This may cause us problems if we
        try to expose networkx graph algorithms
        """
        if edge_id is None:
            edge_id = str(uuid.uuid4())
        edge_data = UNDIRECTED_EDGE if undirected else {}
        self.add_edge(from_id=from_id, to_id=to_id, edge_id=edge_id, label=label, title=label, data=edge_data)

    def insert_path_element(self, path, i):
        if i == 0:
            self.add_vertex(path[i], path_index=0)
            return

        if type(path[i]) is Edge:
            edge = path[i]
            path_left = get_id(path[i - 1])
            path_right = get_id(path[i + 1])

            # If the edge is an object type but its vertices aren't, then the ID contained
            # in the edge won't be the same as the ids used to store those two vertices.
            # For example, g.V().inE().outV().path().by(valueMap()).by().by(valueMap(true)
            # will yield a V, E, V pattern where the first vertex is a dict without T.id, the edge
            # will be an Edge object, and the second vertex will be a dict with T.id.
            if edge.outV.id == path_left or edge.inV.id == path_right:
                from_id = path_left
                to_id = path_right
                self.add_path_edge(path[i], from_id, to_id)
            elif edge.inV.id == path_left or edge.outV.id == path_right:
                from_id = path_right
                to_id = path_left
                self.add_path_edge(path[i], from_id, to_id)
            else:
                from_id = path_left
                to_id = path_right
                self.add_blank_edge(from_id, to_id, edge.id, label=edge.label)
            return
        else:
            from_id = get_id(path[i - 1])

        self.add_vertex(path[i], path_index=i)
        last_path = path[i - 1]
        if type(last_path) is not Edge:
            if type(last_path) is dict:
                if Direction.IN not in last_path and 'IN' not in last_path:
                    self.add_blank_edge(from_id, get_id(path[i]))
            else:
                self.add_blank_edge(from_id, get_id(path[i]))

    def insert_elementmap(self, e_map, check_emap=False, path_element=None, index=None):
        """
        Add a vertex or edge that has been returned by an elementMap query step.

        Any elementMap representations of edges must be directed, and contain both of the Direction.IN and Direction.OUT
        properties. If the elementMap contains neither of these, then we assume it is a vertex.

        :param e_map: A dictionary containing the elementMap representation of a vertex or an edge
        """
        # Handle directed edge elementMap
        if (Direction.IN in e_map.keys() and Direction.OUT in e_map.keys()) \
                or ('IN' in e_map.keys() and 'OUT' in e_map.keys()):
            out_prop = Direction.OUT if Direction.OUT in e_map.keys() else 'OUT'
            in_prop = Direction.IN if Direction.IN in e_map.keys() else 'IN'
            from_id = get_id(e_map[out_prop])
            to_id = get_id(e_map[in_prop])
            # Ensure that the default nodes includes with edge elementMaps do not overwrite nodes
            # with the same ID that have been explicitly inserted.
            if not self.graph.has_node(from_id):
                self.add_vertex(e_map[out_prop], path_index=index-1)
            if not self.graph.has_node(to_id):
                self.add_vertex(e_map[in_prop], path_index=index+1)
            self.add_path_edge(e_map, from_id, to_id)
        # Handle vertex elementMap
        else:
            # If a default node was created at the same index by an edge elementMap, overwrite it.
            if check_emap:
                self.insert_path_element(path_element, index)
            else:
                self.add_vertex(e_map, path_index=index)
