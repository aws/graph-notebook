"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import hashlib
import json
import uuid
from enum import Enum

from graph_notebook.network.EventfulNetwork import EventfulNetwork
from gremlin_python.process.traversal import T
from gremlin_python.structure.graph import Path, Vertex, Edge
from networkx import MultiDiGraph

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
    data_str = json.dumps(data, default=str)
    hashed = hashlib.md5(data_str.encode())
    generate_id = hashed.hexdigest()
    return f'graph_notebook-{generate_id}'


def get_id(element):
    """
    extract id from a given element for use in the GremlinNetwork
    """
    if isinstance(element, Vertex):
        return str(element.id)
    elif isinstance(element, Edge):
        return str(element.label)
    elif isinstance(element, dict):
        if T.id in element:
            return element[T.id]
        else:
            return generate_id_from_dict(element)
    else:
        return str(element)


class GremlinNetwork(EventfulNetwork):
    """
    GremlinNetwork extends the Network class and uses the add_results method to parse two specific types of responses

    1. A query which returns in the format of a path whose objects are in the order Vertex -> Edge -> Vertex.
    2. A query which returns a path as a valueMap. In this case, we will assume that the order is Vertex -> Edge -> Vertex.

    In the future, we will work to support other types of paths and/or results. For now, they are all out of scope.
    You can find more details on this in our design doc for visualization here: https://quip-amazon.com/R1jbA8eECdDd
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH):
        if graph is None:
            graph = MultiDiGraph()
        self.label_max_length = label_max_length
        super().__init__(graph, callbacks)

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

                    # the current pattern is V, inV, or outV
                    if path_pattern in V_PATTERNS:
                        # we cannot reconcile an edge type with a node
                        if type(path[path_index]) is Edge:
                            raise INVALID_VERTEX_PATH_PATTERN_ERROR

                        # add the vertex, no matter what patterns border a vertex pattern, it will always be added.
                        self.add_vertex(path[path_index])
                        # if the path index is over 0, we need to handle edges between this node and the previous one
                        if path_index > 0:
                            if path_pattern == PathPattern.V:
                                # two V patterns next to each other is an undirected, unlabeled edge
                                if previous_pattern == PathPattern.V:
                                    self.add_blank_edge(get_id(path[path_index - 1]),
                                                        get_id(path[path_index]),
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
                                    self.add_blank_edge(get_id(path[path_index - 1]), get_id(path[path_index]), undirected=False)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                            # path_pattern (OUT_V) -> previous_pattern (V, IN_V)
                            elif path_pattern == PathPattern.OUT_V and previous_pattern not in E_PATTERNS:
                                # draw an unlabeled, directed edge from current -> previous
                                # we can only process V and IN_V as no two adjacent vertices can both be outgoing.
                                if (previous_pattern == PathPattern.V or PathPattern.IN_V) and path_index > 0:
                                    self.add_blank_edge(get_id(path[path_index]), get_id(path[path_index - 1]), undirected=False)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                    elif path_pattern in E_PATTERNS:
                        # if the type of the given path element is not Edge,
                        # draw an undirected edge using this element for edge data
                        edge = path[path_index]
                        path_previous = get_id(path[path_index - 1])
                        path_next = get_id(path[path_index + 1])

                        if path_pattern == PathPattern.E:
                            # V -> V where the Vertex pattern is identical on either side of the edge
                            if next_pattern == previous_pattern:
                                # this is only valid if both are V, two connected vertices cannot have same direction
                                if next_pattern == PathPattern.V:
                                    self.add_path_edge(edge, path_previous, path_next, UNDIRECTED_EDGE)
                                else:
                                    raise SAME_DIRECTION_ADJACENT_VERTICES
                            # IN_V -> E -> V
                            elif previous_pattern == PathPattern.IN_V:
                                self.add_path_edge(edge, path_next, path_previous)
                            # OUT_V -> E -> V
                            elif previous_pattern == PathPattern.OUT_V:
                                self.add_path_edge(edge, path_previous, path_next)
                        # If the edge direction is specified, use it as the source of truth
                        elif path_pattern == PathPattern.IN_E:
                            self.add_path_edge(edge, from_id=path_next, to_id=path_previous)
                        elif path_pattern == PathPattern.OUT_E:
                            self.add_path_edge(edge, from_id=path_previous, to_id=path_next)
                    else:
                        raise INVALID_PATH_ERROR
                    path_index += 1

        return

    def add_results(self, results):
        """
        receives path results and traverses them to add nodes and edges to the network graph.
        We will look at sets of three in a path to form a vertex -> edge -> vertex pattern. All other
        patters will be considered invalid at this time.

        :param results: the data to be processed. Must be of type :type Path
        :return:
        """
        if not isinstance(results, list):
            raise ValueError("results must be a list of paths")

        for path in results:
            if not isinstance(path, Path):
                raise ValueError("all entries in results must be paths")

            if type(path[0]) is Edge or type(path[-1]) is Edge:
                raise INVALID_PATH_ERROR

            for i in range(len(path)):
                if i == 0:
                    self.add_vertex(path[i])
                    continue

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
                    continue
                else:
                    from_id = get_id(path[i - 1])

                self.add_vertex(path[i])
                if type(path[i - 1]) is not Edge:
                    self.add_blank_edge(from_id, get_id(path[i]))

    def add_vertex(self, v):
        """
        Adds a vertex to the network. If v is of :type Vertex, we will gather its id and label.
        If v comes from a valueMap, it will be a dict, with the keys T.label and T.ID being present in
        the dict for gathering the label and id, respectively.

        :param v: The vertex taken from a path traversal object.
        """
        node_id = ''
        if type(v) is Vertex:
            node_id = v.id
            title = v.label
            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
            data = {'label': label, 'title': title, 'properties': {'id': node_id, 'label': title}}
        elif type(v) is dict:
            properties = {}

            title = ''
            label = ''
            for k in v:
                if str(k) == T_LABEL:
                    title = str(v[k])
                    label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
                elif str(k) == T_ID:
                    node_id = str(v[k])
                properties[k] = v[k]

            # handle when there is no id in a node. In this case, we will generate one which
            # is consistently regenerated so that duplicate dicts will be dedubed to the same vertex.
            if node_id == '':
                node_id = f'{generate_id_from_dict(v)}'

            # similarly, if there is no label, we must generate one. This will be a concatenation
            # of all values in the dict
            if title == '':
                for key in v:
                    title += str(v[key])
                label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'

            data = {'properties': properties, 'label': label, 'title': title}
        else:
            node_id = str(v)
            title = str(v)
            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
            data = {'title': title, 'label': label}
        self.add_node(node_id, data)

    def add_path_edge(self, edge, from_id='', to_id='', data=None):
        if data is None:
            data = {}

        if type(edge) is Edge:
            from_id = from_id if from_id != '' else edge.outV.id
            to_id = to_id if to_id != '' else edge.inV.id
            data['properties'] = {'id': edge.id, 'label': edge.label, 'outV': str(edge.outV), 'inV': str(edge.inV)}
            self.add_edge(from_id, to_id, edge.id, edge.label, data)
        elif type(edge) is dict:
            properties = {}
            edge_id = ''
            edge_label = ''
            for k in edge:
                if str(k) == T_LABEL:
                    edge_label = str(edge[k])
                elif str(k) == T_ID:
                    edge_id = str(edge[k])

                properties[k] = edge[k]
            data['properties'] = properties
            self.add_edge(from_id, to_id, edge_id, edge_label, data)
        else:
            self.add_edge(from_id, to_id, edge, str(edge), data)

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
        self.add_edge(from_id, to_id, edge_id, label, edge_data)
