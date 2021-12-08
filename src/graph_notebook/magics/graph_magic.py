"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import print_function  # Python 2/3 compatibility

import argparse
import logging
import json
import time
import datetime
import os
import uuid
from enum import Enum
from json import JSONDecodeError
from graph_notebook.network.opencypher.OCNetwork import OCNetwork

import ipywidgets as widgets
from SPARQLWrapper import SPARQLWrapper
from botocore.session import get_session
from gremlin_python.driver.protocol import GremlinServerError
from IPython.core.display import HTML, display_html, display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic, line_cell_magic, needs_local_scope)
from ipywidgets.widgets.widget_description import DescriptionStyle
from requests import HTTPError

import graph_notebook
from graph_notebook.configuration.generate_config import generate_default_config, DEFAULT_CONFIG_LOCATION, \
    AuthModeEnum, Configuration
from graph_notebook.decorators.decorators import display_exceptions, magic_variables
from graph_notebook.magics.ml import neptune_ml_magic_handler, generate_neptune_ml_parser
from graph_notebook.magics.streams import StreamViewer
from graph_notebook.neptune.client import ClientBuilder, Client, VALID_FORMATS, PARALLELISM_OPTIONS, PARALLELISM_HIGH, \
    LOAD_JOB_MODES, MODE_AUTO, FINAL_LOAD_STATUSES, SPARQL_ACTION, FORMAT_CSV, FORMAT_OPENCYPHER, FORMAT_NTRIPLE, \
    FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE
from graph_notebook.network import SPARQLNetwork
from graph_notebook.network.gremlin.GremlinNetwork import parse_pattern_list_str, GremlinNetwork
from graph_notebook.visualization.rows_and_columns import sparql_get_rows_and_columns, opencypher_get_rows_and_columns
from graph_notebook.visualization.template_retriever import retrieve_template
from graph_notebook.configuration.get_config import get_config, get_config_from_dict
from graph_notebook.seed.load_query import get_data_sets, get_queries, normalize_model_name
from graph_notebook.widgets import Force
from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED, vis_options_merge
from graph_notebook.magics.metadata import build_sparql_metadata_from_query, build_gremlin_metadata_from_query, \
    build_opencypher_metadata_from_query

sparql_table_template = retrieve_template("sparql_table.html")
sparql_explain_template = retrieve_template("sparql_explain.html")
sparql_construct_template = retrieve_template("sparql_construct.html")
gremlin_table_template = retrieve_template("gremlin_table.html")
opencypher_table_template = retrieve_template("opencypher_table.html")
pre_container_template = retrieve_template("pre_container.html")
loading_wheel_template = retrieve_template("loading_wheel.html")
error_template = retrieve_template("error.html")

loading_wheel_html = loading_wheel_template.render()
DEFAULT_LAYOUT = widgets.Layout(max_height='600px', overflow='scroll', width='100%')

logging.basicConfig()
logger = logging.getLogger("graph_magic")

DEFAULT_MAX_RESULTS = 1000

GREMLIN_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, 
                            for example: %gremlin_status --cancelQuery --queryId my-query-id'''
SPARQL_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, 
                            for example: %sparql_status --cancelQuery --queryId my-query-id'''
OPENCYPHER_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, 
                                for example: %opencypher_status --cancelQuery --queryId my-query-id'''
SEED_LANGUAGE_OPTIONS = ['', 'Property_Graph', 'RDF']

LOADER_FORMAT_CHOICES = ['']
LOADER_FORMAT_CHOICES.extend(VALID_FORMATS)

serializers_map = {
    "MIME_JSON": "application/json",
    "GRAPHSON_V2D0": "application/vnd.gremlin-v2.0+json",
    "GRAPHSON_V3D0": "application/vnd.gremlin-v3.0+json",
    "GRYO_V3D0": "application/vnd.gremlin-v3.0+gryo",
    "GRAPHBINARY_V1D0": "application/vnd.graphbinary-v1.0"
}

DEFAULT_NAMEDGRAPH_URI = "http://aws.amazon.com/neptune/vocab/v01/DefaultNamedGraph"
DEFAULT_BASE_URI = "http://aws.amazon.com/neptune/default"
RDF_LOAD_FORMATS = [FORMAT_NTRIPLE, FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE]
BASE_URI_FORMATS = [FORMAT_RDFXML, FORMAT_TURTLE]

class QueryMode(Enum):
    DEFAULT = 'query'
    EXPLAIN = 'explain'
    PROFILE = 'profile'
    EMPTY = ''


def store_to_ns(key: str, value, ns: dict = None):
    if key == '' or ns is None:
        return

    ns[key] = value


def str_to_query_mode(s: str) -> QueryMode:
    s = s.lower()
    for mode in list(QueryMode):
        if mode.value == s:
            return QueryMode(s)

    logger.debug(f'Invalid query mode {s} supplied, defaulting to query.')
    return QueryMode.DEFAULT


ACTION_TO_QUERY_TYPE = {
    'sparql': 'application/sparql-query',
    'sparqlupdate': 'application/sparql-update'
}


def get_query_type(query):
    s = SPARQLWrapper('')
    s.setQuery(query)
    return s.queryType


def query_type_to_action(query_type):
    query_type = query_type.upper()
    if query_type in ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE']:
        return 'sparql'
    else:
        # TODO: check explicitly for all query types, raise exception for invalid query
        return 'sparqlupdate'


# TODO: refactor large magic commands into their own modules like what we do with %neptune_ml
# noinspection PyTypeChecker
@magics_class
class Graph(Magics):
    def __init__(self, shell):
        # You must call the parent constructor
        super(Graph, self).__init__(shell)

        self.graph_notebook_config = generate_default_config()
        try:
            self.config_location = os.getenv('GRAPH_NOTEBOOK_CONFIG', DEFAULT_CONFIG_LOCATION)
            self.client: Client = None
            self.graph_notebook_config = get_config(self.config_location)
        except FileNotFoundError:
            print('Could not find a valid configuration. '
                  'Do not forget to validate your settings using %graph_notebook_config.')

        self.max_results = DEFAULT_MAX_RESULTS
        self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED
        self._generate_client_from_config(self.graph_notebook_config)
        logger.setLevel(logging.ERROR)

    def _generate_client_from_config(self, config: Configuration):
        if self.client:
            self.client.close()

        if "amazonaws.com" in config.host:
            builder = ClientBuilder() \
                .with_host(config.host) \
                .with_port(config.port) \
                .with_region(config.aws_region) \
                .with_tls(config.ssl) \
                .with_sparql_path(config.sparql.path)
            if config.auth_mode == AuthModeEnum.IAM:
                builder = builder.with_iam(get_session())
        else:
            builder = ClientBuilder() \
                .with_host(config.host) \
                .with_port(config.port) \
                .with_tls(config.ssl) \
                .with_sparql_path(config.sparql.path) \
                .with_gremlin_traversal_source(config.gremlin.traversal_source)

        self.client = builder.build()

    @line_cell_magic
    @display_exceptions
    def graph_notebook_config(self, line='', cell=''):
        if cell != '':
            data = json.loads(cell)
            config = get_config_from_dict(data)
            self.graph_notebook_config = config
            self._generate_client_from_config(config)
            print('set notebook config to:')
            print(json.dumps(self.graph_notebook_config.to_dict(), indent=2))
        elif line == 'reset':
            self.graph_notebook_config = get_config(self.config_location)
            print('reset notebook config to:')
            print(json.dumps(self.graph_notebook_config.to_dict(), indent=2))
        elif line == 'silent':
            """
            silent option to that our neptune_menu extension can receive json instead
            of python Configuration object
            """
            config_dict = self.graph_notebook_config.to_dict()
            return print(json.dumps(config_dict, indent=2))
        else:
            config_dict = self.graph_notebook_config.to_dict()
            print(json.dumps(config_dict, indent=2))

        return self.graph_notebook_config
    

    @line_magic
    def stream_viewer(self,line):
        parser = argparse.ArgumentParser()
        parser.add_argument('language', type=str.lower, nargs='?', default='gremlin',
                            help='language  (default=gremlin) [gremlin|sparql]',
                            choices = ['gremlin','sparql'])

        parser.add_argument('--limit', type=int, default=10, help='Maximum number of rows to display at a time')

        args = parser.parse_args(line.split())
        
        language = args.language
        limit = args.limit
        uri = self.client.get_uri_with_port()
        viewer = StreamViewer(self.client,uri,language,limit=limit)
        viewer.show()
        
    @line_magic
    def graph_notebook_host(self, line):
        if line == '':
            print('please specify a host.')
            return

        # TODO: we should attempt to make a status call to this host before we set the config to this value.
        self.graph_notebook_config.host = line
        self._generate_client_from_config(self.graph_notebook_config)
        print(f'set host to {line}')

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    def sparql(self, line='', cell='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('query_mode', nargs='?', default='query',
                            help='query mode (default=query) [query|explain]')
        parser.add_argument('--path', '-p', default='',
                            help='prefix path to sparql endpoint. For example, if "foo/bar" were specified, '
                                 'the endpoint called would be host:port/foo/bar')
        parser.add_argument('--expand-all', action='store_true')
        parser.add_argument('--explain-type', default='dynamic',
                            help='explain mode to use when using the explain query mode',
                            choices=['dynamic', 'static', 'details'])
        parser.add_argument('--explain-format', default='text/html', help='response format for explain query mode',
                            choices=['text/csv', 'text/html'])
        parser.add_argument('-g', '--group-by', type=str, default='',
                            help='Property used to group nodes.')
        parser.add_argument('-d', '--display-property', type=str, default='',
                            help='Property to display the value of on each node.')
        parser.add_argument('-de', '--edge-display-property', type=str, default='',
                            help='Property to display the value of on each edge.')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex labels, in characters. Default is 10')
        parser.add_argument('-le', '--edge-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")
        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)

        if not args.silent:
            tab = widgets.Tab()
            titles = []
            children = []

            first_tab_output = widgets.Output(layout=DEFAULT_LAYOUT)
            children.append(first_tab_output)

        path = args.path if args.path != '' else self.graph_notebook_config.sparql.path
        logger.debug(f'using mode={mode}')
        if mode == QueryMode.EXPLAIN:
            res = self.client.sparql_explain(cell, args.explain_type, args.explain_format, path=path)
            res.raise_for_status()
            explain = res.content.decode('utf-8')
            store_to_ns(args.store_to, explain, local_ns)
            if not args.silent:
                sparql_metadata = build_sparql_metadata_from_query(query_type='explain', res=res)
                titles.append('Explain')
                first_tab_html = sparql_explain_template.render(table=explain)
        else:
            query_type = get_query_type(cell)
            headers = {} if query_type not in ['SELECT', 'CONSTRUCT', 'DESCRIBE'] else {
                'Accept': 'application/sparql-results+json'}

            query_res = self.client.sparql(cell, path=path, headers=headers)
            query_res.raise_for_status()
            results = query_res.json()
            store_to_ns(args.store_to, results, local_ns)
            try:
                res = query_res.json()
            except JSONDecodeError:
                res = query_res.content.decode('utf-8')
            store_to_ns(args.store_to, res, local_ns)

            if not args.silent:
                # Assign an empty value so we can always display to table output.
                # We will only add it as a tab if the type of query allows it.
                # Because of this, the table_output will only be displayed on the DOM if the query was of type SELECT.
                first_tab_html = ""
                query_type = get_query_type(cell)
                if query_type in ['SELECT', 'CONSTRUCT', 'DESCRIBE']:
                    logger.debug('creating sparql network...')

                    titles.append('Table')
                    sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=query_res,
                                                                       results=results, scd_query=True)

                    sn = SPARQLNetwork(group_by_property=args.group_by,
                                       display_property=args.display_property,
                                       edge_display_property=args.edge_display_property,
                                       tooltip_property=args.tooltip_property,
                                       edge_tooltip_property=args.edge_tooltip_property,
                                       label_max_length=args.label_max_length,
                                       edge_label_max_length=args.edge_label_max_length,
                                       ignore_groups=args.ignore_groups,
                                       expand_all=args.expand_all)
                    
                    sn.extract_prefix_declarations_from_query(cell)
                    try:
                        sn.add_results(results)
                    except ValueError as value_error:
                        logger.debug(value_error)

                    logger.debug(f'number of nodes is {len(sn.graph.nodes)}')
                    if len(sn.graph.nodes) > 0:
                        self.graph_notebook_vis_options['physics']['disablePhysicsAfterInitialSimulation'] \
                            = args.stop_physics
                        self.graph_notebook_vis_options['physics']['simulationDuration'] = args.simulation_duration
                        f = Force(network=sn, options=self.graph_notebook_vis_options)
                        titles.append('Graph')
                        children.append(f)
                        logger.debug('added sparql network to tabs')

                    rows_and_columns = sparql_get_rows_and_columns(results)
                    if rows_and_columns is not None:
                        table_id = f"table-{str(uuid.uuid4())[:8]}"
                        first_tab_html = sparql_table_template.render(columns=rows_and_columns['columns'],
                                                                      rows=rows_and_columns['rows'], guid=table_id)

                    # Handling CONSTRUCT and DESCRIBE on their own because we want to maintain the previous result
                    # pattern of showing a tsv with each line being a result binding in addition to new ones.
                    if query_type == 'CONSTRUCT' or query_type == 'DESCRIBE':
                        lines = []
                        for b in results['results']['bindings']:
                            lines.append(f'{b["subject"]["value"]}\t{b["predicate"]["value"]}\t{b["object"]["value"]}')
                        raw_output = widgets.Output(layout=DEFAULT_LAYOUT)
                        with raw_output:
                            html = sparql_construct_template.render(lines=lines)
                            display(HTML(html))
                        children.append(raw_output)
                        titles.append('Raw')
                else:
                    sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=query_res,
                                                                       results=results)

                json_output = widgets.Output(layout=DEFAULT_LAYOUT)
                with json_output:
                    print(json.dumps(results, indent=2))
                children.append(json_output)
                titles.append('JSON')

        if not args.silent:
            metadata_output = widgets.Output(layout=DEFAULT_LAYOUT)
            children.append(metadata_output)
            titles.append('Query Metadata')

            if first_tab_html == "":
                tab.children = children[1:]  # the first tab is empty, remove it and proceed
            else:
                tab.children = children

            for i in range(len(titles)):
                tab.set_title(i, titles[i])

            display(tab)

            with metadata_output:
                display(HTML(sparql_metadata.to_html()))

            if first_tab_html != "":
                with first_tab_output:
                    display(HTML(first_tab_html))

    @line_magic
    @needs_local_scope
    @display_exceptions
    def sparql_status(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running SPARQL query. Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Tells the status command to cancel a query. This parameter does not take a value')
        parser.add_argument('-s', '--silent', action='store_true',
                            help='If silent=true then the running query is cancelled and the HTTP response code is 200.'
                                 'If silent is not present or silent=false, '
                                 'the query is cancelled with an HTTP 500 status code.')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        if not args.cancelQuery:
            status_res = self.client.sparql_cancel(args.queryId)
            status_res.raise_for_status()
            res = status_res.json()
        else:
            if args.queryId == '':
                print(SPARQL_CANCEL_HINT_MSG)
                return
            else:
                cancel_res = self.client.sparql_cancel(args.queryId, args.silent)
                cancel_res.raise_for_status()
                res = cancel_res.json()

        store_to_ns(args.store_to, res, local_ns)
        print(json.dumps(res, indent=2))

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    def gremlin(self, line, cell, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('query_mode', nargs='?', default='query',
                            help='query mode (default=query) [query|explain|profile]')
        parser.add_argument('-p', '--path-pattern', default='', help='path pattern')
        parser.add_argument('-g', '--group-by', type=str, default='T.label',
                            help='Property used to group nodes (e.g. code, T.region) default is T.label')
        parser.add_argument('-d', '--display-property', type=str, default='T.label',
                            help='Property to display the value of on each node, default is T.label')
        parser.add_argument('-de', '--edge-display-property', type=str, default='T.label',
                            help='Property to display the value of on each edge, default is T.label')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the node label value.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the edge label value.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex label, in characters. Default is 10')
        parser.add_argument('-le', '--edge-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('--no-results', action='store_false', default=True,
                            help='Display only the result count. If not used, all query results will be displayed in '
                                 'the profile report by default.')
        parser.add_argument('--chop', type=int, default=250,
                            help='Property to specify max length of profile results string. Default is 250')
        parser.add_argument('--serializer', type=str, default='application/json',
                            help='Specify how to serialize results. Allowed values are any of the valid MIME type or '
                                 'TinkerPop driver "Serializers" enum values. Default is application/json')
        parser.add_argument('--indexOps', action='store_true', default=False,
                            help='Show a detailed report of all index operations.')
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")

        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)
        logger.debug(f'Arguments {args}')

        if not args.silent:
            tab = widgets.Tab()
            children = []
            titles = []

            first_tab_output = widgets.Output(layout=DEFAULT_LAYOUT)
            children.append(first_tab_output)

        if mode == QueryMode.EXPLAIN:
            res = self.client.gremlin_explain(cell)
            res.raise_for_status()
            query_res = res.content.decode('utf-8')
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='explain', results=query_res, res=res)
                titles.append('Explain')
                if 'Neptune Gremlin Explain' in query_res:
                    first_tab_html = pre_container_template.render(content=query_res)
                else:
                    first_tab_html = pre_container_template.render(content='No explain found')
        elif mode == QueryMode.PROFILE:
            logger.debug(f'results: {args.no_results}')
            logger.debug(f'chop: {args.chop}')
            logger.debug(f'serializer: {args.serializer}')
            logger.debug(f'indexOps: {args.indexOps}')
            if args.serializer in serializers_map:
                serializer = serializers_map[args.serializer]
            else:
                serializer = args.serializer
            profile_args = {"profile.results": args.no_results,
                            "profile.chop": args.chop,
                            "profile.serializer": serializer,
                            "profile.indexOps": args.indexOps}
            res = self.client.gremlin_profile(query=cell, args=profile_args)
            res.raise_for_status()
            query_res = res.content.decode('utf-8')
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='profile', results=query_res, res=res)
                titles.append('Profile')
                if 'Neptune Gremlin Profile' in query_res:
                    first_tab_html = pre_container_template.render(content=query_res)
                else:
                    first_tab_html = pre_container_template.render(content='No profile found')
        else:
            query_start = time.time() * 1000  # time.time() returns time in seconds w/high precision; x1000 to get in ms
            query_res = self.client.gremlin_query(cell)
            query_time = time.time() * 1000 - query_start
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='query', results=query_res,
                                                                     query_time=query_time)
                titles.append('Console')
                try:
                    logger.debug(f'groupby: {args.group_by}')
                    logger.debug(f'display_property: {args.display_property}')
                    logger.debug(f'edge_display_property: {args.edge_display_property}')
                    logger.debug(f'label_max_length: {args.label_max_length}')
                    logger.debug(f'ignore_groups: {args.ignore_groups}')
                    gn = GremlinNetwork(group_by_property=args.group_by, display_property=args.display_property,
                                        edge_display_property=args.edge_display_property,
                                        tooltip_property=args.tooltip_property,
                                        edge_tooltip_property=args.edge_tooltip_property,
                                        label_max_length=args.label_max_length,
                                        edge_label_max_length=args.edge_label_max_length,
                                        ignore_groups=args.ignore_groups)

                    if args.path_pattern == '':
                        gn.add_results(query_res)
                    else:
                        pattern = parse_pattern_list_str(args.path_pattern)
                        gn.add_results_with_pattern(query_res, pattern)
                    logger.debug(f'number of nodes is {len(gn.graph.nodes)}')
                    if len(gn.graph.nodes) > 0:
                        self.graph_notebook_vis_options['physics']['disablePhysicsAfterInitialSimulation'] \
                            = args.stop_physics
                        self.graph_notebook_vis_options['physics']['simulationDuration'] = args.simulation_duration
                        f = Force(network=gn, options=self.graph_notebook_vis_options)
                        titles.append('Graph')
                        children.append(f)
                        logger.debug('added gremlin network to tabs')
                except ValueError as value_error:
                    logger.debug(
                        f'unable to create gremlin network from result. Skipping from result set: {value_error}')

                table_id = f"table-{str(uuid.uuid4()).replace('-', '')[:8]}"
                first_tab_html = gremlin_table_template.render(guid=table_id, results=query_res)

        if not args.silent:
            metadata_output = widgets.Output(layout=DEFAULT_LAYOUT)
            titles.append('Query Metadata')
            children.append(metadata_output)

            tab.children = children
            for i in range(len(titles)):
                tab.set_title(i, titles[i])
            display(tab)

            with metadata_output:
                display(HTML(gremlin_metadata.to_html()))

            with first_tab_output:
                display(HTML(first_tab_html))

        store_to_ns(args.store_to, query_res, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    def gremlin_status(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running Gremlin query. Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Required for cancellation. Parameter has no corresponding value.')
        parser.add_argument('-w', '--includeWaiting', action='store_true',
                            help='(Optional) Normally, only running queries are included in the response. '
                                 'When the includeWaiting parameter is specified, '
                                 'the status of all waiting queries is also returned.')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        if not args.cancelQuery:
            status_res = self.client.gremlin_status(args.queryId)
            status_res.raise_for_status()
            res = status_res.json()
        else:
            if args.queryId == '':
                print(GREMLIN_CANCEL_HINT_MSG)
                return
            else:
                cancel_res = self.client.gremlin_cancel(args.queryId)
                cancel_res.raise_for_status()
                res = cancel_res.json()
        print(json.dumps(res, indent=2))
        store_to_ns(args.store_to, res, local_ns)

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    def oc(self, line='', cell='', local_ns: dict = None):
        self.handle_opencypher_query(line, cell, local_ns)

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    def opencypher(self, line='', cell='', local_ns: dict = None):
        self.handle_opencypher_query(line, cell, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    def oc_status(self, line='', local_ns: dict = None):
        self.handle_opencypher_status(line, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    def opencypher_status(self, line='', local_ns: dict = None):
        self.handle_opencypher_status(line, local_ns)

    @line_magic
    @display_exceptions
    def status(self, line):
        logger.info(f'calling for status on endpoint {self.graph_notebook_config.host}')
        status_res = self.client.status()
        status_res.raise_for_status()
        try:
            res = status_res.json()
            logger.info(f'got the json format response {res}')
            return res
        except ValueError:
            logger.info(f'got the HTML format response {status_res.text}')
            if "blazegraph&trade; by SYSTAP" in status_res.text:
                print("For more information on the status of your Blazegraph cluster, please visit: ")
                print()
                print(f'http://{self.graph_notebook_config.host}:{self.graph_notebook_config.port}/blazegraph/#status')
                print()
            return status_res

    @line_magic
    @display_exceptions
    def db_reset(self, line):
        logger.info(f'calling system endpoint {self.client.host}')
        parser = argparse.ArgumentParser()
        parser.add_argument('-g', '--generate-token', action='store_true', help='generate token for database reset')
        parser.add_argument('-t', '--token', default='', help='perform database reset with given token')
        parser.add_argument('-y', '--yes', action='store_true', help='skip the prompt and perform database reset')
        args = parser.parse_args(line.split())
        generate_token = args.generate_token
        skip_prompt = args.yes
        if generate_token is False and args.token == '':
            if skip_prompt:
                initiate_res = self.client.initiate_reset()
                initiate_res.raise_for_status()
                res = initiate_res.json()
                token = res['payload']['token']

                perform_reset_res = self.client.perform_reset(token)
                perform_reset_res.raise_for_status()
                logger.info(f'got the response {res}')
                res = perform_reset_res.json()
                return res

            output = widgets.Output()
            source = 'Are you sure you want to delete all the data in your cluster?'
            label = widgets.Label(source)
            text_hbox = widgets.HBox([label])
            check_box = widgets.Checkbox(
                value=False,
                disabled=False,
                indent=False,
                description='I acknowledge that upon deletion the cluster data will no longer be available.',
                layout=widgets.Layout(width='600px', margin='5px 5px 5px 5px')
            )
            button_delete = widgets.Button(description="Delete")
            button_cancel = widgets.Button(description="Cancel")
            button_hbox = widgets.HBox([button_delete, button_cancel])

            display(text_hbox, check_box, button_hbox, output)

            def on_button_delete_clicked(b):
                initiate_res = self.client.initiate_reset()
                initiate_res.raise_for_status()
                result = initiate_res.json()

                text_hbox.close()
                check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()

                if not check_box.value:
                    with output:
                        print('Checkbox is not checked.')
                    return
                token = result['payload']['token']
                if token == "":
                    with output:
                        print('Failed to get token.')
                        print(result)
                    return

                perform_reset_res = self.client.perform_reset(token)
                perform_reset_res.raise_for_status()
                result = perform_reset_res.json()

                if 'status' not in result or result['status'] != '200 OK':
                    with output:
                        print('Database reset failed, please try the operation again or reboot the cluster.')
                        print(result)
                        logger.error(result)
                    return

                retry = 10
                poll_interval = 5
                interval_output = widgets.Output()
                job_status_output = widgets.Output()
                status_hbox = widgets.HBox([interval_output])
                vbox = widgets.VBox([status_hbox, job_status_output])
                display(vbox)

                last_poll_time = time.time()
                while retry > 0:
                    time_elapsed = int(time.time() - last_poll_time)
                    time_remaining = poll_interval - time_elapsed
                    interval_output.clear_output()
                    if time_elapsed > poll_interval:
                        with interval_output:
                            print('checking status...')
                        job_status_output.clear_output()
                        with job_status_output:
                            display_html(HTML(loading_wheel_html))
                        try:
                            retry -= 1
                            status_res = self.client.status()
                            status_res.raise_for_status()
                            interval_check_response = status_res.json()
                        except Exception as e:
                            # Exception is expected when database is resetting, continue waiting
                            with job_status_output:
                                last_poll_time = time.time()
                                time.sleep(1)
                                continue
                        job_status_output.clear_output()
                        with job_status_output:
                            if interval_check_response["status"] == 'healthy':
                                interval_output.close()
                                print('Database has been reset.')
                                return
                        last_poll_time = time.time()
                    else:
                        with interval_output:
                            print(f'checking status in {time_remaining} seconds')
                    time.sleep(1)
                with output:
                    print(result)
                    if interval_check_response["status"] != 'healthy':
                        print("Could not retrieve the status of the reset operation within the allotted time. "
                              "If the database is not healthy after 1 min, please try the operation again or "
                              "reboot the cluster.")

            def on_button_cancel_clicked(b):
                text_hbox.close()
                check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()
                with output:
                    print('Database reset operation has been canceled.')

            button_delete.on_click(on_button_delete_clicked)
            button_cancel.on_click(on_button_cancel_clicked)
            return
        elif generate_token:
            initiate_res = self.client.initiate_reset()
            initiate_res.raise_for_status()
            res = initiate_res.json()
        else:
            # args.token is an array of a single string, e.g., args.token=['ade-23-c23'], use index 0 to take the string
            perform_res = self.client.perform_reset(args.token)
            perform_res.raise_for_status()
            res = perform_res.json()

        logger.info(f'got the response {res}')
        return res

    @line_magic
    @needs_local_scope
    @display_exceptions
    def load(self, line='', local_ns: dict = None):
        # TODO: change widgets to let any arbitrary inputs be added by users
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--source', default='s3://')
        try:
            parser.add_argument('-l', '--loader-arn', default=self.graph_notebook_config.load_from_s3_arn)
        except AttributeError:
            print(f"Missing required configuration option 'load_from_s3_arn'. Please ensure that you have provided a "
                  "valid Neptune cluster endpoint URI in the 'host' field of %graph_notebook_config.")
            return
        parser.add_argument('-f', '--format', choices=LOADER_FORMAT_CHOICES, default=FORMAT_CSV)
        parser.add_argument('-p', '--parallelism', choices=PARALLELISM_OPTIONS, default=PARALLELISM_HIGH)
        try:
            parser.add_argument('-r', '--region', default=self.graph_notebook_config.aws_region)
        except AttributeError:
            print("Missing required configuration option 'aws_region'. Please ensure that you have provided a "
                  "valid Neptune cluster endpoint URI in the 'host' field of %graph_notebook_config.")
            return
        parser.add_argument('--fail-on-failure', action='store_true', default=False)
        parser.add_argument('--update-single-cardinality', action='store_true', default=True)
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--run', action='store_true', default=False)
        parser.add_argument('-m', '--mode', choices=LOAD_JOB_MODES, default=MODE_AUTO)
        parser.add_argument('-q', '--queue-request', action='store_true', default=False)
        parser.add_argument('-d', '--dependencies', action='append', default=[])
        parser.add_argument('-e', '--no-edge-ids', action='store_true', default=False)
        parser.add_argument('--named-graph-uri', type=str, default=DEFAULT_NAMEDGRAPH_URI,
                            help='The default graph for all RDF formats when no graph is specified. '
                                 'Default is http://aws.amazon.com/neptune/vocab/v01/DefaultNamedGraph.')
        parser.add_argument('--base-uri', type=str, default=DEFAULT_BASE_URI,
                            help='The base URI for RDF/XML and Turtle formats. '
                                 'Default is http://aws.amazon.com/neptune/default')
        parser.add_argument('--allow-empty-strings', action='store_true', default=False,
                            help='Load empty strings found in node and edge property values.')
        parser.add_argument('-n', '--nopoll', action='store_true', default=False)

        args = parser.parse_args(line.split())
        region = self.graph_notebook_config.aws_region
        button = widgets.Button(description="Submit")
        output = widgets.Output()
        widget_width = '25%'
        label_width = '16%'

        source = widgets.Text(
            value=args.source,
            placeholder='Type something',
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        arn = widgets.Text(
            value=args.loader_arn,
            placeholder='Type something',
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        source_format = widgets.Dropdown(
            options=LOADER_FORMAT_CHOICES,
            value=args.format,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        ids_hbox_visibility = 'none'
        gremlin_parser_options_hbox_visibility = 'none'
        named_graph_hbox_visibility = 'none'
        base_uri_hbox_visibility = 'none'

        if source_format.value.lower() == FORMAT_CSV:
            gremlin_parser_options_hbox_visibility = 'flex'
        elif source_format.value.lower() == FORMAT_OPENCYPHER:
            ids_hbox_visibility = 'flex'
        elif source_format.value.lower() in RDF_LOAD_FORMATS:
            named_graph_hbox_visibility = 'flex'
            if source_format.value.lower() in BASE_URI_FORMATS:
                base_uri_hbox_visibility = 'flex'

        region_box = widgets.Text(
            value=region,
            placeholder=args.region,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        fail_on_error = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.fail_on_failure).upper(),
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        parallelism = widgets.Dropdown(
            options=PARALLELISM_OPTIONS,
            value=args.parallelism,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        allow_empty_strings = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.allow_empty_strings).upper(),
            disabled=False,
            layout=widgets.Layout(display=gremlin_parser_options_hbox_visibility,
                                  width=widget_width)
        )

        named_graph_uri = widgets.Text(
            value=args.named_graph_uri,
            placeholder='http://named-graph-string',
            disabled=False,
            layout=widgets.Layout(display=named_graph_hbox_visibility,
                                  width=widget_width)
        )

        base_uri = widgets.Text(
            value=args.base_uri,
            placeholder='http://base-uri-string',
            disabled=False,
            layout=widgets.Layout(display=base_uri_hbox_visibility,
                                  width=widget_width)
        )

        update_single_cardinality = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.update_single_cardinality).upper(),
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        mode = widgets.Dropdown(
            options=LOAD_JOB_MODES,
            value=args.mode,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        user_provided_edge_ids = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(not args.no_edge_ids).upper(),
            disabled=False,
            layout=widgets.Layout(display=ids_hbox_visibility,
                                  width=widget_width)
        )

        queue_request = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.queue_request).upper(),
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        dependencies = widgets.Textarea(
            value="\n".join(args.dependencies),
            placeholder='load_A_id\nload_B_id',
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        poll_status = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(not args.nopoll).upper(),
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        # Create a series of HBox containers that will hold the widgets and labels
        # that make up the %load form. Some of the labels and widgets are created
        # in two parts to support the validation steps that come later. In the case
        # of validation errors this allows additional text to easily be added to an
        # HBox describing the issue.
        source_hbox_label = widgets.Label('Source:',
                                          layout=widgets.Layout(width=label_width,
                                                                display="flex",
                                                                justify_content="flex-end"))

        source_hbox = widgets.HBox([source_hbox_label, source])

        format_hbox_label = widgets.Label('Format:',
                                          layout=widgets.Layout(width=label_width,
                                                                display="flex",
                                                                justify_content="flex-end"))

        source_format_hbox = widgets.HBox([format_hbox_label, source_format])

        region_hbox = widgets.HBox([widgets.Label('Region:',
                                                  layout=widgets.Layout(width=label_width,
                                                                        display="flex",
                                                                        justify_content="flex-end")),
                                    region_box])

        arn_hbox_label = widgets.Label('Load ARN:',
                                       layout=widgets.Layout(width=label_width,
                                                             display="flex",
                                                             justify_content="flex-end"))

        arn_hbox = widgets.HBox([arn_hbox_label, arn])

        mode_hbox = widgets.HBox([widgets.Label('Mode:',
                                                layout=widgets.Layout(width=label_width,
                                                                      display="flex",
                                                                      justify_content="flex-end")),
                                  mode])

        fail_hbox = widgets.HBox([widgets.Label('Fail on Error:',
                                                layout=widgets.Layout(width=label_width,
                                                                      display="flex",
                                                                      justify_content="flex-end")),
                                  fail_on_error])

        parallelism_hbox = widgets.HBox([widgets.Label('Parallelism:',
                                                       layout=widgets.Layout(width=label_width,
                                                                             display="flex",
                                                                             justify_content="flex-end")),
                                         parallelism])

        allow_empty_strings_hbox_label = widgets.Label('Allow Empty Strings:',
                                                       layout=widgets.Layout(width=label_width,
                                                                             display=gremlin_parser_options_hbox_visibility,
                                                                             justify_content="flex-end"))

        allow_empty_strings_hbox = widgets.HBox([allow_empty_strings_hbox_label, allow_empty_strings])

        named_graph_uri_hbox_label = widgets.Label('Named Graph URI:',
                                                   layout=widgets.Layout(width=label_width,
                                                                         display=named_graph_hbox_visibility,
                                                                         justify_content="flex-end"))

        named_graph_uri_hbox = widgets.HBox([named_graph_uri_hbox_label, named_graph_uri])

        base_uri_hbox_label = widgets.Label('Base URI:',
                                            layout=widgets.Layout(width=label_width,
                                                                  display=base_uri_hbox_visibility,
                                                                  justify_content="flex-end"))

        base_uri_hbox = widgets.HBox([base_uri_hbox_label, base_uri])

        cardinality_hbox = widgets.HBox([widgets.Label('Update Single Cardinality:',
                                                       layout=widgets.Layout(width=label_width,
                                                                             display="flex",
                                                                             justify_content="flex-end")),
                                         update_single_cardinality])

        queue_hbox = widgets.HBox([widgets.Label('Queue Request:',
                                                 layout=widgets.Layout(width=label_width,
                                                                       display="flex", justify_content="flex-end")),
                                   queue_request])

        dep_hbox_label = widgets.Label('Dependencies:',
                                       layout=widgets.Layout(width=label_width,
                                                             display="flex", justify_content="flex-end"))

        dep_hbox = widgets.HBox([dep_hbox_label, dependencies])

        ids_hbox_label = widgets.Label('User Provided Edge Ids:',
                                       layout=widgets.Layout(width=label_width,
                                                             display=ids_hbox_visibility,
                                                             justify_content="flex-end"))

        ids_hbox = widgets.HBox([ids_hbox_label, user_provided_edge_ids])

        poll_status_label = widgets.Label('Poll Load Status:',
                                          layout=widgets.Layout(width=label_width,
                                                                display="flex",
                                                                justify_content="flex-end"))

        poll_status_hbox = widgets.HBox([poll_status_label, poll_status])

        def update_edge_ids_options(change):
            if change.new.lower() == FORMAT_OPENCYPHER:
                ids_hbox_visibility = 'flex'
            else:
                ids_hbox_visibility = 'none'
                user_provided_edge_ids.value = 'TRUE'
            user_provided_edge_ids.layout.display = ids_hbox_visibility
            ids_hbox_label.layout.display = ids_hbox_visibility

        def update_parserconfig_options(change):
            if change.new.lower() == FORMAT_CSV:
                gremlin_parser_options_hbox_visibility = 'flex'
                named_graph_hbox_visibility_hbox_visibility = 'none'
                base_uri_hbox_visibility = 'none'
                named_graph_uri.value = ''
                base_uri.value = ''
            elif change.new.lower() == FORMAT_OPENCYPHER:
                gremlin_parser_options_hbox_visibility = 'none'
                allow_empty_strings.value = 'FALSE'
                named_graph_hbox_visibility_hbox_visibility = 'none'
                base_uri_hbox_visibility = 'none'
                named_graph_uri.value = ''
                base_uri.value = ''
            else:
                gremlin_parser_options_hbox_visibility = 'none'
                allow_empty_strings.value = 'FALSE'
                named_graph_hbox_visibility_hbox_visibility = 'flex'
                named_graph_uri.value = DEFAULT_NAMEDGRAPH_URI
                if change.new.lower() in BASE_URI_FORMATS:
                    base_uri_hbox_visibility = 'flex'
                    base_uri.value = DEFAULT_BASE_URI
                else:
                    base_uri_hbox_visibility = 'none'
                    base_uri.value = ''

            allow_empty_strings.layout.display = gremlin_parser_options_hbox_visibility
            allow_empty_strings_hbox_label.layout.display = gremlin_parser_options_hbox_visibility
            named_graph_uri.layout.display = named_graph_hbox_visibility_hbox_visibility
            named_graph_uri_hbox_label.layout.display = named_graph_hbox_visibility_hbox_visibility
            base_uri.layout.display = base_uri_hbox_visibility
            base_uri_hbox_label.layout.display = base_uri_hbox_visibility

        source_format.observe(update_edge_ids_options, names='value')
        source_format.observe(update_parserconfig_options, names='value')

        display(source_hbox,
                source_format_hbox,
                region_hbox,
                arn_hbox,
                mode_hbox,
                fail_hbox,
                parallelism_hbox,
                cardinality_hbox,
                queue_hbox,
                dep_hbox,
                poll_status_hbox,
                ids_hbox,
                allow_empty_strings_hbox,
                named_graph_uri_hbox,
                base_uri_hbox,
                button,
                output)

        def on_button_clicked(b):
            source_hbox.children = (source_hbox_label, source,)
            arn_hbox.children = (arn_hbox_label, arn,)
            source_format_hbox.children = (format_hbox_label, source_format,)
            allow_empty_strings.children = (allow_empty_strings_hbox_label, allow_empty_strings,)
            named_graph_uri_hbox.children = (named_graph_uri_hbox_label, named_graph_uri,)
            base_uri_hbox.children = (base_uri_hbox_label, base_uri,)
            dep_hbox.children = (dep_hbox_label, dependencies,)

            dependencies_list = list(filter(None, dependencies.value.split('\n')))

            validated = True
            validation_label_style = DescriptionStyle(color='red')
            if not (source.value.startswith('s3://') and len(source.value) > 7) and not source.value.startswith('/'):
                validated = False
                source_validation_label = widgets.HTML(
                    '<p style="color:red;">Source must be an s3 bucket or file path</p>')
                source_validation_label.style = validation_label_style
                source_hbox.children += (source_validation_label,)

            if source_format.value == '':
                validated = False
                source_format_validation_label = widgets.HTML('<p style="color:red;">Format cannot be blank.</p>')
                source_format_hbox.children += (source_format_validation_label,)

            if not arn.value.startswith('arn:aws') and source.value.startswith(
                    "s3://"):  # only do this validation if we are using an s3 bucket.
                validated = False
                arn_validation_label = widgets.HTML('<p style="color:red;">Load ARN must start with "arn:aws"</p>')
                arn_hbox.children += (arn_validation_label,)

            if not len(dependencies_list) < 64:
                validated = False
                dep_validation_label = widgets.HTML(
                    '<p style="color:red;">A maximum of 64 jobs may be queued at once.</p>')
                dep_hbox.children += (dep_validation_label,)

            if not validated:
                return

            # replace any env variables in source.value with their values, can use $foo or ${foo}.
            # Particularly useful for ${AWS_REGION}
            source_exp = os.path.expandvars(
                source.value)
            logger.info(f'using source_exp: {source_exp}')
            try:
                kwargs = {
                    'failOnError': fail_on_error.value,
                    'parallelism': parallelism.value,
                    'updateSingleCardinalityProperties': update_single_cardinality.value,
                    'queueRequest': queue_request.value,
                    'region': region,
                    'parserConfiguration': {}
                }

                if dependencies:
                    kwargs['dependencies'] = dependencies_list

                if source_format.value.lower() == FORMAT_OPENCYPHER:
                    kwargs['userProvidedEdgeIds'] = user_provided_edge_ids.value
                elif source_format.value.lower() == FORMAT_CSV:
                    if allow_empty_strings.value == 'TRUE':
                        kwargs['parserConfiguration']['allowEmptyStrings'] = True
                elif source_format.value.lower() in RDF_LOAD_FORMATS:
                    if named_graph_uri.value:
                        kwargs['parserConfiguration']['namedGraphUri'] = named_graph_uri.value
                    if base_uri.value and source_format.value.lower() in BASE_URI_FORMATS:
                        kwargs['parserConfiguration']['baseUri'] = base_uri.value

                if source.value.startswith("s3://"):
                    load_res = self.client.load(str(source_exp), source_format.value, arn.value, **kwargs)
                else:
                    load_res = self.client.load(str(source_exp), source_format.value, **kwargs)
                load_res.raise_for_status()
                load_result = load_res.json()
                store_to_ns(args.store_to, load_result, local_ns)

                source_hbox.close()
                source_format_hbox.close()
                region_hbox.close()
                arn_hbox.close()
                mode_hbox.close()
                fail_hbox.close()
                parallelism_hbox.close()
                cardinality_hbox.close()
                queue_hbox.close()
                dep_hbox.close()
                poll_status_hbox.close()
                ids_hbox.close()
                allow_empty_strings_hbox.close()
                named_graph_uri_hbox.close()
                base_uri_hbox.close()
                button.close()
                output.close()

                if 'status' not in load_result or load_result['status'] != '200 OK':
                    with output:
                        print('Something went wrong.')
                        print(load_result)
                        logger.error(load_result)
                    return

                if poll_status.value == 'FALSE':
                    start_msg_label = widgets.Label(f'Load started successfully!')
                    polling_msg_label = widgets.Label(f'You can run "%load_status {load_result["payload"]["loadId"]}" '
                                                      f'in another cell to check the current status of your bulk load.')
                    start_msg_hbox = widgets.HBox([start_msg_label])
                    polling_msg_hbox = widgets.HBox([polling_msg_label])
                    vbox = widgets.VBox([start_msg_hbox, polling_msg_hbox])
                    display(vbox)
                else:
                    poll_interval = 5
                    load_id_label = widgets.Label(f'Load ID: {load_result["payload"]["loadId"]}')
                    interval_output = widgets.Output()
                    job_status_output = widgets.Output()
                    load_id_hbox = widgets.HBox([load_id_label])
                    status_hbox = widgets.HBox([interval_output])
                    vbox = widgets.VBox([load_id_hbox, status_hbox, job_status_output])
                    display(vbox)

                    last_poll_time = time.time()
                    while True:
                        time_elapsed = int(time.time() - last_poll_time)
                        time_remaining = poll_interval - time_elapsed
                        interval_output.clear_output()
                        if time_elapsed > poll_interval:
                            with interval_output:
                                print('checking status...')
                            job_status_output.clear_output()
                            with job_status_output:
                                display_html(HTML(loading_wheel_html))
                            try:
                                load_status_res = self.client.load_status(load_result['payload']['loadId'])
                                load_status_res.raise_for_status()
                                interval_check_response = load_status_res.json()
                            except Exception as e:
                                logger.error(e)
                                with job_status_output:
                                    print('Something went wrong updating job status. Ending.')
                                    return
                            job_status_output.clear_output()
                            with job_status_output:
                                print(f'Overall Status: {interval_check_response["payload"]["overallStatus"]["status"]}')
                                if interval_check_response["payload"]["overallStatus"]["status"] in FINAL_LOAD_STATUSES:
                                    execution_time = interval_check_response["payload"]["overallStatus"]["totalTimeSpent"]
                                    if execution_time == 0:
                                        execution_time_statement = '<1 second'
                                    elif execution_time > 59:
                                        execution_time_statement = str(datetime.timedelta(seconds=execution_time))
                                    else:
                                        execution_time_statement = f'{execution_time} seconds'
                                    print('Total execution time: ' + execution_time_statement)
                                    interval_output.close()
                                    print('Done.')
                                    return
                            last_poll_time = time.time()
                        else:
                            with interval_output:
                                print(f'checking status in {time_remaining} seconds')
                        time.sleep(1)

            except HTTPError as httpEx:
                output.clear_output()
                with output:
                    print(httpEx.response.content.decode('utf-8'))

        button.on_click(on_button_clicked)
        if args.run:
            on_button_clicked(None)

    @line_magic
    @display_exceptions
    @needs_local_scope
    def load_ids(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('--store-to', type=str, default='')
        args = parser.parse_args(line.split())

        load_status = self.client.load_status()
        load_status.raise_for_status()
        res = load_status.json()
        ids = []
        if 'payload' in res and 'loadIds' in res['payload']:
            ids = res['payload']['loadIds']

        labels = [widgets.Label(value=label_id) for label_id in ids]

        if not labels:
            labels = [widgets.Label(value="No load IDs found.")]

        vbox = widgets.VBox(labels)
        display(vbox)

        if args.store_to != '' and local_ns is not None:
            local_ns[args.store_to] = res

    @line_magic
    @display_exceptions
    @needs_local_scope
    def load_status(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('load_id', default='', help='loader id to check status for')
        parser.add_argument('--store-to', type=str, default='')
        parser.add_argument('--details', action='store_true', default=False)
        parser.add_argument('--errors', action='store_true', default=False)
        parser.add_argument('--page', '-p', default='1',
                            help='The error page number. Only valid when the --errors option is set.')
        parser.add_argument('--errorsPerPage', '-e', default='10',
                            help='The number of errors per each page. Only valid when the --errors option is set.')
        args = parser.parse_args(line.split())

        payload = {
            'details': args.details,
            'errors': args.errors,
            'page': args.page,
            'errorsPerPage': args.errorsPerPage
        }
        load_status_res = self.client.load_status(args.load_id, **payload)
        load_status_res.raise_for_status()
        res = load_status_res.json()
        print(json.dumps(res, indent=2))

        if args.store_to != '' and local_ns is not None:
            local_ns[args.store_to] = res

    @line_magic
    @display_exceptions
    @needs_local_scope
    def cancel_load(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('load_id', default='', help='loader id to check status for')
        parser.add_argument('--store-to', type=str, default='')
        args = parser.parse_args(line.split())

        cancel_res = self.client.cancel_load(args.load_id)
        cancel_res.raise_for_status()
        res = cancel_res.json()
        if res:
            print('Cancelled successfully.')
        else:
            print('Something went wrong cancelling bulk load job.')

        if args.store_to != '' and local_ns is not None:
            local_ns[args.store_to] = res

    @line_magic
    @display_exceptions
    def seed(self, line):
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', type=str, default='', choices=SEED_LANGUAGE_OPTIONS)
        parser.add_argument('--dataset', type=str, default='')
        # TODO: Gremlin api paths are not yet supported.
        parser.add_argument('--path', '-p', default=SPARQL_ACTION,
                            help='prefix path to query endpoint. For example, "foo/bar". '
                                 'The queried path would then be host:port/foo/bar for sparql seed commands')
        parser.add_argument('--run', action='store_true')
        args = parser.parse_args(line.split())

        output = widgets.Output()
        progress_output = widgets.Output()
        model_dropdown = widgets.Dropdown(
            options=SEED_LANGUAGE_OPTIONS,
            description='Data model:',
            disabled=False
        )

        data_set_drop_down = widgets.Dropdown(
            description='Data set:',
            disabled=False
        )

        submit_button = widgets.Button(description="Submit")
        data_set_drop_down.layout.visibility = 'hidden'
        submit_button.layout.visibility = 'hidden'

        def on_value_change(change):
            selected_model = change['new']
            data_sets = get_data_sets(selected_model)
            data_sets.sort()
            data_set_drop_down.options = [ds for ds in data_sets if
                                          ds != '__pycache__']  # being extra sure that we aren't passing __pycache__.
            data_set_drop_down.layout.visibility = 'visible'
            submit_button.layout.visibility = 'visible'
            return

        def on_button_clicked(b=None):
            submit_button.close()
            model_dropdown.disabled = True
            data_set_drop_down.disabled = True
            model = normalize_model_name(model_dropdown.value)
            data_set = data_set_drop_down.value.lower()
            with output:
                print(f'Loading data set {data_set} for {model}')
            queries = get_queries(model, data_set)
            if len(queries) < 1:
                with output:
                    print('Did not find any queries for the given dataset')
                return

            load_index = 1  # start at 1 to have a non-empty progress bar
            progress = widgets.IntProgress(
                value=load_index,
                min=0,
                max=len(queries) + 1,  # len + 1 so we can start at index 1
                orientation='horizontal',
                bar_style='info',
                description='Loading:'
            )

            with progress_output:
                display(progress)

            for q in queries:
                with output:
                    print(f'{progress.value}/{len(queries)}:\t{q["name"]}')
                if model == 'propertygraph':
                    # IMPORTANT: We treat each line as its own query!
                    for line in q['content'].splitlines():
                        try:
                            self.client.gremlin_query(line)
                        except GremlinServerError as gremlinEx:
                            try:
                                error = json.loads(gremlinEx.args[0][5:])  # remove the leading error code.
                                content = json.dumps(error, indent=2)
                            except Exception:
                                content = {
                                    'error': gremlinEx
                                }

                            with output:
                                print(content)
                            progress.close()
                            return
                        except Exception as e:
                            content = {
                                'error': e
                            }
                            with output:
                                print(content)
                            progress.close()
                            return
                else:
                    try:
                        self.client.sparql(q['content'], path=args.path)
                    except HTTPError as httpEx:
                        # attempt to turn response into json
                        try:
                            error = json.loads(httpEx.response.content.decode('utf-8'))
                            content = json.dumps(error, indent=2)
                        except Exception:
                            content = {
                                'error': httpEx
                            }
                        with output:
                            print(content)
                        progress.close()
                        return
                    except Exception as ex:
                        content = {
                            'error': str(ex)
                        }
                        with output:
                            print(content)

                        progress.close()
                        return

                progress.value += 1
            # Sleep for two seconds so the user sees the progress bar complete
            time.sleep(2)
            progress.close()
            with output:
                print('Done.')
            return

        submit_button.on_click(on_button_clicked)
        model_dropdown.observe(on_value_change, names='value')

        display(model_dropdown, data_set_drop_down, submit_button, progress_output, output)
        if args.model != '':
            model_dropdown.value = args.model
            if args.dataset != '' and args.dataset in data_set_drop_down.options:
                data_set_drop_down.value = args.dataset.lower()
                if args.run:
                    on_button_clicked()

    @line_magic
    def enable_debug(self, line):
        logger.setLevel(logging.DEBUG)

    @line_magic
    def disable_debug(self, line):
        logger.setLevel(logging.ERROR)

    @line_magic
    def graph_notebook_version(self, line):
        print(graph_notebook.__version__)

    @line_cell_magic
    @display_exceptions
    def graph_notebook_vis_options(self, line='', cell=''):
        parser = argparse.ArgumentParser()
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        line_args = line.split()
        if line_args:
            if line_args[0] == 'reset':
                line = 'reset'
                if len(line_args) > 1:
                    line_args = line_args[1:]
                else:
                    line_args = []
        args = parser.parse_args(line_args)

        if line == 'reset':
            self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED

        if cell == '':
            if not args.silent:
                print(json.dumps(self.graph_notebook_vis_options, indent=2))
        else:
            options_dict = json.loads(cell)
            self.graph_notebook_vis_options = vis_options_merge(self.graph_notebook_vis_options, options_dict)

    @magic_variables
    @line_cell_magic
    @display_exceptions
    @needs_local_scope
    def neptune_ml(self, line, cell='', local_ns: dict = None):
        parser = generate_neptune_ml_parser()
        args = parser.parse_args(line.split())
        logger.info(f'received call to neptune_ml with details: {args.__dict__}, cell={cell}, local_ns={local_ns}')
        main_output = widgets.Output()
        display(main_output)
        res = neptune_ml_magic_handler(args, self.client, main_output, cell)
        message = json.dumps(res, indent=2) if type(res) is dict else res
        store_to_ns(args.store_to, res, local_ns)
        with main_output:
            print(message)

    def handle_opencypher_query(self, line, cell, local_ns):
        """
        This method in its own handler so that the magics %%opencypher and %%oc can both call it
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-g', '--group-by', type=str, default='~labels',
                            help='Property used to group nodes (e.g. code, ~id) default is ~labels')
        parser.add_argument('mode', nargs='?', default='query', help='query mode [query|bolt]',
                            choices=['query', 'bolt'])
        parser.add_argument('-d', '--display-property', type=str, default='~labels',
                            help='Property to display the value of on each node, default is ~labels')
        parser.add_argument('-de', '--edge-display-property', type=str, default='~labels',
                            help='Property to display the value of on each edge, default is ~type')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the node label value.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the edge label value.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex label, in characters. Default is 10')
        parser.add_argument('-rel', '--rel-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")
        args = parser.parse_args(line.split())
        logger.debug(args)
        res = None

        if not args.silent:
            tab = widgets.Tab()
            titles = []
            children = []
            force_graph_output = None

        if args.mode == 'query':
            query_start = time.time() * 1000  # time.time() returns time in seconds w/high precision; x1000 to get in ms
            oc_http = self.client.opencypher_http(cell)
            query_time = time.time() * 1000 - query_start
            oc_http.raise_for_status()
            res = oc_http.json()
            if not args.silent:
                oc_metadata = build_opencypher_metadata_from_query(query_type='query', results=res,
                                                                   query_time=query_time)
                try:
                    gn = OCNetwork(group_by_property=args.group_by, display_property=args.display_property,
                                   edge_display_property=args.edge_display_property,
                                   tooltip_property=args.tooltip_property,
                                   edge_tooltip_property=args.edge_tooltip_property,
                                   label_max_length=args.label_max_length,
                                   edge_label_max_length=args.rel_label_max_length,
                                   ignore_groups=args.ignore_groups)
                    gn.add_results(res)
                    logger.debug(f'number of nodes is {len(gn.graph.nodes)}')
                    if len(gn.graph.nodes) > 0:
                        self.graph_notebook_vis_options['physics']['disablePhysicsAfterInitialSimulation'] \
                            = args.stop_physics
                        self.graph_notebook_vis_options['physics']['simulationDuration'] = args.simulation_duration
                        force_graph_output = Force(network=gn, options=self.graph_notebook_vis_options)
                except (TypeError, ValueError) as network_creation_error:
                    logger.debug(f'Unable to create network from result. Skipping from result set: {res}')
                    logger.debug(f'Error: {network_creation_error}')
        elif args.mode == 'bolt':
            res = self.client.opencyper_bolt(cell)            
            # Need to eventually add code to parse and display a network for the bolt format here

        if not args.silent:
            rows_and_columns = opencypher_get_rows_and_columns(res, True if args.mode == 'bolt' else False)
            display(tab)
            table_output = widgets.Output(layout=DEFAULT_LAYOUT)
            # Assign an empty value so we can always display to table output.
            table_html = ""

            # Display Console Tab
            # some issues with displaying a datatable when not wrapped in an hbox and displayed last
            hbox = widgets.HBox([table_output], layout=DEFAULT_LAYOUT)
            children.append(hbox)
            titles.append('Console')
            if rows_and_columns is not None:
                table_id = f"table-{str(uuid.uuid4())[:8]}"
                table_html = opencypher_table_template.render(columns=rows_and_columns['columns'],
                                                              rows=rows_and_columns['rows'], guid=table_id)

            # Display Graph Tab (if exists)
            if force_graph_output:
                titles.append('Graph')
                children.append(force_graph_output)

            # Display JSON tab
            json_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with json_output:
                print(json.dumps(res, indent=2))
            children.append(json_output)
            titles.append('JSON')

            # Display Query Metadata Tab
            metadata_output = widgets.Output(layout=DEFAULT_LAYOUT)
            titles.append('Query Metadata')
            children.append(metadata_output)

            tab.children = children
            for i in range(len(titles)):
                tab.set_title(i, titles[i])

            if table_html != "":
                with table_output:
                    display(HTML(table_html))

            with metadata_output:
                display(HTML(oc_metadata.to_html()))

        store_to_ns(args.store_to, res, local_ns)

    def handle_opencypher_status(self, line, local_ns):
        """
        This is refactored xinto its own handler method so that we can invoke is from
        %opencypher_status or from %oc_status
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running OpenCypher query. '
                                 'Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Tells the status command to cancel a query. This parameter does not take a value')
        parser.add_argument('-s', '--silent', action='store_true',
                            help='If silent=true then the running query is cancelled and the HTTP response code is 200.'
                                 ' If silent is not present or silent=false, '
                                 'the query is cancelled with an HTTP 500 status code.')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        if not args.cancelQuery:
            res = self.client.opencypher_status(args.queryId)
            res.raise_for_status()
        else:
            if args.queryId == '':
                print(OPENCYPHER_CANCEL_HINT_MSG)
                return
            else:
                res = self.client.opencypher_cancel(args.queryId, args.silent)
                res.raise_for_status()
        js = res.json()
        store_to_ns(args.store_to, js, local_ns)
        print(json.dumps(js, indent=2))
