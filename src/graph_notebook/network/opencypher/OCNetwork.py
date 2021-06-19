"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import hashlib
import json
import uuid
import logging
from enum import Enum
import collections

from graph_notebook.network.EventfulNetwork import EventfulNetwork
from networkx import MultiDiGraph

logging.basicConfig()
logger = logging.getLogger("graph_magic")

LABEL = '~label'
ID = '~id'

DEFAULT_LABEL_MAX_LENGTH = 10
TO_DISABLED = {"to": {"enabled": False}}
UNDIRECTED_EDGE = {
    "arrows": TO_DISABLED
}

ENTITY_KEY="~entityType"
ID_KEY="~id"
START_KEY="~start"
END_KEY="~end"
PROPERTIES_KEY="~properties"
TYPE_KEY="~type"
LABEL_KEY="~labels"
NODE_ENTITY_TYPE='node'
REL_ENTITY_TYPE='relationship'

node_ids=[]
nodes=[]
rels=[]

class OCNetwork(EventfulNetwork):
    """
    OCNetwork extends the Network class and uses the add_results method to parse responses
    """

    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH,
                 group_by_property=LABEL, ignore_groups=False):
        if graph is None:
            graph = MultiDiGraph()
        self.label_max_length = label_max_length
        try:
            self.group_by_property = json.loads(group_by_property)
        except ValueError:
            self.group_by_property = group_by_property
        self.ignore_groups = ignore_groups
        super().__init__(graph, callbacks)
    
    def flatten(self, d, parent_key='', sep='_'):
        items = []
        for k, v in d.items():
            new_key = parent_key + sep + k if parent_key else k
            if isinstance(v, collections.MutableMapping):
                items.extend(self.flatten(v, new_key, sep=sep).items())
            else:
                items.append((new_key, v))
        return dict(items)

    def parse_node(self, node):
        node_ids.append(node[ID_KEY])
        data = node

        if LABEL_KEY in node.keys():
            title = node[LABEL_KEY][0]
        else:
            for key in node:
                title += str(node[key])
            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
            
        label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
        if not isinstance(self.group_by_property, dict):  # Handle string format group_by
            if self.group_by_property in [LABEL_KEY, 'label']:  # this handles if it's just a string
                group = node[LABEL_KEY][0]
            elif self.group_by_property == [ID_KEY, 'id']:
                group = node[ID_KEY]
            else:
                group = ''
        else:  # handle dict format group_by
            try:
                if str(node[LABEL_KEY]) in self.group_by_property:
                    if self.group_by_property[LABEL_KEY]['groupby'] in [LABEL_KEY, 'label']:
                        group = node[LABEL_KEY][0]
                    else:
                        group = node[PROPERTIES_KEY][self.group_by_property[LABEL_KEY]['groupby']]
                elif ID_KEY in self.group_by_property:
                    group = node[ID_KEY]
                else:
                    group = ''
            except KeyError:
                group = ''
        data['group_by']=group

        if title == '':
            for key in node[PROPERTIES_KEY]:
                title += str(node[PROPERTIES_KEY][key])
            label = title if len(title) <= self.label_max_length else title[:self.label_max_length - 3] + '...'
        data = {'properties': data[PROPERTIES_KEY], 'label': label, 'title': title, 'group': group}


        #logger.debug(data)
        nodes.append({ID_KEY: node[ID_KEY], PROPERTIES_KEY: data})
    
    def parse_rel(self, rel):
        """if not rel[START_KEY] in node_ids:        
            node_ids.append(rel[START_KEY])
            logger.debug("add start node")
            n = {ID_KEY: rel[START_KEY], LABEL_KEY:[rel[START_KEY]], PROPERTIES_KEY: {}}
            self.parse_node(n)        
        if not rel[END_KEY] in node_ids:        
            node_ids.append(rel[END_KEY])
            logger.debug("add end node")
            n = {ID_KEY: rel[END_KEY], LABEL_KEY:[rel[START_KEY]], PROPERTIES_KEY: {}}
            self.parse_node(n)"""
        self.add_edge(rel[START_KEY],rel[END_KEY], rel[ID_KEY], rel[ID_KEY], rel[ID_KEY])

    def process_result(self, res):
        if ENTITY_KEY in res:
            if res[ENTITY_KEY] == NODE_ENTITY_TYPE:
                self.parse_node(res)
            else:
                self.parse_rel(res)
        else:
            print("No Type Found")

    def add_results(self, results):
        """


        :param results: the data to be processed. Must be of type :type Path
        :return:
        """
        for res in results["results"]:
            if type(res) is dict:
                for k in res.keys():            
                    if type(res[k]) is dict:
                        self.process_result(res[k])
                    elif type(res[k]) is list:
                        for l in res[k]:
                            self.process_result(l)
        for n in nodes:
            self.add_node(n[ID_KEY], n[PROPERTIES_KEY])
