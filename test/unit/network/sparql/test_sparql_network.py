"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.network.EventfulNetwork import EVENT_ADD_NODE
from graph_notebook.network.sparql.SPARQLNetwork import SPARQLNetwork, InvalidBindingsCombinationError
from test.unit.network.sparql.data.get_sparql_result import get_sparql_result


def create_network_from_dataset(dataset: str, expand_all: bool = False) -> SPARQLNetwork:
    data = get_sparql_result(dataset)
    sparql_network = SPARQLNetwork(expand_all=expand_all)
    sparql_network.add_results(data)
    return sparql_network


class TestSPARQLNetwork(unittest.TestCase):
    def test_add_sparql_result(self):
        sparql_network = create_network_from_dataset("001_kelvin-airroutes.json")
        from_id = 'http://kelvinlawrence.net/air-routes/resource/24'
        resource = sparql_network.graph.nodes.get(from_id)
        expected_label = 'SJC'
        self.assertEqual(expected_label, resource['label'])

        expected_rdfs_label = 'SJC'
        actual_node_label = sparql_network.graph.nodes[from_id]['properties']['rdfs:label']
        self.assertEqual(expected_rdfs_label, actual_node_label)

        desc_property_key = 'datatypeProperty:desc'
        actual_desc_value = sparql_network.graph.nodes[from_id]['properties'][desc_property_key]
        expected_desc_property_value = 'Norman Y. Mineta San Jose International Airport'
        self.assertEqual(expected_desc_property_value, actual_desc_value)

    def test_add_sparql_result_with_bnode(self):
        sparql_network = create_network_from_dataset("000_bnode.json")
        expected_label = 'Marcia Lassila'
        bnode_id = 'b255789583'
        actual_label = sparql_network.graph.nodes[bnode_id]['label']
        self.assertEqual(f'{expected_label[:sparql_network.label_max_length - 3]}...', actual_label)

        expected_properties = {
            'rdfs:label': expected_label,
            'rdf:type': 'example:Person'
        }
        actual_properties = sparql_network.graph.nodes[bnode_id]['properties']
        self.assertEqual(expected_properties, actual_properties)

    def test_extract_prefix(self):
        sparql_network = SPARQLNetwork()
        uri_to_prefix = {
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#type': 'rdf',
            'http://kelvinlawrence.net/air-routes/class/Airport': 'class',
            'http://kelvinlawrence.net/air-routes/resource/24': 'resource',
            'http://www.w3.org/2000/01/rdf-schema#': 'rdfs'
        }
        for k in uri_to_prefix:
            prefix = sparql_network.extract_prefix(k)
            self.assertEqual(uri_to_prefix[k], prefix)

    def test_extract_value(self):
        sparql_network = SPARQLNetwork()
        uri_to_value = {
            'http://www.w3.org/1999/02/22-rdf-syntax-ns#type': 'type',
            'http://kelvinlawrence.net/air-routes/class/Airport': 'Airport',
            'http://kelvinlawrence.net/air-routes/resource/24': '24',
            'http://example.org/index.html#section2': 'section2',
            # this is invalid uri syntax but Neptune allows it.
            'http://example.org/index.html#section2#point1': 'section2#point1',
            'http://example.org/index.html#/user/orders/1': '/user/orders/1'
        }

        for k in uri_to_value:
            value = sparql_network.extract_value(k)
            self.assertEqual(uri_to_value[k], value)

    def test_extract_conflicting_prefix(self):
        sparql_network = SPARQLNetwork()
        uri_to_prefix = {
            'http://kelvinlawrence.net/air-routes/resource/24': 'resource',
            'http://kelvinlawrence.net/class/resource/24': 'resource-2',
            'http://example/resource/24': 'resource-3',
            'http://example.org/index.html#section2': 'index.html',
            # this is invalid uri syntax but Neptune allows it.
            'http://example.org/index.html#section2#point1': 'index.html',
            'http://example.org/index.html#/user/orders/1': 'index.html'
        }
        for k in uri_to_prefix:
            prefix = sparql_network.extract_prefix(k)
            self.assertEqual(uri_to_prefix[k], prefix)

    def test_sparql_network_event_callback(self):
        callback_reached = {}
        node_id = 'http://kelvinlawrence.net/air-routes/resource/24'

        def add_node_callback(network, event_name, data):
            expected_data = {
                'data': {
                    'group': 'DEFAULT_GROUP',
                    'label': 'resourc...',
                    'prefix': 'resource',
                    'title': 'resource:24'
                },
                'node_id': 'http://kelvinlawrence.net/air-routes/resource/24'
            }
            self.assertEqual(expected_data, data)
            node = network.graph.nodes.get(node_id)
            self.assertIsNotNone(node)
            self.assertEqual(expected_data['data'], node)
            callback_reached[event_name] = True

        callbacks = {EVENT_ADD_NODE: [add_node_callback]}
        sn = SPARQLNetwork(callbacks=callbacks)
        sn.parse_node(node_id=node_id)
        self.assertTrue(callback_reached[EVENT_ADD_NODE])

    def test_sparql_network_truncated_labels(self):
        sparql_network = create_network_from_dataset("004_soccer_teams.json")
        subject = 'http://www.example.com/soccer/resource#Brighton'

        node = sparql_network.graph.nodes.get(subject)
        self.assertEqual(node['label'], node['properties']['rdfs:label'][:sparql_network.label_max_length - 3] + '...')

    def test_sparql_network_invalid_bindings(self):
        with self.assertRaises(ValueError) as context:
            create_network_from_dataset("005_incorrect_bindings.json")

        self.assertEqual(context.exception, InvalidBindingsCombinationError)

    def test_sparql_network_spo_bindings(self):
        sparql_network = create_network_from_dataset("006_spo_bindings.json")
        subject = "http://lassila.org/example/Person"
        node = sparql_network.graph.nodes.get(subject)
        self.assertEqual(node['label'], 'Person')

    def test_sparql_network_subject_literal_bindings(self):
        sparql_network = create_network_from_dataset("007_literal_subject_bindings.json", expand_all=True)
        node = sparql_network.graph.nodes.get('CZM')
        self.assertEqual('CZM', node['label'])
        self.assertEqual(12, len(sparql_network.graph.nodes))
        edge = sparql_network.graph.edges['CZM', 'IAH', 'route']
        self.assertIsNotNone(edge)
        self.assertEqual(11, len(sparql_network.graph.edges))

    def test_sparql_network_extract_prefixes_from_query(self):
        sparql_network = SPARQLNetwork()
        query = """
        PREFIX rdf:   <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        PREFIX rdfs:  <http://www.w3.org/2000/01/rdf-schema#>
        PREFIX res:   <http://kelvinlawrence.net/air-routes/resource/>
        PREFIX prop:  <http://kelvinlawrence.net/air-routes/datatypeProperty/>
        PREFIX op:    <http://kelvinlawrence.net/air-routes/objectProperty/>
        PREFIX class: <http://kelvinlawrence.net/air-routes/class/>

        SELECT ?s ?p ?o 
        WHERE {
            ?s ?p ?o . 
            ?s prop:code "CZM" .
            ?s op:route ?o
        } 
        LIMIT 50
        """
        sparql_network.extract_prefix_declarations_from_query(query)
        self.assertEqual(sparql_network.prefix_to_namespace['prop'],
                         'http://kelvinlawrence.net/air-routes/datatypeProperty/')
        self.assertEqual(sparql_network.namespace_to_prefix['http://kelvinlawrence.net/air-routes/datatypeProperty/'],
                         'prop')

        # now load some bindings which use these prefixes and verify they are used over the extracted ones.
        data = get_sparql_result('001_kelvin-airroutes.json')
        sparql_network.add_results(data)
        icao = sparql_network.graph.nodes['http://kelvinlawrence.net/air-routes/resource/24']['properties']['prop:icao']
        self.assertEqual(icao, 'KSJC')

    def test_sparql_network_multiple_s_and_p_bindings(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual(['value1', 'value2'], node['properties']['example:prop'])
        self.assertEqual(['value3', 'value4'], node['properties']['propLiteral'])

    def test_sparql_network_label_length_full(self):
        sparql_network = SPARQLNetwork(label_max_length=20)
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['label'])
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_label_length_truncated(self):
        sparql_network = SPARQLNetwork(label_max_length=5)
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('re...', node['label'])
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_edge_label_full(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property="value")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['label'])
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['title'])

    def test_sparql_network_edge_label_truncated(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=10, edge_display_property="value")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://...', edge['label'])
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['title'])

    def test_sparql_network_group_default(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('ontology:Team', node['group'])

    def test_sparql_network_group_default_no_type(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/365')
        self.assertEqual('DEFAULT_GROUP', node['group'])

    def test_sparql_network_group_default_multiple_types(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/400')
        self.assertEqual("['ontology:airport', 'ontology:regional']", node['group'])

    def test_sparql_network_group_default_no_properties(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/85')
        self.assertEqual('DEFAULT_GROUP', node['group'])

    def test_sparql_network_group_nested_properties_string(self):
        sparql_network = SPARQLNetwork(group_by_property='P.ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['group'])

    def test_sparql_network_group_nested_properties_string_multiproperty(self):
        sparql_network = SPARQLNetwork(group_by_property='P.rdf:type')
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/400')
        self.assertEqual("['ontology:airport', 'ontology:regional']", node['group'])

    def test_sparql_network_group_nested_properties_string_invalid_prop(self):
        sparql_network = SPARQLNetwork(group_by_property='P.ontology:wins')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('ontology:Team', node['group'])

    def test_sparql_network_group_nested_properties_string_invalid_format(self):
        sparql_network = SPARQLNetwork(group_by_property='ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('ontology:Team', node['group'])

    def test_sparql_network_group_nested_properties_string_no_properties(self):
        sparql_network = SPARQLNetwork(group_by_property='P.destinations')
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/85')
        self.assertEqual('DEFAULT_GROUP', node['group'])

    def test_sparql_network_group_nested_properties_string_use_binding(self):
        sparql_network = SPARQLNetwork(group_by_property='type')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('uri', node['group'])

    def test_sparql_network_group_nested_properties_string_shared_property(self):
        sparql_network = SPARQLNetwork(group_by_property='P.rdf:type')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('ontology:Team', node['group'])

    def test_sparql_network_group_nested_properties_string_use_binding_shared_property(self):
        sparql_network = SPARQLNetwork(group_by_property='type')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('uri', node['group'])

    def test_sparql_network_group_string(self):
        sparql_network = SPARQLNetwork(group_by_property='value')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('http://kelvinlawrence.net/air-routes/resource/24', node['group'])

    def test_sparql_network_group_string_invalid(self):
        sparql_network = SPARQLNetwork(group_by_property='foo')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('class:Airport', node['group'])

    def test_sparql_network_group_by_raw_string(self):
        sparql_network = SPARQLNetwork(group_by_raw='__RAW_RESULT__')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual("{'type': 'uri', 'value': 'http://kelvinlawrence.net/air-routes/resource/24'}", node['group'])

    def test_sparql_network_group_map(self):
        sparql_network = SPARQLNetwork(group_by_property='{"class:Airport":"type"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual("uri", node['group'])

    def test_sparql_network_group_map_invalid_key(self):
        sparql_network = SPARQLNetwork(group_by_property='{"foo":"value"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('class:Airport', node['group'])

    def test_sparql_network_group_map_invalid_value(self):
        sparql_network = SPARQLNetwork(group_by_property='{"uri":"bar"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('class:Airport', node['group'])

    def test_sparql_network_group_map_invalid_json(self):
        sparql_network = SPARQLNetwork(group_by_property='{"uri":bar"')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('class:Airport', node['group'])

    def test_sparql_network_group_nested_properties_map(self):
        sparql_network = SPARQLNetwork(group_by_property='{"ontology:Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['group'])

    def test_sparql_network_group_nested_properties_map_invalid_key_format(self):
        sparql_network = SPARQLNetwork(group_by_property='{"Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("ontology:Team", node['group'])

    def test_sparql_network_group_nested_properties_map_invalid_value_format(self):
        sparql_network = SPARQLNetwork(group_by_property='{"ontology:Team":"ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("ontology:Team", node['group'])

    def test_sparql_network_group_nested_properties_map_use_binding(self):
        sparql_network = SPARQLNetwork(group_by_property='{"ontology:Team":"type"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("uri", node['group'])

    def test_sparql_network_group_nested_properties_map_multiple(self):
        sparql_network = SPARQLNetwork(group_by_property='{"ontology:Team":"type", '
                                                         '"ontology:Stadium": "P.ontology:opened"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node1 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        node2 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Vitality_Stadium')
        self.assertEqual("uri", node1['group'])
        self.assertEqual("1910", node2['group'])

    def test_sparql_network_group_by_raw_json(self):
        sparql_network = SPARQLNetwork(group_by_raw='{"uri":"__RAW_RESULT__"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual("{'type': 'uri', 'value': 'http://kelvinlawrence.net/air-routes/resource/24'}", node['group'])

    def test_sparql_network_group_by_raw_explicit(self):
        sparql_network = SPARQLNetwork(group_by_raw=True)
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual("{'type': 'uri', 'value': 'http://kelvinlawrence.net/air-routes/resource/24'}", node['group'])

    def test_sparql_network_group_by_raw_explicit_overrule_gbp(self):
        sparql_network = SPARQLNetwork(group_by_raw=True, group_by_property='value')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual("{'type': 'uri', 'value': 'http://kelvinlawrence.net/air-routes/resource/24'}", node['group'])

    def test_sparql_network_ignore_groups(self):
        sparql_network = SPARQLNetwork(group_by_property='{"uri":"value"}', ignore_groups=True)
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('DEFAULT_GROUP', node['group'])

    def test_sparql_network_node_label_default(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcast...', node['label'])

    def test_sparql_network_node_label_string(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='value')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('http://kelvinlawrence.net/air-routes/resource/24', node['label'])

    def test_sparql_network_node_label_string_invalid(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='foo')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['label'])

    def test_sparql_network_node_label_nested_properties_string(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='P.ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['label'])

    def test_sparql_network_node_label_nested_properties_string_invalid_prop(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='P.ontology:wins')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcastle United', node['label'])

    def test_sparql_network_node_label_nested_properties_string_invalid_format(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcastle United', node['label'])

    def test_sparql_network_node_label_nested_properties_string_no_properties(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='P.destinations')
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/85')
        self.assertEqual('resource:85', node['label'])

    def test_sparql_network_node_label_nested_properties_string_use_binding(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='type')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('uri', node['label'])

    def test_sparql_network_node_label_map(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"class:Airport":"value"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('http://kelvinlawrence.net/air-routes/resource/24', node['label'])

    def test_sparql_network_node_label_map_invalid_key(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"Airport":"value"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['label'])

    def test_sparql_network_node_label_map_invalid_value(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"class:Airport":"foo"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['label'])

    def test_sparql_network_node_label_map_invalid_json(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"uri:"foo')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['label'])

    def test_sparql_network_node_label_nested_properties_map(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"ontology:Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['label'])

    def test_sparql_network_node_label_nested_properties_map_invalid_key_format(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("Newcastle United", node['label'])

    def test_sparql_network_node_label_nested_properties_map_invalid_value_format(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"ontology:Team":"ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("Newcastle United", node['label'])

    def test_sparql_network_node_label_nested_properties_map_use_binding(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='{"ontology:Team":"type"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("uri", node['label'])

    def test_sparql_network_node_label_nested_properties_map_multiple(self):
        sparql_network = SPARQLNetwork(label_max_length=100,
                                       display_property='{"ontology:Team":"type", '
                                                        '"ontology:Stadium": "P.ontology:opened"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node1 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        node2 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Vitality_Stadium')
        self.assertEqual("uri", node1['label'])
        self.assertEqual("1910", node2['label'])

    def test_sparql_network_node_tooltip_default(self):
        sparql_network = SPARQLNetwork(label_max_length=100)
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcastle United', node['label'])

    def test_sparql_network_node_tooltip_string(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='type')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('uri', node['title'])

    def test_sparql_network_node_tooltip_string_invalid(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='foo')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_node_tooltip_nested_properties_string(self):
        sparql_network = SPARQLNetwork(tooltip_property='P.ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['title'])

    def test_sparql_network_node_tooltip_nested_properties_string_invalid_prop(self):
        sparql_network = SPARQLNetwork(tooltip_property='P.ontology:wins')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcastle United', node['title'])

    def test_sparql_network_node_tooltip_nested_properties_string_invalid_format(self):
        sparql_network = SPARQLNetwork(tooltip_property='ontology:founded')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('Newcastle United', node['title'])

    def test_sparql_network_node_tooltip_nested_properties_string_no_properties(self):
        sparql_network = SPARQLNetwork(tooltip_property='P.destinations')
        data = get_sparql_result('010_airroutes_no_literals.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/85')
        self.assertEqual('resource:85', node['title'])

    def test_sparql_network_node_tooltip_nested_properties_string_use_binding(self):
        sparql_network = SPARQLNetwork(tooltip_property='type')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual('uri', node['title'])

    def test_sparql_network_node_tooltip_map(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='{"class:Airport":"type"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('uri', node['title'])

    def test_sparql_network_node_tooltip_map_invalid_key(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='{"Airport":"type"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_node_tooltip_map_invalid_value(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='{"class:Airport":"bar"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_node_tooltip_map_invalid_json(self):
        sparql_network = SPARQLNetwork(label_max_length=100, tooltip_property='{"class:Airport"type"}')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('resource:24', node['title'])

    def test_sparql_network_node_tooltip_nested_properties_map(self):
        sparql_network = SPARQLNetwork(tooltip_property='{"ontology:Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("1892", node['title'])

    def test_sparql_network_node_tooltip_nested_properties_map_invalid_key_format(self):
        sparql_network = SPARQLNetwork(tooltip_property='{"Team":"P.ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("Newcastle United", node['title'])

    def test_sparql_network_node_tooltip_nested_properties_map_invalid_value_format(self):
        sparql_network = SPARQLNetwork(tooltip_property='{"ontology:Team":"ontology:founded"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("Newcastle United", node['title'])

    def test_sparql_network_node_tooltip_nested_properties_map_use_binding(self):
        sparql_network = SPARQLNetwork(tooltip_property='{"ontology:Team":"type"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        self.assertEqual("uri", node['title'])

    def test_sparql_network_node_tooltip_nested_properties_map_multiple(self):
        sparql_network = SPARQLNetwork(tooltip_property='{"ontology:Team":"type", '
                                                        '"ontology:Stadium": "P.ontology:opened"}')
        data = get_sparql_result('004_soccer_teams.json')
        sparql_network.add_results(data)
        node1 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Newcastle_United')
        node2 = sparql_network.graph.nodes.get('http://www.example.com/soccer/resource#Vitality_Stadium')
        self.assertEqual("uri", node1['title'])
        self.assertEqual("1910", node2['title'])

    def test_sparql_network_node_different_label_and_tooltip(self):
        sparql_network = SPARQLNetwork(label_max_length=100, display_property='value', tooltip_property='type')
        data = get_sparql_result('008_duplicate_s_and_p_bindings.json')
        sparql_network.add_results(data)
        node = sparql_network.graph.nodes.get('http://kelvinlawrence.net/air-routes/resource/24')
        self.assertEqual('http://kelvinlawrence.net/air-routes/resource/24', node['label'])
        self.assertEqual('uri', node['title'])

    def test_sparql_network_edge_label_default(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100)
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['label'])

    def test_sparql_network_edge_label_string(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property="value")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['label'])

    def test_sparql_network_edge_label_string_invalid(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property="foo")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['label'])

    def test_sparql_network_edge_label_map(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property='{"uri":"value"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['label'])

    def test_sparql_network_edge_label_map_invalid_key(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property='{"foo":"value"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['label'])

    def test_sparql_network_edge_label_map_invalid_value(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property='{"uri":"foo"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['label'])

    def test_sparql_network_edge_label_map_invalid_json(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property='{"uri":"foo')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['label'])

    def test_sparql_network_edge_tooltip_default(self):
        sparql_network = SPARQLNetwork()
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['title'])

    def test_sparql_network_edge_tooltip_default_with_custom_label(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_display_property="value")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['label'])
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['title'])

    def test_sparql_network_edge_tooltip_string(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property="value")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['title'])

    def test_sparql_network_edge_tooltip_string_invalid(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property="foo")
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['title'])

    def test_sparql_network_edge_tooltip_map(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property='{"uri":"value"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['title'])

    def test_sparql_network_edge_tooltip_map_invalid_key(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property='{"foo":"value"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['title'])

    def test_sparql_network_edge_tooltip_map_invalid_value(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property='{"uri":"bar"}')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['title'])

    def test_sparql_network_edge_tooltip_map_invalid_json(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100, edge_tooltip_property='{"uri":"value')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('objectProperty:route', edge['title'])

    def test_sparql_network_edge_different_label_and_tooltip(self):
        sparql_network = SPARQLNetwork(edge_label_max_length=100,
                                       edge_display_property='value',
                                       edge_tooltip_property='type')
        data = get_sparql_result('009_airroutes_edge_test.json')
        sparql_network.add_results(data)
        edge = sparql_network.graph.get_edge_data('http://kelvinlawrence.net/air-routes/resource/365',
                                                  'http://kelvinlawrence.net/air-routes/resource/31',
                                                  'http://kelvinlawrence.net/air-routes/objectProperty/route')
        self.assertEqual('http://kelvinlawrence.net/air-routes/objectProperty/route', edge['label'])
        self.assertEqual('uri', edge['title'])


if __name__ == '__main__':
    unittest.main()
