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

import ipywidgets as widgets
from SPARQLWrapper import SPARQLWrapper
from botocore.session import get_session
from gremlin_python.driver.protocol import GremlinServerError
from IPython.core.display import HTML, display_html, display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic, line_cell_magic, needs_local_scope)
from ipywidgets.widgets.widget_description import DescriptionStyle
from requests import HTTPError

import graph_notebook
from graph_notebook.configuration.generate_config import generate_default_config, DEFAULT_CONFIG_LOCATION, AuthModeEnum, \
    Configuration
from graph_notebook.decorators.decorators import display_exceptions, magic_variables
from graph_notebook.magics.ml import neptune_ml_magic_handler, generate_neptune_ml_parser
from graph_notebook.neptune.client import ClientBuilder, Client, VALID_FORMATS, PARALLELISM_OPTIONS, PARALLELISM_HIGH, \
    LOAD_JOB_MODES, MODE_AUTO, FINAL_LOAD_STATUSES, SPARQL_ACTION
from graph_notebook.network import SPARQLNetwork
from graph_notebook.network.gremlin.GremlinNetwork import parse_pattern_list_str, GremlinNetwork
from graph_notebook.visualization.sparql_rows_and_columns import get_rows_and_columns
from graph_notebook.visualization.template_retriever import retrieve_template
from graph_notebook.configuration.get_config import get_config, get_config_from_dict
from graph_notebook.seed.load_query import get_data_sets, get_queries
from graph_notebook.widgets import Force
from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED, vis_options_merge
from graph_notebook.magics.metadata import build_sparql_metadata_from_query, build_gremlin_metadata_from_query

sparql_table_template = retrieve_template("sparql_table.html")
sparql_explain_template = retrieve_template("sparql_explain.html")
sparql_construct_template = retrieve_template("sparql_construct.html")
gremlin_table_template = retrieve_template("gremlin_table.html")
pre_container_template = retrieve_template("pre_container.html")
loading_wheel_template = retrieve_template("loading_wheel.html")
error_template = retrieve_template("error.html")

loading_wheel_html = loading_wheel_template.render()
DEFAULT_LAYOUT = widgets.Layout(max_height='600px', overflow='scroll', width='100%')

logging.basicConfig()
logger = logging.getLogger("graph_magic")

DEFAULT_MAX_RESULTS = 1000

GREMLIN_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, for example: %gremlin_status --cancelQuery --queryId my-query-id'''
SPARQL_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery, for example: %sparql_status --cancelQuery --queryId my-query-id'''
SEED_LANGUAGE_OPTIONS = ['', 'Gremlin', 'SPARQL']

LOADER_FORMAT_CHOICES = ['']
LOADER_FORMAT_CHOICES.extend(VALID_FORMATS)


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
            print(
                'Could not find a valid configuration. Do not forgot to validate your settings using %graph_notebook_config')

        self.max_results = DEFAULT_MAX_RESULTS
        self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED
        self._generate_client_from_config(self.graph_notebook_config)
        logger.setLevel(logging.ERROR)

    def _generate_client_from_config(self, config: Configuration):
        if self.client:
            self.client.close()

        builder = ClientBuilder() \
            .with_host(config.host) \
            .with_port(config.port) \
            .with_region(config.aws_region) \
            .with_tls(config.ssl) \
            .with_sparql_path(config.sparql.path)
        if config.auth_mode == AuthModeEnum.IAM:
            builder = builder.with_iam(get_session())

        self.client = builder.build()

    # TODO: find out where we call this, then add local_ns param and variable decorator
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
                            help='prefix path to sparql endpoint. For example, if "foo/bar" were specified, the endpoint called would be host:port/foo/bar')
        parser.add_argument('--expand-all', action='store_true')
        parser.add_argument('--explain-type', default='dynamic',
                            help='explain mode to use when using the explain query mode',
                            choices=['dynamic', 'static', 'details'])
        parser.add_argument('--explain-format', default='text/html', help='response format for explain query mode',
                            choices=['text/csv', 'text/html'])
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)
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
            sparql_metadata = build_sparql_metadata_from_query(query_type='explain', res=res)
            explain = res.content.decode('utf-8')
            store_to_ns(args.store_to, explain, local_ns)
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

            # Assign an empty value so we can always display to table output.
            # We will only add it as a tab if the type of query allows it.
            # Because of this, the table_output will only be displayed on the DOM if the query was of type SELECT.
            first_tab_html = ""
            query_type = get_query_type(cell)
            if query_type in ['SELECT', 'CONSTRUCT', 'DESCRIBE']:
                logger.debug('creating sparql network...')

                titles.append('Table')
                sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=query_res, results=results,
                                                                   scd_query=True)

                sn = SPARQLNetwork(expand_all=args.expand_all)
                sn.extract_prefix_declarations_from_query(cell)
                try:
                    sn.add_results(results)
                except ValueError as value_error:
                    logger.debug(value_error)

                logger.debug(f'number of nodes is {len(sn.graph.nodes)}')
                if len(sn.graph.nodes) > 0:
                    f = Force(network=sn, options=self.graph_notebook_vis_options)
                    titles.append('Graph')
                    children.append(f)
                    logger.debug('added sparql network to tabs')

                rows_and_columns = get_rows_and_columns(results)
                if rows_and_columns is not None:
                    table_id = f"table-{str(uuid.uuid4())[:8]}"
                    first_tab_html = sparql_table_template.render(columns=rows_and_columns['columns'],
                                                                  rows=rows_and_columns['rows'], guid=table_id)

                # Handling CONSTRUCT and DESCRIBE on their own because we want to maintain the previous result pattern
                # of showing a tsv with each line being a result binding in addition to new ones.
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
                sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=query_res, results=results)

            json_output = widgets.Output(layout=DEFAULT_LAYOUT)
            with json_output:
                print(json.dumps(results, indent=2))
            children.append(json_output)
            titles.append('JSON')

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
                            help='If silent=true then the running query is cancelled and the HTTP response code is 200. If silent is not present or silent=false, the query is cancelled with an HTTP 500 status code.')
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
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)
        logger.debug(f'Arguments {args}')

        tab = widgets.Tab()
        children = []
        titles = []

        first_tab_output = widgets.Output(layout=DEFAULT_LAYOUT)
        children.append(first_tab_output)

        if mode == QueryMode.EXPLAIN:
            res = self.client.gremlin_explain(cell)
            res.raise_for_status()
            query_res = res.content.decode('utf-8')
            gremlin_metadata = build_gremlin_metadata_from_query(query_type='explain', results=query_res, res=res)
            titles.append('Explain')
            if 'Neptune Gremlin Explain' in query_res:
                first_tab_html = pre_container_template.render(content=query_res)
            else:
                first_tab_html = pre_container_template.render(content='No explain found')
        elif mode == QueryMode.PROFILE:
            res = self.client.gremlin_profile(cell)
            res.raise_for_status()
            query_res = res.content.decode('utf-8')
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
            gremlin_metadata = build_gremlin_metadata_from_query(query_type='query', results=query_res,
                                                                 query_time=query_time)
            titles.append('Console')
            try:
                logger.debug(f'groupby: {args.group_by}')
                logger.debug(f'ignore_groups: {args.ignore_groups}')
                gn = GremlinNetwork(group_by_property=args.group_by, ignore_groups=args.ignore_groups)

                if args.path_pattern == '':
                    gn.add_results(query_res)
                else:
                    pattern = parse_pattern_list_str(args.path_pattern)
                    gn.add_results_with_pattern(query_res, pattern)
                logger.debug(f'number of nodes is {len(gn.graph.nodes)}')
                if len(gn.graph.nodes) > 0:
                    f = Force(network=gn, options=self.graph_notebook_vis_options)
                    titles.append('Graph')
                    children.append(f)
                    logger.debug('added gremlin network to tabs')
            except ValueError as value_error:
                logger.debug(f'unable to create gremlin network from result. Skipping from result set: {value_error}')

            table_id = f"table-{str(uuid.uuid4()).replace('-', '')[:8]}"
            first_tab_html = gremlin_table_template.render(guid=table_id, results=query_res)

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
                            help='(Optional) Normally, only running queries are included in the response. When the includeWaiting parameter is specified, the status of all waiting queries is also returned.')
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

    @line_magic
    @display_exceptions
    def status(self, line):
        logger.info(f'calling for status on endpoint {self.graph_notebook_config.host}')
        status_res = self.client.status()
        status_res.raise_for_status()
        res = status_res.json()
        logger.info(f'got the response {res}')
        return res

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
        parser.add_argument('-l', '--loader-arn', default=self.graph_notebook_config.load_from_s3_arn)
        parser.add_argument('-f', '--format', choices=LOADER_FORMAT_CHOICES, default='')
        parser.add_argument('-p', '--parallelism', choices=PARALLELISM_OPTIONS, default=PARALLELISM_HIGH)
        parser.add_argument('-r', '--region', default=self.graph_notebook_config.aws_region)
        parser.add_argument('--fail-on-failure', action='store_true', default=False)
        parser.add_argument('--update-single-cardinality', action='store_true', default=True)
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--run', action='store_true', default=False)
        parser.add_argument('-m', '--mode', choices=LOAD_JOB_MODES, default=MODE_AUTO)
        parser.add_argument('-q', '--queue-request', action='store_true', default=False)
        parser.add_argument('-d', '--dependencies', action='append', default=[])

        args = parser.parse_args(line.split())

        region = self.graph_notebook_config.aws_region
        button = widgets.Button(description="Submit")
        output = widgets.Output()
        source = widgets.Text(
            value=args.source,
            placeholder='Type something',
            description='Source:',
            disabled=False,
        )

        arn = widgets.Text(
            value=args.loader_arn,
            placeholder='Type something',
            description='Load ARN:',
            disabled=False
        )

        source_format = widgets.Dropdown(
            options=LOADER_FORMAT_CHOICES,
            value=args.format,
            description='Format:',
            disabled=False
        )

        region_box = widgets.Text(
            value=region,
            placeholder=args.region,
            description='AWS Region:',
            disabled=False
        )

        fail_on_error = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.fail_on_failure).upper(),
            description='Fail on Failure: ',
            disabled=False
        )

        parallelism = widgets.Dropdown(
            options=PARALLELISM_OPTIONS,
            value=args.parallelism,
            description='Parallelism:',
            disabled=False
        )

        update_single_cardinality = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.update_single_cardinality).upper(),
            description='Update Single Cardinality:',
            disabled=False,
        )

        mode = widgets.Dropdown(
            options=LOAD_JOB_MODES,
            value=args.mode,
            description='Mode:',
            disabled=False
        )

        queue_request = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(args.queue_request).upper(),
            description='Queue Request:',
            disabled=False,
        )

        dependencies = widgets.Textarea(
            value="\n".join(args.dependencies),
            placeholder='load_A_id\nload_B_id',
            description='Dependencies:',
            disabled=False
        )

        source_hbox = widgets.HBox([source])
        arn_hbox = widgets.HBox([arn])
        source_format_hbox = widgets.HBox([source_format])
        dep_hbox = widgets.HBox([dependencies])

        display(source_hbox, source_format_hbox, region_box, arn_hbox, mode, fail_on_error, parallelism,
                update_single_cardinality, queue_request, dep_hbox, button, output)

        def on_button_clicked(b):
            source_hbox.children = (source,)
            arn_hbox.children = (arn,)
            source_format_hbox.children = (source_format,)
            dep_hbox.children = (dependencies,)

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

            source_exp = os.path.expandvars(
                source.value)  # replace any env variables in source.value with their values, can use $foo or ${foo}. Particularly useful for ${AWS_REGION}
            logger.info(f'using source_exp: {source_exp}')
            try:
                kwargs = {
                    'failOnError': fail_on_error.value,
                    'parallelism': parallelism.value,
                    'updateSingleCardinalityProperties': update_single_cardinality.value,
                    'queueRequest': queue_request.value
                }

                if dependencies:
                    kwargs['dependencies'] = dependencies_list

                load_res = self.client.load(source.value, source_format.value, arn.value, region_box.value, **kwargs)
                load_res.raise_for_status()
                load_result = load_res.json()
                store_to_ns(args.store_to, load_result, local_ns)

                source_hbox.close()
                source_format_hbox.close()
                region_box.close()
                arn_hbox.close()
                mode.close()
                fail_on_error.close()
                parallelism.close()
                update_single_cardinality.close()
                queue_request.close()
                dep_hbox.close()
                button.close()
                output.close()

                if 'status' not in load_result or load_result['status'] != '200 OK':
                    with output:
                        print('Something went wrong.')
                        print(load_result)
                        logger.error(load_result)
                    return

                load_id_label = widgets.Label(f'Load ID: {load_result["payload"]["loadId"]}')
                poll_interval = 5
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
        parser.add_argument('--language', type=str, default='', choices=SEED_LANGUAGE_OPTIONS)
        parser.add_argument('--dataset', type=str, default='')
        # TODO: Gremlin api paths are not yet supported.
        parser.add_argument('--path', '-p', default=SPARQL_ACTION,
                            help='prefix path to query endpoint. For example, "foo/bar". The queried path would then be host:port/foo/bar for sparql seed commands')
        parser.add_argument('--run', action='store_true')
        args = parser.parse_args(line.split())

        output = widgets.Output()
        progress_output = widgets.Output()
        language_dropdown = widgets.Dropdown(
            options=SEED_LANGUAGE_OPTIONS,
            description='Language:',
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
            selected_language = change['new']
            data_sets = get_data_sets(selected_language)
            data_sets.sort()
            data_set_drop_down.options = [ds for ds in data_sets if
                                          ds != '__pycache__']  # being extra sure that we aren't passing __pycache__ here.
            data_set_drop_down.layout.visibility = 'visible'
            submit_button.layout.visibility = 'visible'
            return

        def on_button_clicked(b=None):
            submit_button.close()
            language_dropdown.disabled = True
            data_set_drop_down.disabled = True
            language = language_dropdown.value.lower()
            data_set = data_set_drop_down.value.lower()
            with output:
                print(f'Loading data set {data_set} with language {language}')
            queries = get_queries(language, data_set)
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
                if language == 'gremlin':
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

            progress.close()
            with output:
                print('Done.')
            return

        submit_button.on_click(on_button_clicked)
        language_dropdown.observe(on_value_change, names='value')

        display(language_dropdown, data_set_drop_down, submit_button, progress_output, output)
        if args.language != '':
            language_dropdown.value = args.language

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

    # TODO: find out where we call this, then add local_ns param and variable decorator
    @line_cell_magic
    @display_exceptions
    def graph_notebook_vis_options(self, line='', cell=''):
        if line == 'reset':
            self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED

        if cell == '':
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
        res = neptune_ml_magic_handler(args, self.client, main_output, cell, local_ns)
        message = json.dumps(res, indent=2) if type(res) is dict else res
        store_to_ns(args.store_to, res, local_ns)
        with main_output:
            print(message)
