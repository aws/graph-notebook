"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import re
from networkx import MultiDiGraph
from rdflib.namespace import RDF, RDFS, OWL, XSD, SKOS, DOAP, FOAF, DC, DCTERMS, VOID

from graph_notebook.network.EventfulNetwork import EventfulNetwork, DEFAULT_GRP, DEFAULT_RAW_GRP_KEY

NAMESPACE_RDFS = str(RDFS.uri)
NAMESPACE_RDF = str(RDF.uri)
NAMESPACE_OWL = str(OWL)
NAMESPACE_XSD = str(XSD)
NAMESPACE_SKOS = str(SKOS)
NAMESPACE_DOAP = str(DOAP)
NAMESPACE_FOAF = str(FOAF)
NAMESPACE_DC = str(DC)
NAMESPACE_DCTERMS = str(DCTERMS)
NAMESPACE_VOID = str(VOID)

PREFIX_RDFS = 'rdfs'
PREFIX_RDF = 'rdf'
PREFIX_OWL = 'owl'
PREFIX_XSD = 'xsd'
PREFIX_SKOS = 'skos'
PREFIX_DOAP = 'doap'
PREFIX_FOAF = 'foaf'
PREFIX_DC = 'dc'
PREFIX_DCTERMS = 'dc-terms'
PREFIX_VOID = 'void'

RDFS_LABEL = f'{NAMESPACE_RDFS}label'
RDF_TYPE = f'{NAMESPACE_RDF}type'
NODE_TYPES = ['uri', 'bnode']
DEFAULT_LABEL_MAX_LENGTH = 10

InvalidBindingsCombinationError = ValueError('Bindings must be either "subject" "predicate" "object" or "s" "p" "o"')


class SPARQLNetwork(EventfulNetwork):
    """
    SPARQLNetwork extended Network and overrides how we add nodes to guarantee
    that all nodes will have their extracted qname and prefix attached to them.
    SPARQLNetwork also provides a helper method to add data from a SPARQL results whose
    resulting bindings contain 'subject', 'predicate', and 'object'
    """

    def __init__(self,
                 graph: MultiDiGraph = None,
                 callbacks: list = None,
                 label_max_length: int = DEFAULT_LABEL_MAX_LENGTH,
                 edge_label_max_length: int = DEFAULT_LABEL_MAX_LENGTH,
                 group_by_property='',
                 display_property='',
                 edge_display_property='',
                 tooltip_property='',
                 edge_tooltip_property='',
                 ignore_groups=False,
                 expand_all: bool = False,
                 group_by_raw=False):
        if graph is None:
            graph = MultiDiGraph()
        self.expand_all = expand_all

        super().__init__(graph, callbacks, label_max_length, edge_label_max_length, group_by_property,
                         display_property, edge_display_property, tooltip_property, edge_tooltip_property,
                         ignore_groups, group_by_raw)
        self.namespace_to_prefix = {  # http://foo/bar/ -> bar
            NAMESPACE_RDFS: PREFIX_RDFS,
            NAMESPACE_RDF: PREFIX_RDF,
            NAMESPACE_OWL: PREFIX_OWL,
            NAMESPACE_XSD: PREFIX_XSD,
            NAMESPACE_SKOS: PREFIX_SKOS,
            NAMESPACE_DOAP: PREFIX_DOAP,
            NAMESPACE_FOAF: PREFIX_FOAF,
            NAMESPACE_DC: PREFIX_DC,
            NAMESPACE_DCTERMS: PREFIX_DCTERMS,
            NAMESPACE_VOID: PREFIX_VOID

        }
        self.prefix_to_namespace = {  # bar -> http://foo/bar/
            PREFIX_RDFS: NAMESPACE_RDFS,
            PREFIX_RDF: NAMESPACE_RDF,
            PREFIX_OWL: NAMESPACE_OWL,
            PREFIX_XSD: NAMESPACE_XSD,
            PREFIX_SKOS: NAMESPACE_SKOS,
            PREFIX_DOAP: NAMESPACE_DOAP,
            PREFIX_FOAF: NAMESPACE_FOAF,
            PREFIX_DC: NAMESPACE_DC,
            PREFIX_DCTERMS: NAMESPACE_DCTERMS,
            PREFIX_VOID: NAMESPACE_VOID
        }

    def extract_prefix_declarations_from_query(self, query: str):
        for line in query.split('\n'):
            line = line.strip()
            if len(line) > 6:
                if line[:6].lower() == 'prefix':
                    words = line.split(' ')
                    shorthand = words[1][:words[1].find(':')]
                    namespace = words[-1][1:len(words[-1]) - 1].strip()
                    self.namespace_to_prefix[namespace] = shorthand
                    self.prefix_to_namespace[shorthand] = namespace

    def generate_node_label_title(self, node_id: str, data: dict):
        prefix = self.extract_prefix(node_id)
        value = self.extract_value(node_id)

        if prefix is not None:
            title = f'{prefix}:{value}'
            data['prefix'] = prefix
        else:
            title = node_id

        label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
        data['label'] = label
        if 'title' not in data:
            data['title'] = title
        return data

    def get_node_property_value(self, binding: dict, custom_property, data: dict = None):
        if data is None:
            data = {}
            node_type = None
        else:
            node_type = self.get_node_class(data)
        if isinstance(custom_property, dict):
            if node_type:
                try:
                    if node_type in custom_property:
                        property_for_type = custom_property[node_type]
                        if property_for_type[:2] == "P." and 'properties' in data:
                            prop_value = self.retrieve_object_property_value(property_for_type[2:], data['properties'])
                        else:
                            prop_value = binding[property_for_type]
                    else:
                        prop_value = None
                except KeyError:
                    prop_value = None
            else:
                prop_value = None
        elif custom_property[:2] == "P." and 'properties' in data:
            prop_value = self.retrieve_object_property_value(custom_property[2:], data['properties'])
        elif custom_property in binding:
            prop_value = binding[custom_property]
        else:
            prop_value = None

        return prop_value

    def get_edge_property_value(self, binding: dict, custom_property):
        # use binding["type"] as class identifier, as RDF does not support literal edge properties.
        if isinstance(custom_property, dict):
            try:
                if str(binding["type"]) in custom_property:
                    label = binding[custom_property[binding["type"]]]
                else:
                    label = None
            except KeyError:
                label = None
        elif custom_property in binding:
            label = binding[custom_property]
        else:
            label = None

        return label

    def retrieve_object_property_value(self, obj_property, data_properties):
        if obj_property in data_properties:
            prop_value = str(data_properties[obj_property])
        else:
            prop_value = None
        return prop_value

    def get_node_class(self, data: dict = None):
        # use rdf:type (or similar type property) as class identifier.
        try:
            data_props = data["properties"]
            type_regex = re.compile('.*:type$')
            node_type = None
            for prop, value in data_props.items():
                if type_regex.match(prop):
                    node_type = value
                    break
        except KeyError:
            node_type = None
        return node_type

    def parse_node(self, node_id: str, node_binding: dict = None, data: dict = None):
        """
        overriding parent add_node class to automatically parse the uri for a node
        and add data to the node for prefix and shortened name
        :param node_id: the full uri
        :param node_binding: the subject or object binding, in dict form
        :param data: dict to set node initial node properties
        """
        if data is None:
            data = {}
        if self.display_property:
            label = self.get_node_property_value(node_binding, self.display_property, data=data)
            if label:
                title, label = self.strip_and_truncate_label_and_title(label, self.label_max_length)
                data['label'] = label
                data['title'] = title
        if self.tooltip_property and self.tooltip_property != self.display_property:
            tooltip_raw = self.get_node_property_value(node_binding, self.tooltip_property, data=data)
            if tooltip_raw:
                title, label_plc = self.strip_and_truncate_label_and_title(tooltip_raw)
                data['title'] = title
        if 'label' not in data:
            data = self.generate_node_label_title(node_id=node_id, data=data)
        if self.ignore_groups or not node_binding:
            node_group = DEFAULT_GRP
        elif str(self.group_by_property) == DEFAULT_RAW_GRP_KEY:
            node_group = str(node_binding)
        else:
            node_group = None
            node_type = self.get_node_class(data)
            if isinstance(self.group_by_property, dict):
                # if rdf:type or similar node class identifier does not exist on the node, set group to the default.
                if node_type:
                    try:
                        if node_type in self.group_by_property:
                            group_by_for_type = self.group_by_property[node_type]
                            if group_by_for_type == DEFAULT_RAW_GRP_KEY:
                                node_group = str(node_binding)
                            elif group_by_for_type[:2] == "P." and 'properties' in data:
                                node_group = self.retrieve_object_property_value(group_by_for_type[2:],
                                                                                 data['properties'])
                            else:
                                node_group = node_binding[group_by_for_type]
                        else:
                            node_group = node_type
                    except KeyError:
                        node_group = node_type
                else:
                    node_group = DEFAULT_GRP
            elif self.group_by_property[:2] == "P." and 'properties' in data:
                node_group = self.retrieve_object_property_value(self.group_by_property[2:],
                                                                 data['properties'])
            elif self.group_by_property in node_binding:
                node_group = node_binding[self.group_by_property]

            if not node_group:
                if node_type:
                    node_group = node_type
                else:
                    node_group = DEFAULT_GRP
        data['group'] = str(node_group)

        self.add_node(node_id=node_id, data=data)

    @staticmethod
    def extract_value(uri: str) -> str:
        """
        extracts the value from a given uri
        :param uri: the full uri whose value should be extracted. Such as http://kelvinlawrence.net/air-routes/resource/24
        :return: the value of the uri. Such as '24'
        """

        hash_index = uri.find('#')
        if hash_index != -1:
            return uri[hash_index + 1:]

        last_slash_index = uri.rfind('/')
        if last_slash_index != -1:
            return uri[last_slash_index + 1:]

        return uri

    def extract_prefix(self, uri: str) -> str:
        """
        extracts the prefix and stores the namespace of a given uri to shorten the text
        used for displaying to the user

        :param uri: the full uri value. such as http://kelvinlawrence.net/air-routes/resource/24
        :return: the prefix of the uri, such as 'resource'
        """
        if not (uri.startswith('http://') or uri.startswith('https://')):
            return None

        hash_index = uri.find('#')
        last_slash_index = uri.rfind('/', 0, hash_index)
        if hash_index != -1:  # for example: http://www.w3.org/1999/02/22-rdf-syntax-ns#type
            namespace = uri[:hash_index + 1]
            prefix = uri[last_slash_index + 1:hash_index]
        else:
            second_last_slash_index = uri.rindex('/', 0, last_slash_index)
            namespace = uri[:last_slash_index + 1]
            prefix = uri[second_last_slash_index + 1:last_slash_index]

        if namespace in self.namespace_to_prefix:
            return self.namespace_to_prefix[namespace]
        else:
            if prefix in self.prefix_to_namespace:
                # this prefix is already reserved, we need to generate a new one.
                # look at the previous section and attempt to append it to the prefix
                num = 2
                while True:
                    generated_prefix = f'{prefix}-{num}'
                    if generated_prefix not in self.prefix_to_namespace:
                        prefix = generated_prefix
                        break
                    else:
                        num += 1

            self.namespace_to_prefix[namespace] = prefix
            self.prefix_to_namespace[prefix] = namespace
            return prefix

    def add_results(self, results):
        """
        takes a json result from a sparql query and attempts to add all bindings
        with the variables "subject" ,"predicate", "object" or "s", "p", "o"
        :param results:
        """

        # validate that we can process this result..
        vars = []
        if 'head' in results and 'vars' in results['head']:
            vars = results['head']['vars']

        if len(vars) < 3:  # if we have less than three vars in the result, then we cannot have the three we require.
            return

        found_subject = False
        found_predicate = False
        found_object = False

        subject_binding = "subject"
        predicate_binding = "predicate"
        object_binding = "object"

        for v in vars:
            if v == 'subject' and not found_subject:
                subject_binding = 'subject'
                found_subject = True
                continue
            if v == 'predicate' and not found_predicate:
                predicate_binding = "predicate"
                found_predicate = True
                continue
            if v == 'object' and not found_object:
                object_binding = "object"
                found_object = True
                continue
            if v == 's' and not found_subject:
                subject_binding = 's'
                found_subject = True
                continue
            if v == 'p' and not found_predicate:
                predicate_binding = 'p'
                found_predicate = True
                continue
            if v == 'o' and not found_object:
                object_binding = 'o'
                found_object = True
                continue

        if subject_binding == 's' and predicate_binding == 'p' and object_binding == 'o':
            use_spo = True
        elif subject_binding == 'subject' and predicate_binding == 'predicate' and object_binding == 'object':
            use_spo = False
        else:
            raise InvalidBindingsCombinationError

        if not (found_subject and found_predicate and found_object):
            return

        bindings = []
        if 'results' in results and 'bindings' in results['results']:
            bindings = results['results']['bindings']

        # sort the bindings so we can process all triples that make up a given node (subject)
        # this will reduce the number of message callbacks generated as we process larger
        # result sets.
        bindings.sort(key=lambda x: x[subject_binding]['value'])

        if len(bindings) < 1:
            return

        current_subject_binding = bindings[0][subject_binding]
        data = {'properties': {}}
        edge_bindings = []

        for b in bindings:
            # just because the result vars show the needed variables doesn't mean that bindings will have them.
            if subject_binding not in b or predicate_binding not in b or object_binding not in b:
                if subject_binding in b:
                    self.parse_node(node_binding=b[subject_binding], node_id=b[subject_binding]['value'])

                if object_binding in b:
                    self.parse_node(node_binding=b[object_binding], node_id=b[object_binding]['value'])
                continue
            sub = b[subject_binding]
            pred = b[predicate_binding]
            obj = b[object_binding]

            if sub['value'] != current_subject_binding['value']:
                self.parse_node(node_binding=current_subject_binding,
                                node_id=current_subject_binding['value'],
                                data=data)
                data = {'properties': {}}
                current_subject_binding = sub

            # if obj is of type uri, and the predicate value is neither rdfs:label nor rdf:type this binding is an edge.
            if (obj['type'] in NODE_TYPES or self.expand_all) and pred['value'] not in [RDFS_LABEL, RDF_TYPE]:
                edge_bindings.append(b)
                continue

            if pred['type'] == 'uri':
                prefix = self.extract_prefix(pred['value'])
                value = self.extract_value(pred['value'])

                obj_entry = obj['value']
                if obj['type'] == 'uri':
                    obj_prefix = self.extract_prefix(obj['value'])
                    obj_value = self.extract_value(obj['value'])
                    obj_entry = f'{obj_prefix}:{obj_value}'

                # default label/tooltip set here. May be overwritten by custom properties.
                if pred['value'] == RDFS_LABEL:
                    title = obj_entry
                    label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
                    data['title'] = title
                    data['label'] = label

                # object is a literal. Check if data has this predicate already. If it does, turn its value into an
                # array and append the new value to it.
                if 'properties' in data and f'{prefix}:{value}' in data['properties']:
                    if type(data['properties'][f'{prefix}:{value}']) is list:
                        data['properties'][f'{prefix}:{value}'].append(obj_entry)
                    else:
                        data['properties'][f'{prefix}:{value}'] = [data['properties'][f'{prefix}:{value}'], obj_entry]
                else:
                    data['properties'][f'{prefix}:{value}'] = obj_entry
            else:
                # Check if data has this predicate already. If it does, turn its value into an
                # array and append the new value to it.
                if 'properties' in data and pred['value'] in data['properties']:
                    if type(data['properties'][pred['value']]) is list:
                        data['properties'][pred['value']].append(obj['value'])
                    else:
                        data['properties'][pred['value']] = [data['properties'][pred['value']], obj['value']]
                else:
                    data['properties'][pred['value']] = obj['value']

        # add the last node and all our edges
        self.parse_node(node_binding=current_subject_binding,
                        node_id=current_subject_binding['value'],
                        data=data)
        self.process_edge_bindings(edge_bindings, use_spo)
        return

    def process_edge_bindings(self, bindings, use_spo=False):
        subject_binding = 'subject'
        predicate_binding = 'predicate'
        object_binding = 'object'

        if use_spo:
            subject_binding = 's'
            predicate_binding = 'p'
            object_binding = 'o'

        for b in bindings:
            if subject_binding not in b or predicate_binding not in b or object_binding not in b:
                continue

            pred = b[predicate_binding]

            edge_label = self.get_edge_property_value(pred, self.edge_display_property)

            if not edge_label:
                if pred['type'] == 'uri':
                    prefix = self.extract_prefix(pred['value'])
                    value = self.extract_value(pred['value'])
                    edge_label = f'{prefix}:{value}'
                else:
                    edge_label = pred['value']

            # Draw node at other end of the edge, if it doesn't exist yet
            if not self.graph.has_node(b[object_binding]['value']):
                self.parse_node(node_binding=b[object_binding],
                                node_id=b[object_binding]['value'])
            edge_title, edge_label = self.strip_and_truncate_label_and_title(edge_label, self.edge_label_max_length)
            if self.edge_tooltip_property and self.edge_tooltip_property != self.edge_display_property:
                tooltip_raw = self.get_edge_property_value(pred, self.edge_tooltip_property)
                if tooltip_raw:
                    edge_title, label_plc = self.strip_and_truncate_label_and_title(tooltip_raw)
            data = {'title': edge_title}
            self.add_edge(from_id=b[subject_binding]['value'], to_id=b[object_binding]['value'], edge_id=pred['value'],
                          label=edge_label, title=edge_title, data=data)
