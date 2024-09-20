"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from __future__ import print_function  # Python 2/3 compatibility

import argparse
import base64
import logging
import json
import time
import datetime
import os
import uuid
import ast
import re

from ipyfilechooser import FileChooser
from enum import Enum
from copy import copy
from sys import maxsize
from json import JSONDecodeError
from collections import deque
from graph_notebook.network.opencypher.OCNetwork import OCNetwork

import ipywidgets as widgets
import pandas as pd
import itables.options as opt
from itables import show, JavascriptFunction, init_notebook_mode
from SPARQLWrapper import SPARQLWrapper
from botocore.session import get_session
from gremlin_python.driver.protocol import GremlinServerError
from gremlin_python.structure.graph import Path
from IPython.core.display import HTML, display_html, display
from IPython.core.magic import (Magics, magics_class, cell_magic, line_magic, line_cell_magic, needs_local_scope)
from ipywidgets.widgets.widget_description import DescriptionStyle
from requests import HTTPError
from json_repair import repair_json

import graph_notebook
from graph_notebook.configuration.generate_config import generate_default_config, DEFAULT_CONFIG_LOCATION, \
    AuthModeEnum, Configuration
from graph_notebook.decorators.decorators import display_exceptions, magic_variables, \
    neptune_db_only, neptune_graph_only
from graph_notebook.magics.ml import neptune_ml_magic_handler, generate_neptune_ml_parser
from graph_notebook.magics.streams import StreamViewer
from graph_notebook.neptune.client import (ClientBuilder, Client, PARALLELISM_OPTIONS, PARALLELISM_HIGH, \
    LOAD_JOB_MODES, MODE_AUTO, FINAL_LOAD_STATUSES, SPARQL_ACTION, FORMAT_CSV, FORMAT_OPENCYPHER, FORMAT_NTRIPLE, \
    DB_LOAD_TYPES, ANALYTICS_LOAD_TYPES, VALID_BULK_FORMATS, VALID_INCREMENTAL_FORMATS, \
    FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE, FORMAT_NTRIPLE, STREAM_RDF, STREAM_PG, STREAM_ENDPOINTS, \
    NEPTUNE_CONFIG_HOST_IDENTIFIERS, is_allowed_neptune_host, \
    STATISTICS_LANGUAGE_INPUTS, STATISTICS_LANGUAGE_INPUTS_SPARQL, STATISTICS_MODES, SUMMARY_MODES, \
    SPARQL_EXPLAIN_MODES, OPENCYPHER_EXPLAIN_MODES, GREMLIN_EXPLAIN_MODES, \
    OPENCYPHER_PLAN_CACHE_MODES, OPENCYPHER_DEFAULT_TIMEOUT, OPENCYPHER_STATUS_STATE_MODES, \
    normalize_service_name, NEPTUNE_DB_SERVICE_NAME, NEPTUNE_ANALYTICS_SERVICE_NAME, GRAPH_PG_INFO_METRICS, \
    GREMLIN_PROTOCOL_FORMATS, DEFAULT_HTTP_PROTOCOL, DEFAULT_WS_PROTOCOL, \
    GREMLIN_SERIALIZERS_WS, GREMLIN_SERIALIZERS_CLASS_TO_MIME_MAP, normalize_protocol_name, generate_snapshot_name)
from graph_notebook.network import SPARQLNetwork
from graph_notebook.network.gremlin.GremlinNetwork import parse_pattern_list_str, GremlinNetwork
from graph_notebook.visualization.rows_and_columns import sparql_get_rows_and_columns, opencypher_get_rows_and_columns
from graph_notebook.visualization.template_retriever import retrieve_template
from graph_notebook.configuration.get_config import get_config, get_config_from_dict
from graph_notebook.seed.load_query import get_data_sets, get_queries, normalize_model_name, normalize_language_name
from graph_notebook.widgets import Force
from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED, vis_options_merge
from graph_notebook.magics.metadata import build_sparql_metadata_from_query, build_gremlin_metadata_from_query, \
    build_opencypher_metadata_from_query

sparql_table_template = retrieve_template("sparql_table.html")
sparql_explain_template = retrieve_template("sparql_explain.html")
sparql_construct_template = retrieve_template("sparql_construct.html")
gremlin_table_template = retrieve_template("gremlin_table.html")
opencypher_table_template = retrieve_template("opencypher_table.html")
opencypher_explain_template = retrieve_template("opencypher_explain.html")
gremlin_explain_profile_template = retrieve_template("gremlin_explain_profile.html")
pre_container_template = retrieve_template("pre_container.html")
loading_wheel_template = retrieve_template("loading_wheel.html")
error_template = retrieve_template("error.html")

loading_wheel_html = loading_wheel_template.render()
DEFAULT_LAYOUT = widgets.Layout(max_height='600px', max_width='940px', overflow='scroll')
UNRESTRICTED_LAYOUT = widgets.Layout()

DEFAULT_PAGINATION_OPTIONS = [10, 25, 50, 100, -1]
DEFAULT_PAGINATION_MENU = [10, 25, 50, 100, "All"]
opt.order = []
opt.maxBytes = 0
opt.classes = ["display", "hover", "nowrap"]
index_col_js = """
            function (td, cellData, rowData, row, col) {
                $(td).css('font-weight', 'bold');
                $(td).css('font-size', '12px');
            }
            """
cell_style_js = """
            function (td, cellData, rowData, row, col) {
                $(td).css('font-family', 'monospace');
                $(td).css('font-size', '12px');
            }
            """
SPARQL_RESULTS_FILENAME = "sparql_results"
GREMLIN_RESULTS_FILENAME = "gremlin_results"
OC_RESULTS_FILENAME = "oc_results"
LOAD_IDS_FILENAME = "load_ids"
RESULTS_EXPORT_OPTIONS = {
    "columns": ":gt(0)",
    "modifier": {
        "header": False,
        "page": "all",
        "order": "current",
        "search": "applied",
    }
}

JSON_FORMAT = "json"
PANDAS_FORMATS = ["pd", "pandas", "df", "dataframe"]
QUERY_STORE_TO_FORMATS = PANDAS_FORMATS + [JSON_FORMAT]
DT_HTML_CHAR_MAP = {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;"}

logging.basicConfig()
root_logger = logging.getLogger()
logger = logging.getLogger("graph_magic")

DEFAULT_MAX_RESULTS = 1000

GREMLIN_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery,
                            for example: %gremlin_status --cancelQuery --queryId my-query-id'''
SPARQL_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery,
                            for example: %sparql_status --cancelQuery --queryId my-query-id'''
OPENCYPHER_CANCEL_HINT_MSG = '''You must supply a string queryId when using --cancelQuery,
                                for example: %opencypher_status --cancelQuery --queryId my-query-id'''
SEED_MODEL_OPTIONS_PG = ['', 'propertygraph']
SEED_MODEL_OPTIONS = SEED_MODEL_OPTIONS_PG + ['rdf']
SEED_LANGUAGE_OPTIONS_OC = ['', 'opencypher']
SEED_LANGUAGE_OPTIONS_PG = SEED_LANGUAGE_OPTIONS_OC + ['gremlin']
SEED_LANGUAGE_OPTIONS = SEED_LANGUAGE_OPTIONS_PG + ['sparql']
SEED_SOURCE_OPTIONS = ['', 'samples', 'custom']
SEED_NO_DATASETS_FOUND_MSG = "(No datasets available)"
SEED_WIDGET_STYLE = {'description_width': '95px'}

# Tokens as currently defined in TinkerPop 3.7: https://github.com/apache/tinkerpop/blob/3.7-dev/gremlin-util/src/main/java/org/apache/tinkerpop/gremlin/util/ser/SerTokens.java
serializers_map = {
    "MIME_JSON": "application/json",
    "GRAPHSON_V1": "application/vnd.gremlin-v1.0+json",
    "GRAPHSON_V1_UNTYPED": "application/vnd.gremlin-v1.0+json;types=false",
    "GRAPHSON_V2": "application/vnd.gremlin-v2.0+json",
    "GRAPHSON_V2_UNTYPED":  "application/vnd.gremlin-v2.0+json;types=false",
    "GRAPHSON_V3": "application/vnd.gremlin-v3.0+json",
    "GRAPHSON_V3_UNTYPED": "application/vnd.gremlin-v3.0+json;types=false",
    "GRAPHBINARY_V1": "application/vnd.graphbinary-v1.0"
}

DEFAULT_NAMEDGRAPH_URI = "http://aws.amazon.com/neptune/vocab/v01/DefaultNamedGraph"
DEFAULT_BASE_URI = "http://aws.amazon.com/neptune/default"
RDF_LOAD_FORMATS = [FORMAT_NTRIPLE, FORMAT_NQUADS, FORMAT_RDFXML, FORMAT_TURTLE]
BASE_URI_FORMATS = [FORMAT_RDFXML, FORMAT_TURTLE]
DEFAULT_LOAD_CONCURRENCY = 1

MEDIA_TYPE_SPARQL_JSON = "application/sparql-results+json"
MEDIA_TYPE_SPARQL_XML = "application/sparql-results+xml"
MEDIA_TYPE_BINARY_RESULTS_TABLE = "application/x-binary-rdf-results-table"
MEDIA_TYPE_SPARQL_CSV = "text/csv"
MEDIA_TYPE_SPARQL_TSV = "text/tab-separated-values"
MEDIA_TYPE_BOOLEAN = "text/boolean"
MEDIA_TYPE_NQUADS = "application/n-quads"
MEDIA_TYPE_NQUADS_TEXT = "text/x-nquads"
MEDIA_TYPE_RDF_XML = "application/rdf+xml"
MEDIA_TYPE_JSON_LD = "application/ld+json"
MEDIA_TYPE_NTRIPLES = "application/n-triples"
MEDIA_TYPE_NTRIPLES_TEXT = "text/plain"
MEDIA_TYPE_TURTLE = "text/turtle"
MEDIA_TYPE_N3 = "text/n3"
MEDIA_TYPE_TRIX = "application/trix"
MEDIA_TYPE_TRIG = "application/trig"
MEDIA_TYPE_RDF4J_BINARY = "application/x-binary-rdf"

NEPTUNE_RDF_SELECT_FORMATS = [MEDIA_TYPE_SPARQL_JSON, MEDIA_TYPE_SPARQL_XML, MEDIA_TYPE_BINARY_RESULTS_TABLE,
                              MEDIA_TYPE_SPARQL_CSV, MEDIA_TYPE_SPARQL_TSV]
NEPTUNE_RDF_ASK_FORMATS = [MEDIA_TYPE_SPARQL_JSON, MEDIA_TYPE_SPARQL_XML, MEDIA_TYPE_BOOLEAN]
NEPTUNE_RDF_CONSTRUCT_DESCRIBE_FORMATS = [MEDIA_TYPE_SPARQL_JSON, MEDIA_TYPE_NQUADS, MEDIA_TYPE_NQUADS_TEXT,
                                          MEDIA_TYPE_RDF_XML, MEDIA_TYPE_JSON_LD, MEDIA_TYPE_NTRIPLES,
                                          MEDIA_TYPE_NTRIPLES_TEXT, MEDIA_TYPE_TURTLE, MEDIA_TYPE_N3, MEDIA_TYPE_TRIX,
                                          MEDIA_TYPE_TRIG, MEDIA_TYPE_RDF4J_BINARY]

byte_units = {'B': 1, 'KB': 1024, 'MB': 1024 ** 2, 'GB': 1024 ** 3, 'TB': 1024 ** 4}


class QueryMode(Enum):
    DEFAULT = 'query'
    EXPLAIN = 'explain'
    PROFILE = 'profile'
    EMPTY = ''


def generate_seed_error_msg(error_content, file_name, line_index=None):
    error_message = f"Terminated seed due to error in file {file_name}"
    if line_index:
        error_message = error_message + f" at line {line_index}"
    print(error_message)
    print(error_content)


def store_to_ns(key: str, value, ns: dict = None):
    if key == '' or ns is None:
        return

    ns[key] = value


def export_config(export_path: str = "graph_notebook_config.json", config: dict = None, silent: bool = False):
    if export_path == '':
        return

    input_root, input_ext = os.path.splitext(export_path)
    csv_ext = ".json"
    config_file_path = input_root + csv_ext
    try:
        with open(config_file_path, 'w') as cfg_file:
            json.dump(config, cfg_file, indent=4)
        if not silent:
            print(f"\nExported config to file: {config_file_path}")
    except Exception as e:
        print("\nFailed to export config to JSON file.")
        print(e)

    return


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


def oc_results_df(oc_res, oc_res_format: str = None):
    rows_and_columns = opencypher_get_rows_and_columns(oc_res, oc_res_format)
    if rows_and_columns:
        results_df = pd.DataFrame(rows_and_columns['rows']).convert_dtypes()
        results_df = results_df.astype(str)
        results_df = results_df.map(lambda x: encode_html_chars(x))
        col_0_value = range(1, len(results_df) + 1)
        results_df.insert(0, "#", col_0_value)
        for col_index, col_name in enumerate(rows_and_columns['columns']):
            results_df.rename({results_df.columns[col_index + 1]: col_name},
                              axis='columns',
                              inplace=True)
        has_results = True
    else:
        results_df = None
        has_results = False
    return results_df, has_results


def results_per_page_check(results_per_page):
    if results_per_page < 1:
        return 1
    elif results_per_page > 1000:
        return 1000
    else:
        return int(results_per_page)


def generate_pagination_vars(visible_results: int):
    pagination_options = DEFAULT_PAGINATION_OPTIONS.copy()
    pagination_menu = DEFAULT_PAGINATION_MENU.copy()
    visible_results_fixed = results_per_page_check(visible_results)

    if visible_results_fixed not in pagination_options:
        pagination_options.append(visible_results_fixed)
        pagination_options.sort()
        pagination_menu = pagination_options.copy()
        pagination_menu[0] = "All"

    return visible_results_fixed, pagination_options, pagination_menu


def encode_html_chars(result):
    fixed_result = str(result)

    for k, v in iter(DT_HTML_CHAR_MAP.items()):
        fixed_result = fixed_result.replace(k, v)

    return fixed_result


def decode_html_chars(results_df: pd.DataFrame = None) -> pd.DataFrame:
    for k, v in iter(DT_HTML_CHAR_MAP.items()):
        results_df = results_df.map(lambda x: x.replace(v, k))

    return results_df


def process_df_for_store(language: str = None, results_df: pd.DataFrame = None) -> pd.DataFrame:
    if language == 'sparql':
        results_df_final = results_df.drop("#", axis=1)
    elif language == 'gremlin':
        results_df.index = results_df.index - 1
        results_df.columns.name = None
        results_df_final = decode_html_chars(results_df)
    else:
        results_df = results_df.drop("#", axis=1)
        results_df_final = decode_html_chars(results_df)
    return results_df_final


def get_results_for_store(store_type: str = "json", pandas_results: pd.DataFrame = None, json_results: dict = None):
    if store_type in PANDAS_FORMATS:
        return pandas_results
    else:
        if store_type != "json":
            print("Invalid --store-format input. Defaulting to JSON.")
    return json_results


def export_csv_results(export_path: str = "results.csv", results_df: pd.DataFrame = None):
    if export_path == '':
        return

    input_root, input_ext = os.path.splitext(export_path)
    csv_ext = ".csv"
    final_export_path = input_root + csv_ext
    try:
        results_df.to_csv(final_export_path, index=False)
    except OSError:
        print("CSV export failed. Please check that the path provided to --export-to is valid.")

    return


def get_load_ids(neptune_client):
    load_status = neptune_client.load_status()
    load_status.raise_for_status()
    res = load_status.json()
    ids = []
    if 'payload' in res and 'loadIds' in res['payload']:
        ids = res['payload']['loadIds']
    return ids, res


def process_statistics_400(response, is_summary: bool = False, is_analytics: bool = False):
    bad_request_res = json.loads(response.text)
    res_code = bad_request_res['code']
    if res_code == 'StatisticsNotAvailableException':
        print("No statistics found. ", end="")
        if not is_analytics:
            print("Please ensure that auto-generation of DFE statistics is enabled by running '%statistics' and "
                  "checking if 'autoCompute' if set to True. Alternately, you can manually trigger statistics "
                  "generation by running: '%statistics --mode refresh'.")
        return
    elif res_code == "BadRequestException":
        if is_analytics:
            if bad_request_res["message"] == 'Bad route: /summary':
                logger.debug("Encountered bad route exception for Analytics, retrying with legacy statistics endpoint.")
                return 1
        else:
            print("Unable to query the statistics endpoint. Please check that your Neptune instance is of size "
                  "r5.large or greater in order to have DFE statistics enabled.")
            if is_summary and "Statistics is disabled" not in bad_request_res["detailedMessage"]:
                print("\nPlease also note that the Graph Summary API is only available in Neptune engine version "
                      "1.2.1.0 and later.")
        return
    print("Query encountered 400 error, please see below.")
    print(f"\nFull response: {bad_request_res}")
    return


def mcl_to_bytes(mcl):
    using_abb = re.match(r'(\d+)([A-Za-z]+)?', mcl, re.IGNORECASE)
    if using_abb:
        num, unit = using_abb.groups()
        unit = unit.upper() if unit else 'B'
        if unit in byte_units:
            mcl_bytes = int(num) * byte_units[unit]
            return mcl_bytes
    return byte_units['MB'] * 10


# TODO: refactor large magic commands into their own modules like what we do with %neptune_ml
# noinspection PyTypeChecker
@magics_class
class Graph(Magics):
    def __init__(self, shell):
        # You must call the parent constructor
        super(Graph, self).__init__(shell)

        self.neptune_cfg_allowlist = copy(NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        self.neptune_client_endpoint_url = None
        self.graph_notebook_config = generate_default_config()
        try:
            self.config_location = os.getenv('GRAPH_NOTEBOOK_CONFIG', DEFAULT_CONFIG_LOCATION)
            self.client: Client = None
            self.graph_notebook_config = get_config(self.config_location, neptune_hosts=self.neptune_cfg_allowlist)
        except FileNotFoundError:
            print('Could not find a valid configuration. '
                  'Do not forget to validate your settings using %graph_notebook_config.')

        self.max_results = DEFAULT_MAX_RESULTS
        self.graph_notebook_vis_options = OPTIONS_DEFAULT_DIRECTED
        self._generate_client_from_config(self.graph_notebook_config)
        root_logger.setLevel(logging.CRITICAL)
        logger.setLevel(logging.ERROR)

    def _generate_client_from_config(self, config: Configuration):
        if self.client:
            self.client.close()

        is_neptune_host = is_allowed_neptune_host(hostname=config.host, host_allowlist=self.neptune_cfg_allowlist)

        if is_neptune_host:
            builder = ClientBuilder() \
                .with_host(config.host) \
                .with_port(config.port) \
                .with_neptune_service(config.neptune_service) \
                .with_region(config.aws_region) \
                .with_tls(config.ssl) \
                .with_ssl_verify(config.ssl_verify) \
                .with_proxy_host(config.proxy_host) \
                .with_proxy_port(config.proxy_port) \
                .with_sparql_path(config.sparql.path) \
                .with_gremlin_serializer(config.gremlin.message_serializer)
            if config.auth_mode == AuthModeEnum.IAM:
                builder = builder.with_iam(get_session())
            if self.neptune_cfg_allowlist != NEPTUNE_CONFIG_HOST_IDENTIFIERS:
                builder = builder.with_custom_neptune_hosts(self.neptune_cfg_allowlist)
            if self.neptune_client_endpoint_url:
                builder = builder.with_custom_neptune_client_endpoint(self.neptune_client_endpoint_url)
        else:
            builder = ClientBuilder() \
                .with_host(config.host) \
                .with_port(config.port) \
                .with_tls(config.ssl) \
                .with_ssl_verify(config.ssl_verify) \
                .with_sparql_path(config.sparql.path) \
                .with_gremlin_traversal_source(config.gremlin.traversal_source) \
                .with_gremlin_login(config.gremlin.username, config.gremlin.password) \
                .with_gremlin_serializer(config.gremlin.message_serializer) \
                .with_neo4j_login(config.neo4j.username, config.neo4j.password, config.neo4j.auth,
                                  config.neo4j.database)

        self.client = builder.build()

    @magic_variables
    @line_cell_magic
    @needs_local_scope
    @display_exceptions
    def graph_notebook_config(self, line='', cell='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('mode', nargs='?', default='show',
                            help='mode (default=show) [show|reset|silent]')
        parser.add_argument('--export-to', type=str, default='',
                            help='Export the configuration JSON object to the provided file path.')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        args = parser.parse_args(line.split())

        if cell != '':
            data = json.loads(cell)
            config = get_config_from_dict(data, neptune_hosts=self.neptune_cfg_allowlist)
            self.graph_notebook_config = config
            self._generate_client_from_config(config)
            if not args.silent:
                print('Set notebook config to:')
                print(json.dumps(self.graph_notebook_config.to_dict(), indent=4))
        elif args.mode == 'reset':
            self.graph_notebook_config = get_config(self.config_location, neptune_hosts=self.neptune_cfg_allowlist)
            if not args.silent:
                print('Reset notebook config to:')
                print(json.dumps(self.graph_notebook_config.to_dict(), indent=4))
        elif args.mode == 'silent':
            """
            silent option to that our neptune_menu extension can receive json instead
            of python Configuration object
            """
            config_dict = self.graph_notebook_config.to_dict()
            store_to_ns(args.store_to, json.dumps(config_dict, indent=4), local_ns)
            if not args.silent:
                return print(json.dumps(config_dict, indent=4))
        else:
            config_dict = self.graph_notebook_config.to_dict()
            if not args.silent:
                print(json.dumps(config_dict, indent=4))

        store_to_ns(args.store_to, json.dumps(self.graph_notebook_config.to_dict(), indent=4), local_ns)
        export_config(args.export_to, self.graph_notebook_config.to_dict(), args.silent)

        return self.graph_notebook_config

    @line_cell_magic
    def neptune_config_allowlist(self, line='', cell=''):
        parser = argparse.ArgumentParser()
        parser.add_argument('mode', nargs='?', default='add',
                            help='mode (default=add) [add|remove|overwrite|reset]')
        args = parser.parse_args(line.split())

        try:
            cell_new = ast.literal_eval(cell)
            input_type = 'list'
        except:
            cell_new = cell
            input_type = 'string'

        allowlist_modified = True
        if args.mode == 'reset':
            self.neptune_cfg_allowlist = copy(NEPTUNE_CONFIG_HOST_IDENTIFIERS)
        elif cell != '':
            if args.mode == 'add':
                if input_type == 'string':
                    self.neptune_cfg_allowlist.append(cell_new.strip())
                else:
                    self.neptune_cfg_allowlist = list(set(self.neptune_cfg_allowlist) | set(cell_new))
            elif args.mode == 'remove':
                if input_type == 'string':
                    self.neptune_cfg_allowlist.remove(cell_new.strip())
                else:
                    self.neptune_cfg_allowlist = list(set(self.neptune_cfg_allowlist) - set(cell_new))
            elif args.mode == 'overwrite':
                if input_type == 'string':
                    self.neptune_cfg_allowlist = [cell_new.strip()]
                else:
                    self.neptune_cfg_allowlist = cell_new
        else:
            allowlist_modified = False

        if allowlist_modified:
            self._generate_client_from_config(self.graph_notebook_config)
            print(f'Set Neptune config allow list to: {self.neptune_cfg_allowlist}')
        else:
            print(f'Current Neptune config allow list: {self.neptune_cfg_allowlist}')

    @line_magic
    def neptune_client_endpoint(self, line=''):
        ep = line.lower()
        if ep == '':
            if self.neptune_client_endpoint_url:
                print(f'SDK client is using custom endpoint_url: {self.neptune_client_endpoint_url}')
            else:
                print('No custom endpoint_url has been set for the SDK client.')
            return
        elif ep == 'reset':
            self.neptune_client_endpoint_url = None
            print('Reset SDK client to default endpoint_url.')
        else:
            self.neptune_client_endpoint_url = ep
            print(f'Set SDK client to use endpoint_url: {self.neptune_client_endpoint_url}')

        self._generate_client_from_config(self.graph_notebook_config)


    @line_magic
    @neptune_db_only
    def stream_viewer(self, line):
        parser = argparse.ArgumentParser()
        parser.add_argument('language', nargs='?', default=STREAM_PG,
                            help=f'language  (default={STREAM_PG}) [{STREAM_PG}|{STREAM_RDF}]',
                            choices=[STREAM_PG, STREAM_RDF])

        parser.add_argument('--limit', type=int, default=10, help='Maximum number of rows to display at a time')

        args = parser.parse_args(line.split())

        language = args.language
        limit = args.limit
        uri = self.client.get_uri(include_port=True)
        viewer = StreamViewer(self.client, uri, language, limit=limit)
        viewer.show()

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_db_only
    def statistics(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('language', nargs='?', type=str.lower, default="propertygraph",
                            help=f'The language endpoint to use. Valid inputs: {STATISTICS_LANGUAGE_INPUTS}. '
                                 f'Default: propertygraph.',
                            choices=STATISTICS_LANGUAGE_INPUTS)
        parser.add_argument('-m', '--mode', type=str, default='',
                            help=f'The action to perform on the statistics endpoint. Valid inputs: {STATISTICS_MODES}. '
                                 f'Default: `basic` if `--summary` is specified, otherwise `status`.')
        parser.add_argument('--summary', action='store_true', default=False, help="Retrieves the graph summary.")
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='')

        args = parser.parse_args(line.split())
        mode = args.mode

        if not mode:
            mode = 'basic' if args.summary else 'status'
        elif (args.summary and mode not in SUMMARY_MODES) or (not args.summary and mode not in STATISTICS_MODES):
            if mode == 'refresh' and self.client.is_analytics_domain():
                print("Refresh mode is unavailable for Neptune Analytics.")
                return
            err_endpoint_type, err_mode_list, err_default_mode = ("summary", SUMMARY_MODES[1:], "basic summary view") \
                if args.summary else ("statistics", STATISTICS_MODES[1:], "status")
            print(f'Invalid {err_endpoint_type} mode. Please specify one of: {err_mode_list}, '
                  f'or leave blank to retrieve {err_default_mode}.')
            return

        statistics_res = self.client.statistics(args.language, args.summary, mode)
        if statistics_res.status_code == 400:
            if args.summary:
                process_statistics_400(statistics_res)
            else:
                process_statistics_400(statistics_res)
            return
        statistics_res.raise_for_status()
        statistics_res_json = statistics_res.json()
        if not args.silent:
            print(json.dumps(statistics_res_json, indent=2))

        store_to_ns(args.store_to, statistics_res_json, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    def summary(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('language', nargs='?', type=str.lower, default="propertygraph",
                            help=f'The language endpoint to use. Valid inputs: {STATISTICS_LANGUAGE_INPUTS}. '
                                 f'Default: propertygraph.',
                            choices=STATISTICS_LANGUAGE_INPUTS)
        parser.add_argument('--detailed', action='store_true', default=False,
                            help="Toggles the display of structures fields on or off in the output. If not supplied, "
                                 "we will default to the basic summary display mode.")
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='')

        args = parser.parse_args(line.split())
        if args.detailed:
            mode = "detailed"
        else:
            mode = "basic"

        language_ep = args.language
        if self.client.is_analytics_domain():
            is_analytics = True
            if language_ep in STATISTICS_LANGUAGE_INPUTS_SPARQL:
                print("SPARQL is not supported for Neptune Analytics, defaulting to PropertyGraph.")
                language_ep = 'propertygraph'
        else:
            is_analytics = False
        summary_res = self.client.statistics(language_ep, True, mode, is_analytics)
        if summary_res.status_code == 400:
            retry_legacy = process_statistics_400(summary_res, is_summary=True, is_analytics=is_analytics)
            if retry_legacy == 1:
                summary_res = self.client.statistics(language_ep, True, mode, False)
            else:
                return
        summary_res.raise_for_status()
        summary_res_json = summary_res.json()
        if not args.silent:
            print(json.dumps(summary_res_json, indent=2))

        store_to_ns(args.store_to, summary_res_json, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def graph_pg_info(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-m', '--metric', type=str, default='',
                            help=f'Metric to display the count of. If not specified, all available metrics and their '
                                 f'counts will be returned.  Valid inputs: {GRAPH_PG_INFO_METRICS}')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='')

        args = parser.parse_args(line.split())

        if args.metric in GRAPH_PG_INFO_METRICS:
            info_query = f"CALL neptune.graph.pg_info() YIELD metric, count WHERE metric = '{args.metric}' RETURN count"
        else:
            info_query = "CALL neptune.graph.pg_info() YIELD metric, count RETURN metric, count"

        oc_rebuild_args = (f"{f'--store-to {args.store_to} ' if args.store_to else ''}"
                           f"{'--silent' if args.silent else ''}")

        self.handle_opencypher_query(oc_rebuild_args, info_query, local_ns)

    @line_magic
    def graph_notebook_host(self, line):
        if line == '':
            print(f'current host: {self.graph_notebook_config.host}')
            return

        # TODO: we should attempt to make a status call to this host before we set the config to this value.
        self.graph_notebook_config.host = line
        self._generate_client_from_config(self.graph_notebook_config)
        print(f'set host to {self.graph_notebook_config.host}')

    @line_magic
    def graph_notebook_service(self, line):
        if line == '':
            print(f'current service name: {self.graph_notebook_config.neptune_service}')
            return

        self.graph_notebook_config.neptune_service = normalize_service_name(line)
        self._generate_client_from_config(self.graph_notebook_config)
        print(f'set service name to {self.graph_notebook_config.neptune_service}')

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    @neptune_db_only
    def sparql(self, line='', cell='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('query_mode', nargs='?', default='query',
                            help='query mode (default=query) [query|explain]')
        parser.add_argument('--path', '-p', default='',
                            help='prefix path to sparql endpoint. For example, if "foo/bar" were specified, '
                                 'the endpoint called would be host:port/foo/bar')
        parser.add_argument('--expand-all', action='store_true')
        parser.add_argument('--explain-type', type=str.lower, default='dynamic',
                            help=f'Explain mode to use when using the explain query mode. '
                                 f'Expected values: {SPARQL_EXPLAIN_MODES}')
        parser.add_argument('--explain-format', default='text/html', help='response format for explain query mode',
                            choices=['text/csv', 'text/html'])
        parser.add_argument('-m', '--media-type', type=str, default='',
                            help='Response format for SELECT/CONSTRUCT/DESCRIBE queries. See '
                                 'https://docs.aws.amazon.com/neptune/latest/userguide/sparql-media-type-support.html '
                                 'for valid RDF media types supported by Neptune for each query type. Default for '
                                 'Neptune and SELECT queries is application/sparql-results+json, otherwise no format '
                                 'will be specified in the request.')
        parser.add_argument('-g', '--group-by', type=str, default='',
                            help='Property used to group nodes.')
        parser.add_argument('-gr', '--group-by-raw', action='store_true', default=False,
                            help="Group nodes by the raw binding")
        parser.add_argument('-d', '--display-property', type=str, default='',
                            help='Property to display the value of on each node.')
        parser.add_argument('-de', '--edge-display-property', type=str, default='',
                            help='Property to display the value of on each edge.')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each edge tooltip.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex labels, in characters. Default is 10')
        parser.add_argument('-le', '--edge-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--store-format', type=str.lower, default='json',
                            help=f'Configures export type when using --store-to with base query mode. '
                                 f'Valid inputs: {QUERY_STORE_TO_FORMATS}. Default is JSON')
        parser.add_argument('--export-to', type=str, default='',
                            help='Export the base query mode CSV result to the provided file path.')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")
        parser.add_argument('-ct', '--connected-table', action='store_true', default=False,
                            help=f'Dynamically load jQuery and DataTables resources for iTables. For more information, see: '
                                 f'https://mwouts.github.io/itables/quick_start.html#offline-mode-versus-connected-mode')
        parser.add_argument('-r', '--results-per-page', type=int, default=10,
                            help='Specifies how many query results to display per page in the output. Default is 10')
        parser.add_argument('--no-scroll', action='store_true', default=False,
                            help="Display the entire output without a scroll bar.")
        parser.add_argument('--hide-index', action='store_true', default=False,
                            help="Hide the index column numbers when displaying the results.")
        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)

        if args.no_scroll:
            sparql_layout = UNRESTRICTED_LAYOUT
            sparql_scrollY = True
            sparql_scrollCollapse = False
            sparql_paging = False
        else:
            sparql_layout = DEFAULT_LAYOUT
            sparql_scrollY = "475px"
            sparql_scrollCollapse = True
            sparql_paging = True

        if not args.silent:
            tab = widgets.Tab()
            titles = []
            children = []

            first_tab_output = widgets.Output(layout=sparql_layout)
            children.append(first_tab_output)

        path = args.path if args.path != '' else self.graph_notebook_config.sparql.path
        logger.debug(f'using mode={mode}')
        results_df = None
        if mode == QueryMode.EXPLAIN:
            res = self.client.sparql_explain(cell, args.explain_type, args.explain_format, path=path)
            res.raise_for_status()
            explain_bytes = res.content.replace(b'\xcc', b'-')
            explain_bytes = explain_bytes.replace(b'\xb6', b'')
            explain = explain_bytes.decode('utf-8')
            if not args.silent:
                sparql_metadata = build_sparql_metadata_from_query(query_type='explain', res=res)
                titles.append('Explain')
                explain_bytes = explain.encode('ascii', 'ignore')
                base64_str = base64.b64encode(explain_bytes).decode('ascii')
                first_tab_html = sparql_explain_template.render(table=explain,
                                                                link=f"data:text/html;base64,{base64_str}")
        else:
            query_type = get_query_type(cell)

            result_type = str(args.media_type).lower()

            headers = {}

            # Different graph DB services support different sets of results formats, some possibly custom, for each
            # query type. We will only verify if media types are valid for Neptune
            # (https://docs.aws.amazon.com/neptune/latest/userguide/sparql-media-type-support.html). For other
            # databases, we will rely on the HTTP query response to tell if there is an issue with the format.
            if is_allowed_neptune_host(self.graph_notebook_config.host, NEPTUNE_CONFIG_HOST_IDENTIFIERS):
                if (query_type == 'SELECT' and result_type not in NEPTUNE_RDF_SELECT_FORMATS) \
                        or (query_type == 'ASK' and result_type not in NEPTUNE_RDF_ASK_FORMATS) \
                        or (query_type in ['CONSTRUCT', 'DESCRIBE']
                            and result_type not in NEPTUNE_RDF_CONSTRUCT_DESCRIBE_FORMATS) \
                        or result_type == '':
                    if result_type != '':
                        print(f"Invalid media type: {result_type} specified for Neptune {query_type} query. "
                              f"Defaulting to: {MEDIA_TYPE_SPARQL_JSON}.")
                    result_type = MEDIA_TYPE_SPARQL_JSON
                headers = {'Accept': result_type}
            elif result_type == '':
                if query_type == 'SELECT':
                    result_type = MEDIA_TYPE_SPARQL_JSON
                    headers = {'Accept': MEDIA_TYPE_SPARQL_JSON}
            else:
                headers = {'Accept': result_type}

            query_res = self.client.sparql(cell, path=path, headers=headers)

            try:
                query_res.raise_for_status()
            except HTTPError:
                # Catching all 400 response errors here to try and fix possible invalid media type for db in headers.
                # Retry query once with RDF spec default media type.
                result_type = MEDIA_TYPE_SPARQL_JSON if query_type == 'SELECT' else MEDIA_TYPE_NTRIPLES
                query_res = self.client.sparql(cell, path=path, headers={'Accept': result_type})
                query_res.raise_for_status()

            try:
                results = query_res.json()
            except Exception:
                results = query_res.content.decode('utf-8')

            if not args.silent:
                # Assign an empty value so we can always display to table output.
                # We will only add it as a tab if the type of query allows it.
                # Because of this, the table_output will only be displayed on the DOM if the query was of type SELECT.
                first_tab_html = ""
                query_type = get_query_type(cell)
                if result_type != MEDIA_TYPE_SPARQL_JSON:
                    raw_output = widgets.Output(layout=sparql_layout)
                    with raw_output:
                        print(results)
                    children.append(raw_output)
                    titles.append('Raw')
                else:
                    if query_type in ['SELECT', 'CONSTRUCT', 'DESCRIBE']:
                        # TODO: Serialize other result types to SPARQL JSON so we can create table and visualization
                        logger.debug('creating sparql network...')

                        titles.append('Table')

                        sn = SPARQLNetwork(group_by_property=args.group_by,
                                           display_property=args.display_property,
                                           edge_display_property=args.edge_display_property,
                                           tooltip_property=args.tooltip_property,
                                           edge_tooltip_property=args.edge_tooltip_property,
                                           label_max_length=args.label_max_length,
                                           edge_label_max_length=args.edge_label_max_length,
                                           ignore_groups=args.ignore_groups,
                                           expand_all=args.expand_all,
                                           group_by_raw=args.group_by_raw)

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
                            results_df = pd.DataFrame(rows_and_columns['rows']).convert_dtypes()
                            results_df = results_df.astype(str)
                            results_df = results_df.map(lambda x: encode_html_chars(x))
                            results_df.insert(0, "#", range(1, len(results_df) + 1))
                            for col_index, col_name in enumerate(rows_and_columns['columns']):
                                try:
                                    results_df.rename({results_df.columns[col_index + 1]: col_name},
                                                      axis='columns',
                                                      inplace=True)
                                except IndexError:
                                    results_df.insert(col_index + 1, col_name, [])

                        # Handling CONSTRUCT and DESCRIBE on their own because we want to maintain the previous result
                        # pattern of showing a tsv with each line being a result binding in addition to new ones.
                        if query_type == 'CONSTRUCT' or query_type == 'DESCRIBE':
                            lines = []
                            for b in results['results']['bindings']:
                                lines.append(
                                    f'{b["subject"]["value"]}\t{b["predicate"]["value"]}\t{b["object"]["value"]}')
                            raw_output = widgets.Output(layout=sparql_layout)
                            with raw_output:
                                html = sparql_construct_template.render(lines=lines)
                                display(HTML(html))
                            children.append(raw_output)
                            titles.append('Raw')

                    json_output = widgets.Output(layout=sparql_layout)
                    with json_output:
                        print(json.dumps(results, indent=2))
                    children.append(json_output)
                    titles.append('JSON')

                sparql_metadata = build_sparql_metadata_from_query(query_type='query', res=query_res, results=results)

        if not args.silent:
            metadata_output = widgets.Output(layout=sparql_layout)
            children.append(metadata_output)
            titles.append('Query Metadata')

            if first_tab_html == "" and results_df is None:
                tab.children = children[1:]  # the first tab is empty, remove it and proceed
            else:
                tab.children = children

            for i in range(len(titles)):
                tab.set_title(i, titles[i])

            display(tab)

            with metadata_output:
                display(HTML(sparql_metadata.to_html()))

            if results_df is not None:
                with first_tab_output:
                    visible_results, final_pagination_options, final_pagination_menu = generate_pagination_vars(
                        args.results_per_page)
                    sparql_columndefs = [
                        {"type": "string", "targets": "_all"},
                        {"width": "5%", "targets": 0},
                        {"visible": True, "targets": 0},
                        {"searchable": False, "targets": 0},
                        {"className": "nowrap dt-left", "targets": "_all"},
                        {"createdCell": JavascriptFunction(index_col_js), "targets": 0},
                        {"createdCell": JavascriptFunction(cell_style_js), "targets": "_all"}
                    ]
                    if args.hide_index:
                        sparql_columndefs[1]["visible"] = False
                    init_notebook_mode(connected=args.connected_table)
                    show(results_df,
                         connected=args.connected_table,
                         scrollX=True,
                         scrollY=sparql_scrollY,
                         columnDefs=sparql_columndefs,
                         paging=sparql_paging,
                         scrollCollapse=sparql_scrollCollapse,
                         lengthMenu=[final_pagination_options, final_pagination_menu],
                         pageLength=visible_results,
                         buttons=[
                             "pageLength",
                             {
                                 "extend": "copyHtml5",
                                 "text": "Copy",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "csvHtml5",
                                 "title": SPARQL_RESULTS_FILENAME,
                                 "text": "Download CSV",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "excelHtml5",
                                 "filename": SPARQL_RESULTS_FILENAME,
                                 "title": None,
                                 "text": "Download XLSX",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             }
                         ]
                         )
            elif first_tab_html != "":
                with first_tab_output:
                    display(HTML(first_tab_html))

        if args.query_mode == 'explain':
            stored_results = explain
        elif results_df is not None:
            json_results = results
            res_store_type = args.store_format
            res_export_path = args.export_to

            if res_store_type in PANDAS_FORMATS or res_export_path != '':
                results_df = process_df_for_store(language='sparql',
                                                  results_df=results_df)

            stored_results = get_results_for_store(store_type=res_store_type,
                                                   pandas_results=results_df,
                                                   json_results=json_results)

            export_csv_results(export_path=res_export_path,
                               results_df=results_df)
        else:
            stored_results = results

        store_to_ns(args.store_to, stored_results, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_db_only
    def sparql_status(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running SPARQL query. Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true',
                            help='Tells the status command to cancel a query. This parameter does not take a value')
        parser.add_argument('-s', '--silent-cancel', action='store_true',
                            help='If silent_cancel=true then the running query is cancelled and the HTTP response code '
                                 'is 200. If silent_cancel is not present or silent_cancel=false, '
                                 'the query is cancelled with an HTTP 500 status code.')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        if not args.cancelQuery:
            status_res = self.client.sparql_status(query_id=args.queryId)
            status_res.raise_for_status()
            res = status_res.json()
        else:
            if args.queryId == '':
                if not args.silent:
                    print(SPARQL_CANCEL_HINT_MSG)
                return
            else:
                cancel_res = self.client.sparql_cancel(args.queryId, args.silent_cancel)
                cancel_res.raise_for_status()
                res = cancel_res.json()

        store_to_ns(args.store_to, res, local_ns)
        if not args.silent:
            print(json.dumps(res, indent=2))

    @magic_variables
    @cell_magic
    @needs_local_scope
    @display_exceptions
    def gremlin(self, line, cell, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('query_mode', nargs='?', default='query',
                            help='query mode (default=query) [query|explain|profile]')
        parser.add_argument('-cp', '--connection-protocol', type=str.lower, default='',
                            help=f'Neptune endpoints only. Connection protocol to use for connecting to the Gremlin '
                                 f'database - either Websockets or HTTP. Valid inputs: {GREMLIN_PROTOCOL_FORMATS}. '
                                 f'If not specified, defaults to the value of the gremlin.connection_protocol field '
                                 f'in %%graph_notebook_config. Please note that this option has no effect on the '
                                 f'Profile and Explain modes, which must use HTTP.')
        parser.add_argument('--explain-type', type=str.lower, default='dynamic',
                            help=f'Explain mode to use when using the explain query mode. '
                                 f'Accepted values: {GREMLIN_EXPLAIN_MODES}')
        parser.add_argument('-p', '--path-pattern', default='', help='path pattern')
        parser.add_argument('-g', '--group-by', type=str, default='',
                            help='Property used to group nodes (e.g. code, T.region) default is T.label')
        parser.add_argument('-gd', '--group-by-depth', action='store_true', default=False,
                            help="Group nodes based on path hierarchy")
        parser.add_argument('-gr', '--group-by-raw', action='store_true', default=False,
                            help="Group nodes by the raw result")
        parser.add_argument('-d', '--display-property', type=str, default='',
                            help='Property to display the value of on each node, default is T.label')
        parser.add_argument('-de', '--edge-display-property', type=str, default='',
                            help='Property to display the value of on each edge, default is T.label')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the node label value.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each edge tooltip. If not specified, tooltip '
                                 'will default to the edge label value.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex label, in characters. Default is 10')
        parser.add_argument('-le', '--edge-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--store-format', type=str.lower, default='json',
                            help=f'Configures export type when using --store-to with base query mode. '
                                 f'Valid inputs: {QUERY_STORE_TO_FORMATS}. Default is JSON')
        parser.add_argument('--export-to', type=str, default='',
                            help='Export the base query mode CSV result to the provided file path.')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('--profile-no-results', action='store_false', default=True,
                            help='Display only the result count. If not used, all query results will be displayed in '
                                 'the profile report by default.')
        parser.add_argument('--profile-chop', type=int, default=250,
                            help='Property to specify max length of profile results string. Default is 250')
        parser.add_argument('--profile-serializer', type=str, default='GRAPHSON_V3',
                            help='Specify how to serialize results. Allowed values are any of the valid MIME type or '
                                 'TinkerPop driver "Serializers" enum values. Default is GRAPHSON_V3')
        parser.add_argument('--profile-indexOps', action='store_true', default=False,
                            help='Show a detailed report of all index operations.')
        parser.add_argument('--profile-debug', action='store_true', default=False,
                            help='Enable debug mode.')
        parser.add_argument('--profile-misc-args', type=str, default='{}',
                            help='Additional profile options, passed in as a map.')
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")
        parser.add_argument('-ct', '--connected-table', action='store_true', default=False,
                            help=f'Dynamically load jQuery and DataTables resources for iTables. For more information, see: '
                                 f'https://mwouts.github.io/itables/quick_start.html#offline-mode-versus-connected-mode')
        parser.add_argument('-r', '--results-per-page', type=int, default=10,
                            help='Specifies how many query results to display per page in the output. Default is 10')
        parser.add_argument('--no-scroll', action='store_true', default=False,
                            help="Display the entire output without a scroll bar.")
        parser.add_argument('--hide-index', action='store_true', default=False,
                            help="Hide the index column numbers when displaying the results.")
        parser.add_argument('-mcl', '--max-content-length', type=str, default='',
                            help="Specifies maximum size (in bytes) of results that can be returned to the "
                                 "GremlinPython client. Abbreviated memory units (ex.'50MB') are accepted. "
                                 "Default is 10MB")

        args = parser.parse_args(line.split())
        mode = str_to_query_mode(args.query_mode)
        logger.debug(f'Arguments {args}')
        results_df = None

        if args.no_scroll:
            gremlin_layout = UNRESTRICTED_LAYOUT
            gremlin_scrollY = True
            gremlin_scrollCollapse = False
            gremlin_paging = False
        else:
            gremlin_layout = DEFAULT_LAYOUT
            gremlin_scrollY = "475px"
            gremlin_scrollCollapse = True
            gremlin_paging = True

        if not args.silent:
            tab = widgets.Tab()
            children = []
            titles = []

            first_tab_output = widgets.Output(layout=gremlin_layout)
            children.append(first_tab_output)

        mcl_bytes = mcl_to_bytes(args.max_content_length)
        transport_args = {'max_content_length': mcl_bytes}

        if mode == QueryMode.EXPLAIN:
            try:
                res = self.client.gremlin_explain(cell,
                                                  args={'explain.mode': args.explain_type} if args.explain_type else {})
                res.raise_for_status()
            except Exception as e:
                if self.client.is_analytics_domain():
                    print("%%gremlin is incompatible with Neptune Analytics.")
                raise e
            # Replace strikethrough character bytes, can't be encoded to ASCII
            explain_bytes = res.content.replace(b'\xcc', b'-')
            explain_bytes = explain_bytes.replace(b'\xb6', b'')
            query_res = explain_bytes.decode('utf-8')
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='explain', results=query_res, res=res)
                titles.append('Explain')
                if 'Neptune Gremlin Explain' in query_res:
                    explain_bytes = query_res.encode('ascii', 'ignore')
                    base64_str = base64.b64encode(explain_bytes).decode('ascii')
                    first_tab_html = gremlin_explain_profile_template.render(content=query_res,
                                                                             link=f"data:text/html;base64,{base64_str}")
                else:
                    first_tab_html = pre_container_template.render(content='No explain found')
        elif mode == QueryMode.PROFILE:
            logger.debug(f'results: {args.profile_no_results}')
            logger.debug(f'chop: {args.profile_chop}')
            logger.debug(f'serializer: {args.profile_serializer}')
            logger.debug(f'indexOps: {args.profile_indexOps}')
            if args.profile_serializer in serializers_map:
                serializer = serializers_map[args.profile_serializer]
            else:
                serializer = args.profile_serializer
            profile_args = {"profile.results": args.profile_no_results,
                            "profile.chop": args.profile_chop,
                            "profile.serializer": serializer,
                            "profile.indexOps": args.profile_indexOps,
                            "profile.debug": args.profile_debug}
            try:
                profile_misc_args_dict = json.loads(args.profile_misc_args)
                profile_args.update(profile_misc_args_dict)
            except JSONDecodeError:
                print('--profile-misc-args received invalid input, please check that you are passing in a valid '
                      'string representation of a map, ex. "{\'profile.x\':\'true\'}"')
            try:
                res = self.client.gremlin_profile(query=cell, args=profile_args)
                res.raise_for_status()
            except Exception as e:
                if self.client.is_analytics_domain():
                    print("%%gremlin is incompatible with Neptune Analytics.")
                raise e
            profile_bytes = res.content.replace(b'\xcc', b'-')
            profile_bytes = profile_bytes.replace(b'\xb6', b'')
            query_res = profile_bytes.decode('utf-8')
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='profile', results=query_res, res=res)
                titles.append('Profile')
                if 'Neptune Gremlin Profile' in query_res:
                    explain_bytes = query_res.encode('ascii', 'ignore')
                    base64_str = base64.b64encode(explain_bytes).decode('ascii')
                    first_tab_html = gremlin_explain_profile_template.render(content=query_res,
                                                                             link=f"data:text/html;base64,{base64_str}")
                else:
                    first_tab_html = pre_container_template.render(content='No profile found')
        else:
            using_http = False
            query_start = time.time() * 1000  # time.time() returns time in seconds w/high precision; x1000 to get in ms
            if self.client.is_neptune_domain():
                if args.connection_protocol != '':
                    connection_protocol, bad_protocol_input = normalize_protocol_name(args.connection_protocol)
                    if bad_protocol_input:
                        if self.client.is_analytics_domain():
                            connection_protocol = DEFAULT_HTTP_PROTOCOL
                        else:
                            connection_protocol = DEFAULT_WS_PROTOCOL
                        print(f"Connection protocol input is invalid for Neptune, "
                              f"defaulting to {connection_protocol}.")
                    if connection_protocol == DEFAULT_WS_PROTOCOL and \
                            self.graph_notebook_config.gremlin.message_serializer not in GREMLIN_SERIALIZERS_WS:
                        print(f"Serializer is unsupported for GremlinPython client, "
                              f"compatible serializers are: {GREMLIN_SERIALIZERS_WS}")
                        print("Defaulting to HTTP protocol.")
                        connection_protocol = DEFAULT_HTTP_PROTOCOL
                else:
                    connection_protocol = self.graph_notebook_config.gremlin.connection_protocol
                try:
                    if connection_protocol == DEFAULT_HTTP_PROTOCOL:
                        using_http = True
                        message_serializer = self.graph_notebook_config.gremlin.message_serializer
                        message_serializer_mime = GREMLIN_SERIALIZERS_CLASS_TO_MIME_MAP[message_serializer]
                        query_res_http = self.client.gremlin_http_query(cell, headers={
                            'Accept': message_serializer_mime})
                        query_res_http.raise_for_status()
                        try:
                            query_res_http_json = query_res_http.json()
                        except JSONDecodeError:
                            query_res_fixed = repair_json(query_res_http.text)
                            query_res_http_json = json.loads(query_res_fixed)
                        query_res = query_res_http_json['result']['data']
                    else:
                        query_res = self.client.gremlin_query(cell, transport_args=transport_args)
                except Exception as e:
                    if self.client.is_analytics_domain():
                        print("%%gremlin is incompatible with Neptune Analytics.")
                    raise e
            else:
                try:
                    query_res = self.client.gremlin_query(cell, transport_args=transport_args)
                except Exception as e:
                    store_to_ns(args.store_to, {'error': str(e)[5:]}, local_ns)  # remove the leading error code.
                    raise e
            query_time = time.time() * 1000 - query_start
            if not args.silent:
                gremlin_metadata = build_gremlin_metadata_from_query(query_type='query', results=query_res,
                                                                     query_time=query_time)
                titles.append('Console')

                gremlin_network = None
                try:
                    logger.debug(f'groupby: {args.group_by}')
                    logger.debug(f'display_property: {args.display_property}')
                    logger.debug(f'edge_display_property: {args.edge_display_property}')
                    logger.debug(f'label_max_length: {args.label_max_length}')
                    logger.debug(f'ignore_groups: {args.ignore_groups}')
                    gn = GremlinNetwork(group_by_property=args.group_by,
                                        display_property=args.display_property,
                                        group_by_raw=args.group_by_raw,
                                        group_by_depth=args.group_by_depth,
                                        edge_display_property=args.edge_display_property,
                                        tooltip_property=args.tooltip_property,
                                        edge_tooltip_property=args.edge_tooltip_property,
                                        label_max_length=args.label_max_length,
                                        edge_label_max_length=args.edge_label_max_length,
                                        ignore_groups=args.ignore_groups,
                                        using_http=using_http)

                    if using_http and 'path()' in cell and query_res:
                        first_path = query_res[0]
                        if isinstance(first_path, dict) and first_path.keys() == {'labels', 'objects'}:
                            query_res_to_path_type = []
                            for path in query_res:
                                new_path_list = path['objects']
                                new_path = Path(labels=[], objects=new_path_list)
                                query_res_to_path_type.append(new_path)
                            query_res = query_res_to_path_type

                    if args.path_pattern == '':
                        gn.add_results(query_res, is_http=using_http)
                    else:
                        pattern = parse_pattern_list_str(args.path_pattern)
                        gn.add_results_with_pattern(query_res, pattern)
                    gremlin_network = gn
                    logger.debug(f'number of nodes is {len(gn.graph.nodes)}')
                except ValueError as value_error:
                    logger.debug(
                        f'Unable to create graph network from result due to error: {value_error}. '
                        f'Skipping from result set.')
                if gremlin_network and len(gremlin_network.graph.nodes) > 0:
                    try:
                        self.graph_notebook_vis_options['physics']['disablePhysicsAfterInitialSimulation'] \
                            = args.stop_physics
                        self.graph_notebook_vis_options['physics']['simulationDuration'] = args.simulation_duration
                        f = Force(network=gremlin_network, options=self.graph_notebook_vis_options)
                        titles.append('Graph')
                        children.append(f)
                        logger.debug('added gremlin network to tabs')
                    except Exception as force_error:
                        logger.debug(
                            f'Unable to render visualization from graph network due to error: {force_error}. Skipping.')

                # Check if we can access the CDNs required by itables library.
                # If not, then render our own HTML template.

                mixed_results = False
                if query_res:
                    # If the results set contains multiple datatypes, and the first result is a map or list, we need to
                    # insert a temp string first element, or we will get an error when creating the Dataframe.
                    first_res_type = type(query_res[0])
                    if first_res_type in [dict, list, set] and len(query_res) > 1:
                        if not all(isinstance(x, first_res_type) for x in query_res[1:]):
                            mixed_results = True
                            query_res_deque = deque(query_res)
                            query_res_deque.appendleft('x')
                            query_res = list(query_res_deque)

                results_df = pd.DataFrame(query_res).convert_dtypes()
                # Checking for created indices instead of the df itself here, as df.empty will still return True when
                # only empty maps/lists are present in the data.
                if not results_df.index.empty:
                    query_res_reformat = []
                    for result in query_res:
                        fixed_result = encode_html_chars(result)
                        query_res_reformat.append([fixed_result])
                    query_res_reformat.append([{'__DUMMY_KEY__': ['DUMMY_VALUE']}])
                    results_df = pd.DataFrame(query_res_reformat)
                    if mixed_results:
                        results_df = results_df[1:]
                    results_df.drop(results_df.index[-1], inplace=True)
                results_df.insert(0, "#", range(1, len(results_df) + 1))
                if len(results_df.columns) == 2 and int(results_df.columns[1]) == 0:
                    results_df.rename({results_df.columns[1]: 'Result'}, axis='columns', inplace=True)
                else:
                    results_df.insert(1, "Result", [])
                results_df.set_index('#', inplace=True)
                results_df.columns.name = results_df.index.name
                results_df.index.name = None

        if not args.silent:
            metadata_output = widgets.Output(layout=gremlin_layout)
            titles.append('Query Metadata')
            children.append(metadata_output)

            tab.children = children
            for i in range(len(titles)):
                tab.set_title(i, titles[i])
            display(tab)

            with metadata_output:
                display(HTML(gremlin_metadata.to_html()))

            with first_tab_output:
                if mode == QueryMode.DEFAULT:
                    visible_results, final_pagination_options, final_pagination_menu = generate_pagination_vars(
                        args.results_per_page)
                    gremlin_columndefs = [
                        {"type": "string", "targets": "_all"},
                        {"width": "5%", "targets": 0},
                        {"visible": True, "targets": 0},
                        {"searchable": False, "targets": 0},
                        {"minWidth": "95%", "targets": 1},
                        {"className": "nowrap dt-left", "targets": "_all"},
                        {"createdCell": JavascriptFunction(index_col_js), "targets": 0},
                        {"createdCell": JavascriptFunction(cell_style_js), "targets": "_all"},
                    ]
                    if args.hide_index:
                        gremlin_columndefs[1]["visible"] = False
                    init_notebook_mode(connected=args.connected_table)
                    show(results_df,
                         connected=args.connected_table,
                         scrollX=True,
                         scrollY=gremlin_scrollY,
                         columnDefs=gremlin_columndefs,
                         paging=gremlin_paging,
                         scrollCollapse=gremlin_scrollCollapse,
                         lengthMenu=[final_pagination_options, final_pagination_menu],
                         pageLength=visible_results,
                         buttons=[
                             "pageLength",
                             {
                                 "extend": "copyHtml5",
                                 "text": "Copy",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "csvHtml5",
                                 "title": GREMLIN_RESULTS_FILENAME,
                                 "text": "Download CSV",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "excelHtml5",
                                 "filename": GREMLIN_RESULTS_FILENAME,
                                 "title": None,
                                 "text": "Download XLSX",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             }
                         ]
                         )
                else:  # Explain/Profile
                    display(HTML(first_tab_html))

        if mode == QueryMode.DEFAULT and results_df is not None:
            json_results = query_res
            res_store_type = args.store_format
            res_export_path = args.export_to

            if res_store_type in PANDAS_FORMATS or res_export_path != '':
                results_df = process_df_for_store(language='gremlin',
                                                  results_df=results_df)

            stored_results = get_results_for_store(store_type=res_store_type,
                                                   pandas_results=results_df,
                                                   json_results=json_results)

            export_csv_results(export_path=res_export_path,
                               results_df=results_df)
        else:
            stored_results = query_res

        store_to_ns(args.store_to, stored_results, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_db_only
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
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        if not args.cancelQuery:
            status_res = self.client.gremlin_status(query_id=args.queryId, include_waiting=args.includeWaiting)
            status_res.raise_for_status()
            res = status_res.json()
        else:
            if args.queryId == '':
                if not args.silent:
                    print(GREMLIN_CANCEL_HINT_MSG)
                return
            else:
                cancel_res = self.client.gremlin_cancel(args.queryId)
                cancel_res.raise_for_status()
                res = cancel_res.json()
        if not args.silent:
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
    @needs_local_scope
    @display_exceptions
    def status(self, line='', local_ns: dict = None):
        if self.client.is_analytics_domain():
            logger.info(f'Redirected %status call to %get_graph.')
            self.get_graph(line, local_ns)
            return
        logger.info(f'calling for status on endpoint {self.graph_notebook_config.host}')
        parser = argparse.ArgumentParser()
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        status_res = self.client.status()
        status_res.raise_for_status()
        try:
            res = status_res.json()
            logger.info(f'got the json format response {res}')
            store_to_ns(args.store_to, res, local_ns)
            if not args.silent:
                return res
        except ValueError:
            logger.info(f'got the HTML format response {status_res.text}')
            store_to_ns(args.store_to, status_res.text, local_ns)
            if not args.silent:
                if "blazegraph&trade; by SYSTAP" in status_res.text:
                    print("For more information on the status of your Blazegraph cluster, please visit: ")
                    print()
                    print(f'http://{self.graph_notebook_config.host}:{self.graph_notebook_config.port}'
                          f'/blazegraph/#status')
                    print()
                return status_res

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def get_graph(self, line='', local_ns: dict = None):
        logger.info(f'calling for status on endpoint {self.graph_notebook_config.host}')
        parser = argparse.ArgumentParser()
        parser.add_argument('--include-metadata', action='store_true', default=False,
                            help="Display the response metadata if it is available.")
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        try:
            graph_id = self.client.get_graph_id()
            res = self.client.get_graph(graph_id=graph_id)
            if not args.include_metadata:
                res.pop('ResponseMetadata', None)
            if not args.silent:
                print(json.dumps(res, indent=2, default=str))
            store_to_ns(args.store_to, res, local_ns)
        except Exception as e:
            if not args.silent:
                print("Encountered an error when attempting to retrieve graph status:\n")
                print(e)
            store_to_ns(args.store_to, e, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def create_graph_snapshot(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--snapshot-name', type=str, default='',
                            help="The name for the snapshot. Must start with a letter, contain only alphanumeric "
                                 "characters or hyphens, and not end with or contain two consecutive hyphens. If not "
                                 "supplied, this will default to the format 'snapshot-[graph_id]-[timestamp]'.")
        parser.add_argument('-t', '--tags', type=str, default='',
                            help='Metadata tags to attach to the graph snapshot. Pass a dict in string format, '
                                 'ex. {"tag1":"foo","tag2":"bar"}')
        parser.add_argument('--include-metadata', action='store_true', default=False,
                            help="Display the response metadata if it is available.")
        parser.add_argument('--silent', action='store_true', default=False,
                            help="Display no output.")
        parser.add_argument('--store-to', type=str, default='',
                            help='Store query result to this variable')
        args = parser.parse_args(line.split())

        graph_id = self.client.get_graph_id()

        if args.snapshot_name:
            snapshot_name = args.snapshot_name
        else:
            snapshot_name = generate_snapshot_name(graph_id)

        if args.tags:
            try:
                tags = json.loads(args.tags)
            except JSONDecodeError as e:
                print("Tags map is improperly formatted, skipping.")
                tags = None
                logger.error(e)
        else:
            tags = None

        try:
            res = self.client.create_graph_snapshot(graph_id=graph_id, snapshot_name=snapshot_name, tags=tags)
            if not args.include_metadata:
                res.pop('ResponseMetadata', None)
            if not args.silent:
                print("Successfully submitted snapshot request:")
                print(json.dumps(res, indent=2, default=str))
            store_to_ns(args.store_to, res, local_ns)
        except Exception as e:
            if not args.silent:
                print("Encountered an error when attempting to create the graph snapshot:\n")
                print(e)
            store_to_ns(args.store_to, e, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def get_import_task(self, line='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('-ti', '--task-identifier', type=str, default='',
                            help="The unique identifier of an import task.")
        parser.add_argument('--include-metadata', action='store_true', default=False,
                            help="Display the response metadata if it is available.")
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        task_id_regex = "t-[a-z0-9]{10}"
        if args.task_identifier == '':
            print("Please provide an import task ID using the -ti or --task-identifier parameter.")
            return
        if not re.match(fr"^{task_id_regex}$", args.task_identifier):
            print(f"Import task ID must satisfy the regular expression pattern: {task_id_regex}")
            return

        try:
            res = self.client.get_import_task(task_id=args.task_identifier)
            if not args.include_metadata:
                res.pop('ResponseMetadata', None)
            if not args.silent:
                print(json.dumps(res, indent=2, default=str))
            store_to_ns(args.store_to, res, local_ns)
        except Exception as e:
            if not args.silent:
                if "ResourceNotFoundException" in str(e):
                    print(f"Unable to import task with ID: {args.task_identifier}")
                else:
                    print("Encountered an error when attempting to retrieve the specified import task:\n")
                    print(e)
            store_to_ns(args.store_to, e, local_ns)

    @line_magic
    @needs_local_scope
    @display_exceptions
    def reset(self, line, local_ns: dict = None, service: str = None):
        logger.info(f'calling system endpoint {self.client.host}')
        parser = argparse.ArgumentParser()
        parser.add_argument('-g', '--generate-token', action='store_true',
                            help='Generate token for database reset. Database only.')
        parser.add_argument('-t', '--token', default='',
                            help='Perform database reset with given token. Database only.')
        parser.add_argument('-s', '--snapshot', action='store_true', default=False,
                            help='Creates a final graph snapshot before the graph data is deleted. Analytics only.')
        parser.add_argument('-y', '--yes', action='store_true',
                            help='Skip the prompt and perform reset.')
        parser.add_argument('-m', '--max-status-retries', type=int, default=10,
                            help='Specifies how many times we should attempt to check if the database reset has '
                                 'completed, in intervals of 5 seconds. Default is 10')
        args = parser.parse_args(line.split())
        generate_token = args.generate_token
        skip_prompt = args.yes
        snapshot = args.snapshot
        if not service:
            service = self.graph_notebook_config.neptune_service
        if service == NEPTUNE_DB_SERVICE_NAME:
            using_db = True
            graph_id = None
            message_instance = "cluster"
        else:
            using_db = False
            graph_id = self.client.get_graph_id()
            message_instance = "graph"
        max_status_retries = args.max_status_retries if args.max_status_retries > 0 else 1
        if not using_db or (generate_token is False and args.token == ''):
            if skip_prompt:
                if using_db:
                    initiate_res = self.client.initiate_reset()
                    initiate_res.raise_for_status()
                    res = initiate_res.json()
                    token = res['payload']['token']

                    perform_reset_res = self.client.perform_reset(token)
                    perform_reset_res.raise_for_status()
                    logger.info(f'got the response {res}')
                    res = perform_reset_res.json()
                    return res
                else:
                    if snapshot:
                        print(f"Snapshot creation is currently unsupported for prompt skip mode. Please use "
                              f"%create_graph_snapshot to take a snapshot prior to attempting graph reset.")
                        return
                    try:
                        res = self.client.reset_graph(graph_id=graph_id, snapshot=False)
                        print(
                            f"ResetGraph call submitted successfully for graph ID [{graph_id}]. "
                            f"Please note that the graph may take several minutes to become available again, "
                            f"You can use %status or %get_graph to check the current status of the graph.\n")
                        print(json.dumps(res, indent=2, default=str))
                    except Exception as e:
                        print("Received an error when attempting graph reset:")
                        print(e)
                    return

            output = widgets.Output()
            confirm_source = f'Are you sure you want to delete all the data in your {message_instance}?'
            confirm_label = widgets.Label(confirm_source)
            confirm_text_hbox = widgets.HBox([confirm_label])
            confirm_check_box = widgets.Checkbox(
                value=False,
                disabled=False,
                indent=False,
                description=f'I acknowledge that upon deletion the {message_instance} data will no longer be available.',
                layout=widgets.Layout(width='600px', margin='5px 5px 5px 5px')
            )
            button_delete = widgets.Button(description="Delete")
            button_cancel = widgets.Button(description="Cancel")
            button_hbox = widgets.HBox([button_delete, button_cancel])

            if using_db:
                display(confirm_text_hbox, confirm_check_box, button_hbox, output)
            else:
                snapshot_source = f'OPTIONAL: Create a final graph snapshot before reset?'
                snapshot_label = widgets.Label(snapshot_source)
                snapshot_text_hbox = widgets.HBox([snapshot_label])
                snapshot_check_box = widgets.Checkbox(
                    value=snapshot,
                    disabled=False,
                    indent=False,
                    description=f'Yes',
                    layout=widgets.Layout(width='600px', margin='5px 5px 5px 5px')
                )

                display(confirm_text_hbox, confirm_check_box,
                        snapshot_text_hbox, snapshot_check_box,
                        button_hbox, output)

            def on_button_delete_clicked(b):
                if using_db:
                    initiate_res = self.client.initiate_reset()
                    initiate_res.raise_for_status()
                    result = initiate_res.json()

                confirm_text_hbox.close()
                confirm_check_box.close()
                if not using_db:
                    snapshot_text_hbox.close()
                    snapshot_check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()

                if not confirm_check_box.value:
                    with output:
                        print('Reset confirmation checkbox is not checked.')
                    return

                if using_db:
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
                            print('Database reset failed, please see exception below for details.')
                            print(result)
                            logger.error(result)
                        return
                else:
                    if snapshot_check_box.value:
                        snapshot_name = generate_snapshot_name(graph_id)
                        try:
                            self.client.create_graph_snapshot(graph_id=graph_id, snapshot_name=snapshot_name)
                        except Exception as e:
                            with output:
                                print("Graph snapshot creation request failed, please see the exception below.")
                                print(f"\n{e}")
                            logger.error(e)
                            return

                        snapshot_static_output = widgets.Output()
                        snapshot_progress_output = widgets.Output()
                        snapshot_hbox = widgets.HBox([snapshot_static_output, snapshot_progress_output])
                        with snapshot_static_output:
                            print("Creating graph snapshot, this may take several minutes")
                        with output:
                            display(snapshot_hbox)

                        poll_interval = 5
                        poll_index = 0
                        status_ellipses = ""
                        while True:
                            snapshot_progress_output.clear_output()
                            poll_index += 1
                            if poll_index > poll_interval:
                                snapshot_progress_output.clear_output()
                                status_ellipses = ""
                                interval_check_response = self.client.get_graph(graph_id=graph_id)
                                current_status = interval_check_response["status"]
                                if current_status == 'AVAILABLE':
                                    snapshot_static_output.clear_output()
                                    with snapshot_static_output:
                                        print(f'Snapshot creation complete, starting reset.')
                                        break
                                elif current_status != 'SNAPSHOTTING':
                                    snapshot_static_output.clear_output()
                                    with snapshot_static_output:
                                        print(f'Something went wrong with the snapshot creation.')
                                        return
                                poll_index = 0
                            else:
                                status_ellipses += "."
                                with snapshot_progress_output:
                                    print(status_ellipses)
                            time.sleep(1)
                        snapshot_progress_output.close()
                    try:
                        result = self.client.reset_graph(graph_id=graph_id, snapshot=False)
                    except Exception as e:
                        with output:
                            print("Failed to initiate graph reset, please see the exception below.")
                            print(f"\n{e}")
                        logger.error(e)
                        return

                retry = max_status_retries
                poll_interval = 5
                interval_output = widgets.Output()
                job_status_output = widgets.Output()
                status_hbox = widgets.HBox([interval_output])
                vbox = widgets.VBox([status_hbox, job_status_output])
                with output:
                    display(vbox)

                last_poll_time = time.time()
                interval_check_response = {}
                new_interval = True
                while retry > 0:
                    time_elapsed = int(time.time() - last_poll_time)
                    time_remaining = poll_interval - time_elapsed
                    interval_output.clear_output()
                    if time_elapsed > poll_interval:
                        with interval_output:
                            print('Checking status...')
                        job_status_output.clear_output()
                        new_interval = True
                        try:
                            retry -= 1
                            if using_db:
                                status_res = self.client.status()
                                status_res.raise_for_status()
                                interval_check_response = status_res.json()
                            else:
                                interval_check_response = self.client.get_graph(graph_id=graph_id)
                        except Exception as e:
                            # Exception is expected when database is resetting, continue waiting
                            if using_db:
                                with job_status_output:
                                    last_poll_time = time.time()
                                    time.sleep(1)
                                    continue
                            else:
                                print('Graph status check failed, something went wrong.')
                                print(e)
                                logger.error(e)
                                return
                        job_status_output.clear_output()
                        with job_status_output:
                            done_status = 'healthy' if using_db else 'AVAILABLE'
                            if interval_check_response["status"] == done_status:
                                interval_output.close()
                                print(f'{message_instance.capitalize()} has been reset.')
                                return
                        last_poll_time = time.time()
                    else:
                        if new_interval:
                            with job_status_output:
                                display_html(HTML(loading_wheel_html))
                            new_interval = False
                        with interval_output:
                            print(f'Checking status in {time_remaining} seconds')
                    time.sleep(1)
                with (output):
                    job_status_output.clear_output()
                    interval_output.close()
                    total_status_wait = max_status_retries * poll_interval
                    final_status = interval_check_response.get("status")
                    if using_db:
                        if final_status != 'healthy':
                            print(f"Could not retrieve the status of the reset operation within the allotted time of "
                                  f"{total_status_wait} seconds. If the database is not in healthy status after at "
                                  f"least 1 minute, please try the operation again or reboot the cluster.")
                            print(result)
                    else:
                        if final_status == 'RESETTING':
                            print(f"Reset is still in progress after the allotted wait time of {total_status_wait} "
                                  f"seconds, halting status checks. Please use %status to verify when your graph is "
                                  f"available again.")
                            print(f"\nTIP: For future resets, you can use the --max-status-retries option to extend "
                                  f"the total wait duration.")
                        elif final_status != 'AVAILABLE':
                            print(f"Graph is not in AVAILABLE or RESETTING status after the allotted time of "
                                  f"{total_status_wait} seconds, something went wrong. "
                                  f"Current status is {final_status}, see below for details.")
                            print(result)

            def on_button_cancel_clicked(b):
                confirm_text_hbox.close()
                confirm_check_box.close()
                if not using_db:
                    snapshot_text_hbox.close()
                    snapshot_check_box.close()
                button_delete.close()
                button_cancel.close()
                button_hbox.close()
                with output:
                    print(f'{message_instance.capitalize()} reset operation has been canceled.')

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
    @neptune_db_only
    def db_reset(self, line, local_ns: dict = None):
        return self.reset(line, local_ns, service=NEPTUNE_DB_SERVICE_NAME)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def graph_reset(self, line, local_ns: dict = None):
        self.reset(line, local_ns, service=NEPTUNE_ANALYTICS_SERVICE_NAME)

    @line_magic
    @needs_local_scope
    @display_exceptions
    @neptune_graph_only
    def reset_graph(self, line, local_ns: dict = None):
        self.reset(line, local_ns, service=NEPTUNE_ANALYTICS_SERVICE_NAME)

    @magic_variables
    @line_magic
    @needs_local_scope
    @display_exceptions
    def load(self, line='', local_ns: dict = None):
        if self.client.is_analytics_domain():
            load_type = ANALYTICS_LOAD_TYPES[0]
            load_formats = VALID_INCREMENTAL_FORMATS
        else:
            load_type = DB_LOAD_TYPES[0]
            load_formats = VALID_BULK_FORMATS

        # TODO: change widgets to let any arbitrary inputs be added by users
        parser = argparse.ArgumentParser()
        parser.add_argument('-s', '--source', default='s3://')
        try:
            parser.add_argument('-l', '--loader-arn', default=self.graph_notebook_config.load_from_s3_arn)
        except AttributeError:
            print(f"Missing required configuration option 'load_from_s3_arn'. Please ensure that you have provided a "
                  "valid Neptune cluster endpoint URI in the 'host' field of %graph_notebook_config.")
            return
        parser.add_argument('-f', '--format', choices=load_formats, default=FORMAT_CSV)
        parser.add_argument('-p', '--parallelism', choices=PARALLELISM_OPTIONS, default=PARALLELISM_HIGH)
        try:
            parser.add_argument('-r', '--region', default=self.graph_notebook_config.aws_region)
        except AttributeError:
            print("Missing required configuration option 'aws_region'. Please ensure that you have provided a "
                  "valid Neptune cluster endpoint URI in the 'host' field of %graph_notebook_config.")
            return
        parser.add_argument('--no-fail-on-error', action='store_true', default=False)
        parser.add_argument('--update-single-cardinality', action='store_true', default=True)
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--run', action='store_true', default=False)
        parser.add_argument('-m', '--mode', choices=LOAD_JOB_MODES, default=MODE_AUTO)
        parser.add_argument('-q', '--queue-request', action='store_true', default=False)
        parser.add_argument('-d', '--dependencies', action='append', default=[])
        parser.add_argument('-e', '--no-edge-ids', action='store_true', default=False)
        parser.add_argument('-c', '--concurrency', type=int, default=1)
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
            options=load_formats,
            value=args.format,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        ids_hbox_visibility = 'none'
        gremlin_parser_options_hbox_visibility = 'none'
        named_graph_hbox_visibility = 'none'
        base_uri_hbox_visibility = 'none'
        concurrency_hbox_visibility = 'none'

        if load_type == 'incremental':
            concurrency_hbox_visibility = 'flex'
        else:
            if source_format.value.lower() == FORMAT_CSV:
                gremlin_parser_options_hbox_visibility = 'flex'
            elif source_format.value.lower() == FORMAT_OPENCYPHER:
                ids_hbox_visibility = 'flex'
            elif source_format.value.lower() in RDF_LOAD_FORMATS:
                named_graph_hbox_visibility = 'flex'
                if source_format.value.lower() in BASE_URI_FORMATS:
                    base_uri_hbox_visibility = 'flex'

        region_box = widgets.Text(
            value=args.region,
            placeholder=args.region,
            disabled=False,
            layout=widgets.Layout(width=widget_width)
        )

        fail_on_error = widgets.Dropdown(
            options=['TRUE', 'FALSE'],
            value=str(not args.no_fail_on_error).upper(),
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

        concurrency = widgets.BoundedIntText(
            value=str(args.concurrency),
            placeholder=1,
            min=1,
            max=2 ** 16,
            disabled=False,
            layout=widgets.Layout(display=concurrency_hbox_visibility,
                                  width=widget_width)
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

        concurrency_hbox_label = widgets.Label('Concurrency:',
                                               layout=widgets.Layout(width=label_width,
                                                                     display=concurrency_hbox_visibility,
                                                                     justify_content="flex-end"))

        concurrency_hbox = widgets.HBox([concurrency_hbox_label, concurrency])

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

        basic_load_boxes = [source_hbox, source_format_hbox, region_hbox, fail_hbox]
        # load arguments for Analytics incremental load
        incremental_load_boxes = [concurrency_hbox]
        # load arguments for Neptune bulk load
        bulk_load_boxes = [arn_hbox, mode_hbox, parallelism_hbox, cardinality_hbox,
                           queue_hbox, dep_hbox, ids_hbox, allow_empty_strings_hbox,
                           named_graph_uri_hbox, base_uri_hbox, poll_status_hbox]
        submit_load_boxes = [button, output]

        if load_type == 'incremental':
            display_boxes = basic_load_boxes + incremental_load_boxes + submit_load_boxes
        else:
            display_boxes = basic_load_boxes + bulk_load_boxes + submit_load_boxes

        display(*display_boxes)

        def on_button_clicked(b):
            source_hbox.children = (source_hbox_label, source,)
            arn_hbox.children = (arn_hbox_label, arn,)
            source_format_hbox.children = (format_hbox_label, source_format,)
            allow_empty_strings.children = (allow_empty_strings_hbox_label, allow_empty_strings,)
            named_graph_uri_hbox.children = (named_graph_uri_hbox_label, named_graph_uri,)
            base_uri_hbox.children = (base_uri_hbox_label, base_uri,)
            dep_hbox.children = (dep_hbox_label, dependencies,)
            concurrency_hbox.children = (concurrency_hbox_label, concurrency,)

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

            if load_type == 'bulk':
                if not arn.value.startswith('arn:aws') and source.value.startswith(
                        "s3://"):  # only do this validation if we are using an s3 bucket.
                    validated = False
                    arn_validation_label = widgets.HTML('<p style="color:red;">Load ARN must start with "arn:aws"</p>')
                    arn_hbox.children += (arn_validation_label,)
                dependencies_list = list(filter(None, dependencies.value.split('\n')))
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
                    'region': region_box.value
                }

                if load_type == 'incremental':
                    incremental_load_kwargs = {
                        'source': source.value,
                        'format': source_format.value,
                        'concurrency': concurrency.value
                    }
                    kwargs.update(incremental_load_kwargs)
                else:
                    bulk_load_kwargs = {
                        'mode': mode.value,
                        'parallelism': parallelism.value,
                        'updateSingleCardinalityProperties': update_single_cardinality.value,
                        'queueRequest': queue_request.value,
                        'parserConfiguration': {}
                    }

                    if dependencies:
                        bulk_load_kwargs['dependencies'] = dependencies_list

                    if source_format.value.lower() == FORMAT_OPENCYPHER:
                        bulk_load_kwargs['userProvidedEdgeIds'] = user_provided_edge_ids.value
                    elif source_format.value.lower() == FORMAT_CSV:
                        if allow_empty_strings.value == 'TRUE':
                            bulk_load_kwargs['parserConfiguration']['allowEmptyStrings'] = True
                    elif source_format.value.lower() in RDF_LOAD_FORMATS:
                        if named_graph_uri.value:
                            bulk_load_kwargs['parserConfiguration']['namedGraphUri'] = named_graph_uri.value
                        if base_uri.value and source_format.value.lower() in BASE_URI_FORMATS:
                            bulk_load_kwargs['parserConfiguration']['baseUri'] = base_uri.value

                    kwargs.update(bulk_load_kwargs)

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
                concurrency_hbox.close()
                button.close()

                load_submit_status_output = widgets.Output()
                load_submit_hbox = widgets.HBox([load_submit_status_output])
                with output:
                    display(load_submit_hbox)
                with load_submit_status_output:
                    print(f"{load_type.capitalize()} load request submitted, waiting for response...")
                    display_html(HTML(loading_wheel_html))
                try:
                    if load_type == 'incremental':
                        load_oc_params = '{'
                        for param, value in kwargs.items():
                            value_substr = str(value) if (isinstance(value, int) or param == 'failOnError') \
                                else '"' + value + '"'
                            next_param = param + ': ' + value_substr
                            load_oc_params += next_param
                            if param == 'concurrency':
                                if source_format.value == FORMAT_NTRIPLE:
                                    load_oc_params += ', blankNodeHandling: "convertToIri"'
                                load_oc_params += '}'
                            else:
                                load_oc_params += ', '
                        load_oc_query = f"CALL neptune.load({load_oc_params})"
                        oc_load = self.client.opencypher_http(load_oc_query)
                    else:
                        if source.value.startswith("s3://"):
                            load_res = self.client.load(str(source_exp), source_format.value, arn.value, **kwargs)
                        else:
                            load_res = self.client.load(str(source_exp), source_format.value, **kwargs)
                except Exception as e:
                    load_submit_status_output.clear_output()
                    with output:
                        print(f"Failed to submit {load_type.capitalize()} load request.")
                        logger.error(e)
                    return
                load_submit_status_output.clear_output()

                if load_type == 'incremental':
                    oc_load.raise_for_status()
                    load_result = oc_load.json()
                    store_to_ns(args.store_to, load_result, local_ns)
                    with output:
                        print("Load completed.\n")
                        print(json.dumps(load_result, indent=2))
                else:
                    try:
                        load_res.raise_for_status()
                    except Exception as e:
                        # Ignore failure to retrieve status, we handle missing status below.
                        pass
                    load_result = load_res.json()
                    store_to_ns(args.store_to, load_result, local_ns)

                    if 'status' not in load_result or load_result['status'] != '200 OK':
                        with output:
                            print('Something went wrong.')
                            logger.error(load_result)
                        return

                    if poll_status.value == 'FALSE':
                        start_msg_label = widgets.Label(f'Load started successfully!')
                        polling_msg_label = widgets.Label(
                            f'You can run "%load_status {load_result["payload"]["loadId"]}" '
                            f'in another cell to check the current status of your bulk load.')
                        start_msg_hbox = widgets.HBox([start_msg_label])
                        polling_msg_hbox = widgets.HBox([polling_msg_label])
                        vbox = widgets.VBox([start_msg_hbox, polling_msg_hbox])
                        with output:
                            display(vbox)
                    else:
                        poll_interval = 5
                        load_id_label = widgets.Label(f'Load ID: {load_result["payload"]["loadId"]}')
                        interval_output = widgets.Output()
                        job_status_output = widgets.Output()
                        load_id_hbox = widgets.HBox([load_id_label])
                        status_hbox = widgets.HBox([interval_output])
                        vbox = widgets.VBox([load_id_hbox, status_hbox, job_status_output])
                        with output:
                            display(vbox)

                        last_poll_time = time.time()
                        new_interval = True
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
                                new_interval = True
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
                                    # parse status & execution_time differently for Analytics and NeptuneDB
                                    overall_status = \
                                        interval_check_response["payload"][
                                            "status"] if self.client.is_analytics_domain() \
                                            else interval_check_response["payload"]["overallStatus"]["status"]
                                    total_time_spent = \
                                        interval_check_response["payload"][
                                            "timeElapsedSeconds"] if self.client.is_analytics_domain() \
                                            else interval_check_response["payload"]["overallStatus"]["totalTimeSpent"]
                                    print(f'Overall Status: {overall_status}')
                                    if overall_status in FINAL_LOAD_STATUSES:
                                        execution_time = total_time_spent
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
                                if new_interval:
                                    with job_status_output:
                                        display_html(HTML(loading_wheel_html))
                                    new_interval = False
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
    @neptune_db_only
    def load_ids(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('--details', action='store_true', default=False,
                            help="Display status details for each load job. Most recent jobs are listed first.")
        parser.add_argument('--limit', type=int, default=maxsize,
                            help='If --details is True, only return the x most recent load job statuses. '
                                 'Defaults to sys.maxsize.')
        parser.add_argument('-ct', '--connected-table', action='store_true', default=False,
                            help=f'Dynamically load jQuery and DataTables resources for iTables. For more information, see: '
                                 f'https://mwouts.github.io/itables/quick_start.html#offline-mode-versus-connected-mode')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='')
        args = parser.parse_args(line.split())

        ids, res = get_load_ids(self.client)

        if not ids:
            labels = [widgets.Label(value="No load IDs found.")]
        else:
            if args.details:
                res = {}
                res_table = []
                for index, label_id in enumerate(ids):
                    load_status_res = self.client.load_status(label_id)
                    load_status_res.raise_for_status()
                    this_res = load_status_res.json()

                    res[label_id] = this_res

                    res_row = {}
                    res_row["loadId"] = label_id
                    res_row["status"] = this_res["payload"]["overallStatus"]["status"]
                    res_row.update(this_res["payload"]["overallStatus"])
                    if "feedCount" in this_res["payload"]:
                        res_row["feedCount"] = this_res["payload"]["feedCount"]
                    else:
                        res_row["feedCount"] = "N/A"
                    res_table.append(res_row)
                    if index + 1 == args.limit:
                        break
                if not args.silent:
                    tab = widgets.Tab()
                    table_output = widgets.Output(layout=DEFAULT_LAYOUT)
                    raw_output = widgets.Output(layout=DEFAULT_LAYOUT)
                    tab.children = [table_output, raw_output]
                    tab.set_title(0, 'Table')
                    tab.set_title(1, 'Raw')
                    display(tab)

                    results_df = pd.DataFrame(res_table)
                    results_df.insert(0, "#", range(1, len(results_df) + 1))

                    with table_output:
                        init_notebook_mode(connected=args.connected_table)
                        show(results_df,
                             connected=args.connected_table,
                             scrollX=True,
                             scrollY="475px",
                             columnDefs=[
                                 {"width": "5%", "targets": 0},
                                 {"className": "nowrap dt-left", "targets": "_all"},
                                 {"createdCell": JavascriptFunction(index_col_js), "targets": 0},
                                 {"createdCell": JavascriptFunction(cell_style_js), "targets": "_all"}
                             ],
                             paging=True,
                             scrollCollapse=True,
                             lengthMenu=[DEFAULT_PAGINATION_OPTIONS, DEFAULT_PAGINATION_MENU],
                             pageLength=10,
                             buttons=[
                                 "pageLength",
                                 {
                                     "extend": "copyHtml5",
                                     "text": "Copy",
                                     "exportOptions": RESULTS_EXPORT_OPTIONS
                                 },
                                 {
                                     "extend": "csvHtml5",
                                     "title": LOAD_IDS_FILENAME,
                                     "text": "Download CSV",
                                     "exportOptions": RESULTS_EXPORT_OPTIONS
                                 },
                                 {
                                     "extend": "excelHtml5",
                                     "filename": LOAD_IDS_FILENAME,
                                     "title": None,
                                     "text": "Download XLSX",
                                     "exportOptions": RESULTS_EXPORT_OPTIONS
                                 }
                             ]
                             )

                    with raw_output:
                        print(json.dumps(res, indent=2))
            else:
                labels = [widgets.Label(value=label_id) for label_id in ids]

        if not args.details and not args.silent:
            vbox = widgets.VBox(labels)
            display(vbox)

        store_to_ns(args.store_to, res, local_ns)

    @line_magic
    @display_exceptions
    @needs_local_scope
    def load_status(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('load_id', default='', help='loader id to check status for')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
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
        if not args.silent:
            print(json.dumps(res, indent=2))

        store_to_ns(args.store_to, res, local_ns)

    @line_magic
    @display_exceptions
    @needs_local_scope
    @neptune_db_only
    def cancel_load(self, line, local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('load_id', nargs="?", default='', help='loader id to check status for')
        parser.add_argument('--all-in-queue', action='store_true', default=False,
                            help="Cancel all load jobs with LOAD_IN_QUEUE status.")
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='')
        args = parser.parse_args(line.split())

        loads_to_cancel = []
        raw_res = {}
        print_res = {}

        if args.load_id:
            loads_to_cancel.append(args.load_id)
        elif args.all_in_queue:
            all_job_ids = get_load_ids(self.client)[0]
            for job_id in all_job_ids:
                load_status_res = self.client.load_status(job_id)
                load_status_res.raise_for_status()
                this_res = load_status_res.json()
                if this_res["payload"]["overallStatus"]["status"] == "LOAD_IN_QUEUE":
                    loads_to_cancel.append(job_id)
        else:
            print("Please specify either a single load_id or --all-in-queue.")
            return

        for load_id in loads_to_cancel:
            cancel_res = self.client.cancel_load(load_id)
            cancel_res.raise_for_status()
            res = cancel_res.json()
            if res:
                raw_res[load_id] = res
                print_res[load_id] = 'Cancelled successfully.'
            else:
                raw_res[load_id] = 'Something went wrong cancelling bulk load job.'
                print_res[load_id] = 'Something went wrong cancelling bulk load job.'

        if not args.silent:
            if print_res:
                print(json.dumps(print_res, indent=2))
            else:
                print("No cancellable load jobs were found.")

        store_to_ns(args.store_to, raw_res, local_ns)

    @line_magic
    @display_exceptions
    @needs_local_scope
    def seed(self, line, local_ns: dict = None):
        """
        Provides a way to bulk insert data to your endpoint via Gremlin, openCypher, or SPARQL queries. Via the form
        generated by running %seed with no arguments, you can do either of the following:

        a) select a data model (property-graph or RDF), then choose from among a number of different sample data sets
        that Neptune provides.

        b) select a query language to load with, then provide a path to a local file with insert queries,
        or a directory containing multiple of these files.
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('--model', type=str.lower, default='',
                            help='Specifies what data model you would like to load for. '
                                 'Accepted values: property_graph, rdf')
        parser.add_argument('--language', type=str.lower, default='',
                            help='Specifies what language you would like to load for. '
                                 'Accepted values: gremlin, sparql, opencypher')
        parser.add_argument('--dataset', type=str, default='',
                            help='Specifies what sample dataset you would like to load.')
        parser.add_argument('--source', type=str, default='',
                            help='Specifies the full path to a local file or directory that you would like to '
                                 'load from.')
        parser.add_argument('-f', '--full-file-query', action='store_true', default=False,
                            help='Read all content of a file as a single query, instead of per line')
        # TODO: Gremlin api paths are not yet supported.
        parser.add_argument('--path', '-p', default=SPARQL_ACTION,
                            help='prefix path to query endpoint. For example, "foo/bar". '
                                 'The queried path would then be host:port/foo/bar for sparql seed commands')
        parser.add_argument('--run', action='store_true')
        parser.add_argument('--ignore-errors', action='store_true', default=False,
                            help='Continue loading from the seed file on failure of any individual query.')
        args = parser.parse_args(line.split())

        output = widgets.Output()
        progress_output = widgets.Output()
        source_dropdown = widgets.Dropdown(
            options=SEED_SOURCE_OPTIONS,
            description='Source type:',
            disabled=False,
            style=SEED_WIDGET_STYLE
        )

        if self.client.is_analytics_domain():
            model_options = SEED_MODEL_OPTIONS_PG
            custom_language_options = SEED_LANGUAGE_OPTIONS_OC
            samples_pg_language_options = SEED_LANGUAGE_OPTIONS_OC
        else:
            model_options = SEED_MODEL_OPTIONS
            custom_language_options = SEED_LANGUAGE_OPTIONS
            samples_pg_language_options = SEED_LANGUAGE_OPTIONS_PG

        model_dropdown = widgets.Dropdown(
            options=model_options,
            description='Data model:',
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        custom_language_dropdown = widgets.Dropdown(
            options=custom_language_options,
            description='Language:',
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        samples_pg_language_dropdown = widgets.Dropdown(
            options=samples_pg_language_options,
            description='Language:',
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        data_set_drop_down = widgets.Dropdown(
            description='Data set:',
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        fullfile_option_dropdown = widgets.Dropdown(
            description='Full File Query:',
            options=[True, False],
            value=args.full_file_query,
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        location_option_dropdown = widgets.Dropdown(
            description='Location:',
            options=['Local', 'S3'],
            value='Local',
            disabled=False,
            layout=widgets.Layout(display='none'),
            style=SEED_WIDGET_STYLE
        )

        seed_file_location_text = widgets.Text(
            description='Source:',
            placeholder='path/to/seedfiles/directory',
            disabled=False,
            style=SEED_WIDGET_STYLE
        )

        seed_file_location = FileChooser()
        seed_file_location.layout.display = 'none'

        seed_file_location_text_hbox = widgets.HBox([seed_file_location_text])

        submit_button = widgets.Button(description="Submit")
        model_dropdown.layout.visibility = 'hidden'
        custom_language_dropdown.layout.visibility = 'hidden'
        samples_pg_language_dropdown.layout.visibility = 'hidden'
        data_set_drop_down.layout.visibility = 'hidden'
        fullfile_option_dropdown.layout.visibility = 'hidden'
        location_option_dropdown.layout.visibility = 'hidden'
        seed_file_location_text_hbox.layout.visibility = 'hidden'
        seed_file_location.layout.visibility = 'hidden'
        submit_button.layout.visibility = 'hidden'

        def hide_all_widgets():
            location_option_dropdown.layout.visibility = 'hidden'
            location_option_dropdown.layout.display = 'none'
            seed_file_location_text_hbox.layout.visibility = 'hidden'
            seed_file_location_text_hbox.layout.display = 'none'
            custom_language_dropdown.layout.visibility = 'hidden'
            custom_language_dropdown.layout.display = 'none'
            samples_pg_language_dropdown.layout.visibility = 'hidden'
            samples_pg_language_dropdown.layout.display = 'none'
            fullfile_option_dropdown.layout.visibility = 'hidden'
            fullfile_option_dropdown.layout.display = 'none'
            seed_file_location.layout.visibility = 'hidden'
            seed_file_location.layout.display = 'none'
            seed_file_location_text_hbox.layout.visibility = 'hidden'
            seed_file_location_text_hbox.layout.display = 'none'
            model_dropdown.layout.visibility = 'hidden'
            model_dropdown.layout.display = 'none'
            data_set_drop_down.layout.visibility = 'hidden'
            data_set_drop_down.layout.display = 'none'
            submit_button.layout.visibility = 'hidden'

        def on_source_value_change(change):
            hide_all_widgets()
            selected_source = change['new']
            if selected_source == 'custom':
                custom_language_dropdown.layout.visibility = 'visible'
                custom_language_dropdown.layout.display = 'flex'
                location_option_dropdown.layout.visibility = 'visible'
                location_option_dropdown.layout.display = 'flex'
                if custom_language_dropdown.value:
                    if custom_language_dropdown.value != 'sparql':
                        fullfile_option_dropdown.layout.visibility = 'visible'
                        fullfile_option_dropdown.layout.display = 'flex'
                # If textbox has a value, OR we are loading from S3, display textbox instead of the filepicker
                if seed_file_location_text.value or location_option_dropdown.value == 'S3':
                    seed_file_location_text_hbox.layout.visibility = 'visible'
                    seed_file_location_text_hbox.layout.display = 'flex'
                elif seed_file_location.value or location_option_dropdown.value == 'Local':
                    seed_file_location.layout.visibility = 'visible'
                    seed_file_location.layout.display = 'flex'
                if custom_language_dropdown.value \
                        and (seed_file_location_text.value or
                             (seed_file_location.value and location_option_dropdown.value == 'Local')):
                    submit_button.layout.visibility = 'visible'
            elif selected_source == 'samples':
                custom_language_dropdown.layout.visibility = 'hidden'
                custom_language_dropdown.layout.display = 'none'
                fullfile_option_dropdown.layout.visibility = 'hidden'
                fullfile_option_dropdown.layout.display = 'none'
                seed_file_location.layout.visibility = 'hidden'
                seed_file_location.layout.display = 'none'
                model_dropdown.layout.visibility = 'visible'
                model_dropdown.layout.display = 'flex'
                if model_dropdown.value:
                    show_dataset = False
                    if model_dropdown.value == 'propertygraph':
                        samples_pg_language_dropdown.layout.visibility = 'visible'
                        samples_pg_language_dropdown.layout.display = 'flex'
                        if samples_pg_language_dropdown.value != '':
                            show_dataset = True
                    else:
                        samples_pg_language_dropdown.layout.visibility = 'hidden'
                        samples_pg_language_dropdown.layout.display = 'none'
                        show_dataset = True
                    if show_dataset:
                        data_set_drop_down.layout.visibility = 'visible'
                        data_set_drop_down.layout.display = 'flex'
                        if data_set_drop_down.value and data_set_drop_down.value != SEED_NO_DATASETS_FOUND_MSG:
                            submit_button.layout.visibility = 'visible'
            else:
                custom_language_dropdown.layout.visibility = 'hidden'
                custom_language_dropdown.layout.display = 'none'
                samples_pg_language_dropdown.layout.visibility = 'hidden'
                samples_pg_language_dropdown.layout.display = 'none'
                fullfile_option_dropdown.layout.visibility = 'hidden'
                fullfile_option_dropdown.layout.display = 'none'
                seed_file_location.layout.visibility = 'hidden'
                seed_file_location.layout.display = 'none'
                seed_file_location_text.layout.visibility = 'hidden'
                seed_file_location_text.layout.display = 'none'
                model_dropdown.layout.visibility = 'hidden'
                model_dropdown.layout.display = 'none'
                data_set_drop_down.layout.visibility = 'hidden'
                data_set_drop_down.layout.display = 'none'
            return

        def change_datasets_widget(samples_lang):
            data_sets = get_data_sets(samples_lang)
            if data_sets:
                data_sets.sort()
                data_set_drop_down.options = [ds for ds in data_sets if
                                              ds != '__pycache__']  # being extra sure that we aren't passing __pycache__.
                data_set_drop_down.layout.visibility = 'visible'
                data_set_drop_down.layout.display = 'flex'
                submit_button.layout.visibility = 'visible'
            else:
                if samples_lang:
                    data_set_drop_down.options = [SEED_NO_DATASETS_FOUND_MSG]
                    data_set_drop_down.layout.visibility = 'visible'
                    data_set_drop_down.layout.display = 'flex'
                else:
                    data_set_drop_down.layout.visibility = 'hidden'
                    data_set_drop_down.layout.display = 'none'
                submit_button.layout.visibility = 'hidden'
            return

        def on_model_value_change(change):
            selected_model = change['new']
            samples_language = ''
            if selected_model == 'propertygraph':
                samples_pg_language_dropdown.layout.visibility = 'visible'
                samples_pg_language_dropdown.layout.display = 'flex'
                if samples_pg_language_dropdown.value != '':
                    samples_language = samples_pg_language_dropdown.value
            else:
                samples_pg_language_dropdown.layout.visibility = 'hidden'
                samples_pg_language_dropdown.layout.display = 'none'
                if selected_model == 'rdf':
                    samples_language = 'sparql'
            change_datasets_widget(samples_language)
            return

        def on_dataset_value_change(change):
            selected_dataset = change['new']
            if not selected_dataset:
                submit_button.layout.visibility = 'hidden'
            return

        def on_samples_pg_language_value_change(change):
            selected_pg_language = change['new']
            change_datasets_widget(selected_pg_language)
            return

        def on_custom_language_value_change(change):
            # Preserve the value/state of the text/selector widget if it's already rendered
            # Otherwise, display the default selector widget (file browser)
            selected_language = change['new']
            if selected_language != 'sparql':
                fullfile_option_dropdown.layout.visibility = 'visible'
                fullfile_option_dropdown.layout.display = 'flex'
            else:
                fullfile_option_dropdown.layout.visibility = 'hidden'
                fullfile_option_dropdown.layout.display = 'none'
            if not seed_file_location_text.value and seed_file_location_text_hbox.layout.visibility == 'hidden':
                seed_file_location.layout.visibility = 'visible'
                seed_file_location.layout.display = 'flex'
                submit_button.layout.visibility = 'visible'
            return

        def on_location_value_change(change):
            selected_location = change['new']
            if selected_location == 'Local' and not seed_file_location_text.value:
                seed_file_location_text_hbox.layout.visibility = 'hidden'
                seed_file_location_text_hbox.layout.display = 'none'
                seed_file_location.layout.visibility = 'visible'
                seed_file_location.layout.display = 'flex'
            else:
                seed_file_location.layout.visibility = 'hidden'
                seed_file_location.layout.display = 'none'
                seed_file_location_text_hbox.layout.visibility = 'visible'
                seed_file_location_text_hbox.layout.display = 'flex'
            return

        def on_seedfile_text_value_change(change):
            if seed_file_location_text.value:
                submit_button.layout.visibility = 'visible'
            else:
                submit_button.layout.visibility = 'hidden'
            return

        def on_seedfile_select_value_change(change):
            if seed_file_location.value:
                submit_button.layout.visibility = 'visible'
            else:
                submit_button.layout.visibility = 'hidden'
            return

        def disable_seed_widgets():
            source_dropdown.disabled = True
            model_dropdown.disabled = True
            custom_language_dropdown.disabled = True
            samples_pg_language_dropdown.disabled = True
            data_set_drop_down.disabled = True
            fullfile_option_dropdown.disabled = True
            location_option_dropdown.disabled = True
            seed_file_location_text.disabled = True
            seed_file_location.disabled = True
            submit_button.close()

        def process_gremlin_query_line(query_line, line_index, q):
            # Return a state here, with indication of any other variable states that need changing.
            #  return 0 = continue
            #  return 1 = continue, set any_errors_flag = True, error_count += 1
            #  return 2 = progress.close() and return, set any_errors_flag = True, error_count += 1
            if not query_line:
                logger.debug(f"Skipped blank query at line {line_index + 1} in seed file {q['name']}")
                return 0
            try:
                self.client.gremlin_query(query_line)
                return 0
            except GremlinServerError as gremlinEx:
                try:
                    error = json.loads(gremlinEx.args[0][5:])  # remove the leading error code.
                    content = json.dumps(error, indent=2)
                except Exception:
                    content = {
                        'error': gremlinEx
                    }
                logger.debug(f"GremlinServerError at line {line_index + 1} in seed file {q['name']}")
                logger.debug(content)
                if args.ignore_errors:
                    return 1
                else:
                    with output:
                        generate_seed_error_msg(content, q['name'], line_index + 1)
                    return 2
            except Exception as e:
                content = {
                    'error': e
                }
                logger.debug(f"Exception at line {line_index + 1} in seed file {q['name']}")
                logger.debug(content)
                if args.ignore_errors:
                    return 1
                else:
                    with output:
                        generate_seed_error_msg(content, q['name'], line_index + 1)
                    return 2

        def process_cypher_query_line(query_line, line_index, q):
            if not query_line:
                logger.debug(f"Skipped blank query at line {line_index + 1} in seed file {q['name']}")
                return 0
            try:
                cypher_res = self.client.opencypher_http(query_line)
                cypher_res.raise_for_status()
                return 0
            except HTTPError as httpEx:
                try:
                    error = json.loads(httpEx.response.content.decode('utf-8'))
                    content = json.dumps(error, indent=2)
                except Exception:
                    content = {
                        'error': httpEx
                    }
                logger.debug(content)
                if args.ignore_errors:
                    return 1
                else:
                    with output:
                        generate_seed_error_msg(content, q['name'])
                    return 2
            except Exception as ex:
                content = {
                    'error': str(ex)
                }
                logger.error(content)
                if args.ignore_errors:
                    return 1
                else:
                    with output:
                        generate_seed_error_msg(content, q['name'])
                    return 2

        def on_button_clicked(b=None):
            seed_file_location_text_hbox.children = (seed_file_location_text,)
            filename = None
            if source_dropdown.value == 'samples':
                data_set = data_set_drop_down.value.lower()
                fullfile_query = False
            else:
                if seed_file_location_text.value:
                    stall_with_warning = False
                    if location_option_dropdown.value == 'S3' and not (seed_file_location_text.value.startswith('s3://')
                                                                       and len(seed_file_location_text.value) > 7):
                        seed_file_location_text_validation_label = widgets.HTML(
                            '<p style="color:red;">S3 source URI must start with s3://</p>')
                        stall_with_warning = True
                    elif location_option_dropdown.value == 'Local' \
                            and not seed_file_location_text.value.startswith('/'):
                        seed_file_location_text_validation_label = widgets.HTML(
                            '<p style="color:red;">Local source URI must be a valid file path</p>')
                        stall_with_warning = True
                    if stall_with_warning:
                        seed_file_location_text_validation_label.style = DescriptionStyle(color='red')
                        seed_file_location_text_hbox.children += (seed_file_location_text_validation_label,)
                        return
                    filename = seed_file_location_text.value
                elif seed_file_location.value:
                    filename = seed_file_location.value
                else:
                    return
                data_set = filename
                fullfile_query = fullfile_option_dropdown.value
            disable_seed_widgets()
            if custom_language_dropdown.value and filename:
                model = normalize_model_name(custom_language_dropdown.value)
                seeding_language = normalize_language_name(custom_language_dropdown.value)
            else:
                model = normalize_model_name(model_dropdown.value)
                seeding_language = 'sparql' if model == 'rdf' else samples_pg_language_dropdown.value
            with output:
                print(f'Loading data set {data_set} for {seeding_language}')
            queries = get_queries(seeding_language, data_set, source_dropdown.value)
            if queries:
                if len(queries) < 1:
                    with output:
                        print('Did not find any queries for the given dataset')
                    return
            else:
                with output:
                    print('Query retrieval from files terminated with errors.')
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

            error_count = 0
            any_errors_flag = False
            for q in queries:
                with output:
                    print(f'{progress.value}/{len(queries)}:\t{q["name"]}')
                if model == 'rdf':
                    try:
                        self.client.sparql(q['content'], path=args.path)
                    except HTTPError as httpEx:
                        # attempt to turn response into json
                        try:
                            error = json.loads(httpEx.response.content.decode('utf-8'))
                            content = json.dumps(error, indent=2)
                        except Exception:
                            any_errors_flag = True
                            error_count += 1
                            content = {
                                'error': httpEx
                            }
                        logger.debug(content)
                        if args.ignore_errors:
                            progress.value += 1
                            continue
                        else:
                            with output:
                                generate_seed_error_msg(content, q['name'])
                            progress.close()
                            return
                    except Exception as ex:
                        any_errors_flag = True
                        error_count += 1
                        content = {
                            'error': str(ex)
                        }
                        logger.error(content)
                        if args.ignore_errors:
                            progress.value += 1
                            continue
                        else:
                            with output:
                                generate_seed_error_msg(content, q['name'])
                            progress.close()
                            return
                else:  # gremlin and cypher
                    # treat entire file content as one query
                    if fullfile_query or (source_dropdown.value == 'samples' and 'full' in q['name']):
                        if seeding_language == 'opencypher':
                            query_status = process_cypher_query_line(q['content'], 0, q)
                        else:
                            query_status = process_gremlin_query_line(q['content'], 0, q)
                        if query_status == 2:
                            progress.close()
                            return
                        else:
                            if query_status == 1:
                                any_errors_flag = True
                                error_count += 1
                                progress.value += 1
                                continue
                    else:  # treat each line as its own query
                        for line_index, query_line in enumerate(q['content'].splitlines()):
                            if seeding_language == 'opencypher':
                                query_status = process_cypher_query_line(query_line, line_index, q)
                            else:
                                query_status = process_gremlin_query_line(query_line, line_index, q)
                            if query_status == 2:
                                progress.close()
                                return
                            else:
                                if query_status == 1:
                                    any_errors_flag = True
                                    error_count += 1

                progress.value += 1
            # Sleep for two seconds so the user sees the progress bar complete
            time.sleep(2)
            progress.close()
            with output:
                print('Done.')
                if any_errors_flag:
                    print(f'\n{error_count} individual queries were skipped due to errors. For more '
                          f'information, please rerun the query with debug logs enabled (%enable_debug).')
            return

        submit_button.on_click(on_button_clicked)
        source_dropdown.observe(on_source_value_change, names='value')
        model_dropdown.observe(on_model_value_change, names='value')
        data_set_drop_down.observe(on_dataset_value_change, names='value')
        custom_language_dropdown.observe(on_custom_language_value_change, names='value')
        samples_pg_language_dropdown.observe(on_samples_pg_language_value_change, names='value')
        location_option_dropdown.observe(on_location_value_change, names='value')
        seed_file_location_text.observe(on_seedfile_text_value_change, names='value')
        seed_file_location.observe(on_seedfile_select_value_change, names='value')

        display(source_dropdown, model_dropdown, custom_language_dropdown, samples_pg_language_dropdown,
                data_set_drop_down, fullfile_option_dropdown, location_option_dropdown, seed_file_location,
                seed_file_location_text_hbox, submit_button, progress_output, output)

        if (args.model != '' or args.language != '') and args.source == '':
            source_dropdown.value = 'samples'
            normed_model = normalize_model_name(args.model)
            normed_language = normalize_language_name(args.language)
            selected_model = None
            selected_language = None
            if normed_model != '' and normed_model in SEED_MODEL_OPTIONS:
                if normed_model == 'propertygraph':
                    selected_model = 'propertygraph'
                    if normed_language in ['gremlin', 'opencypher']:
                        selected_language = normed_language
                    elif normed_language == '':
                        selected_language = 'gremlin'
                else:
                    selected_model = 'rdf'
                    selected_language = 'sparql'
            elif normed_language != '' and normed_language in SEED_LANGUAGE_OPTIONS:
                if normed_language == 'sparql':
                    selected_model = 'rdf'
                    selected_language = 'sparql'
                else:
                    selected_model = 'propertygraph'
                    selected_language = normed_language
            if selected_model:
                model_dropdown.value = selected_model
                if selected_language:
                    if selected_language != 'sparql':
                        samples_pg_language_dropdown.value = selected_language
                    if args.dataset != '' and args.dataset in data_set_drop_down.options:
                        data_set_drop_down.value = args.dataset.lower()
                        if args.run:
                            on_button_clicked()
        elif args.source != '' or args.language != '':
            source_dropdown.value = 'custom'
            valid_language_value = False
            language = normalize_language_name(args.language)
            if language != '' and language in SEED_LANGUAGE_OPTIONS:
                custom_language_dropdown.value = language
                valid_language_value = True
            if args.source != '':
                seed_file_location_text.value = args.source
                seed_file_location_text_hbox.layout.visibility = 'visible'
                seed_file_location_text_hbox.layout.display = 'flex'
                if seed_file_location_text.value.startswith('s3://'):
                    location_option_dropdown.value = 'S3'
                location_option_dropdown.layout.visibility = 'visible'
                location_option_dropdown.layout.display = 'flex'
                seed_file_location.layout.visibility = 'hidden'
                seed_file_location.layout.display = 'none'
            if seed_file_location_text.value and valid_language_value and args.run:
                on_button_clicked()

    @line_magic
    def enable_debug(self, line):
        logger.setLevel(logging.DEBUG)
        root_logger.setLevel(logging.ERROR)

    @line_magic
    def disable_debug(self, line):
        logger.setLevel(logging.ERROR)
        root_logger.setLevel(logging.CRITICAL)

    @line_magic
    @needs_local_scope
    def toggle_traceback(self, line, local_ns: dict = None):
        show_traceback_ns_var = 'graph_notebook_show_traceback'
        try:
            show_traceback = local_ns[show_traceback_ns_var]
            if not isinstance(show_traceback, bool):
                show_traceback = False
            else:
                show_traceback = not show_traceback
        except KeyError:
            show_traceback = True

        print(f"Display of tracebacks from magics is toggled {'ON' if show_traceback else 'OFF'}.")
        store_to_ns(show_traceback_ns_var, show_traceback, local_ns)

    @line_magic
    def graph_notebook_version(self, line):
        print(graph_notebook.__version__)

    @magic_variables
    @line_cell_magic
    @display_exceptions
    @needs_local_scope
    def graph_notebook_vis_options(self, line='', cell='', local_ns: dict = None):
        parser = argparse.ArgumentParser()
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store visualization settings to this variable')
        parser.add_argument('--load-from', type=str, default='', help='load visualization settings from this variable')
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

        if cell == '' and not args.load_from:
            if not args.silent:
                print(json.dumps(self.graph_notebook_vis_options, indent=2))
        else:
            try:
                if args.load_from:
                    try:
                        options_raw = local_ns[args.load_from]
                        if isinstance(options_raw, dict):
                            options_raw = json.dumps(options_raw)
                        options_dict = json.loads(options_raw)
                    except KeyError:
                        print(f"Unable to load visualization settings, variable [{args.load_from}] does not exist in "
                              f"the local namespace.")
                        return
                else:
                    options_dict = json.loads(cell)
            except (JSONDecodeError, TypeError) as e:
                print(f"Unable to load visualization settings, variable [{args.load_from}] is not in valid JSON "
                      f"format:\n")
                print(e)
                return
            self.graph_notebook_vis_options = vis_options_merge(self.graph_notebook_vis_options, options_dict)
            print("Visualization settings successfully changed to:\n")
            print(json.dumps(self.graph_notebook_vis_options, indent=2))

        store_to_ns(args.store_to, json.dumps(self.graph_notebook_vis_options, indent=2), local_ns)

    @magic_variables
    @line_cell_magic
    @display_exceptions
    @needs_local_scope
    @neptune_db_only
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
        parser.add_argument('-pc', '--plan-cache', type=str.lower, default='auto',
                            help=f'Specifies the plan cache mode to use. '
                                 f'Accepted values: {OPENCYPHER_PLAN_CACHE_MODES}')
        parser.add_argument('-qt', '--query-timeout', type=int, default=None,
                            help=f'Neptune Analytics only. Specifies the maximum query timeout in milliseconds.')
        parser.add_argument('--explain-type', type=str.lower, default='dynamic',
                            help=f'Explain mode to use when using the explain query mode. '
                                 f'Accepted values: {OPENCYPHER_EXPLAIN_MODES}')
        parser.add_argument('-qp', '--query-parameters', type=str, default='',
                            help='Parameter definitions to apply to the query. This option can accept a local variable '
                                 'name, or a string representation of the map.')
        parser.add_argument('-g', '--group-by', type=str, default='~labels',
                            help='Property used to group nodes (e.g. code, ~id) default is ~labels')
        parser.add_argument('-gd', '--group-by-depth', action='store_true', default=False,
                            help="Group nodes based on path hierarchy")
        parser.add_argument('-gr', '--group-by-raw', action='store_true', default=False,
                            help="Group nodes by the raw result")
        parser.add_argument('mode', nargs='?', default='query', help='query mode [query|bolt|explain]',
                            choices=['query', 'bolt', 'explain'])
        parser.add_argument('-d', '--display-property', type=str, default='~labels',
                            help='Property to display the value of on each node, default is ~labels')
        parser.add_argument('-de', '--edge-display-property', type=str, default='~labels',
                            help='Property to display the value of on each edge, default is ~type')
        parser.add_argument('-t', '--tooltip-property', type=str, default='',
                            help='Property to display the value of on each node tooltip. If not specified, tooltip '
                                 'will default to the node label value.')
        parser.add_argument('-te', '--edge-tooltip-property', type=str, default='',
                            help='Property to display the value of on each edge tooltip. If not specified, tooltip '
                                 'will default to the edge label value.')
        parser.add_argument('-l', '--label-max-length', type=int, default=10,
                            help='Specifies max length of vertex label, in characters. Default is 10')
        parser.add_argument('-rel', '--rel-label-max-length', type=int, default=10,
                            help='Specifies max length of edge labels, in characters. Default is 10')
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        parser.add_argument('--store-format', type=str.lower, default='json',
                            help=f'Configures export type when using --store-to with base query mode. '
                                 f'Valid inputs: {QUERY_STORE_TO_FORMATS}. Default is JSON')
        parser.add_argument('--export-to', type=str, default='',
                            help='Export the base query mode CSV result to the provided file path.')
        parser.add_argument('--ignore-groups', action='store_true', default=False, help="Ignore all grouping options")
        parser.add_argument('-sp', '--stop-physics', action='store_true', default=False,
                            help="Disable visualization physics after the initial simulation stabilizes.")
        parser.add_argument('-sd', '--simulation-duration', type=int, default=1500,
                            help='Specifies maximum duration of visualization physics simulation. Default is 1500ms')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no query output.")
        parser.add_argument('-ct', '--connected-table', action='store_true', default=False,
                            help=f'Dynamically load jQuery and DataTables resources for iTables. For more information, see: '
                                 f'https://mwouts.github.io/itables/quick_start.html#offline-mode-versus-connected-mode')
        parser.add_argument('-r', '--results-per-page', type=int, default=10,
                            help='Specifies how many query results to display per page in the output. Default is 10')
        parser.add_argument('--no-scroll', action='store_true', default=False,
                            help="Display the entire output without a scroll bar.")
        parser.add_argument('--hide-index', action='store_true', default=False,
                            help="Hide the index column numbers when displaying the results.")
        args = parser.parse_args(line.split())
        logger.debug(args)
        res = None
        res_format = None
        results_df = None

        query_params = None
        if args.query_parameters:
            if args.query_parameters in local_ns:
                query_params_input = local_ns[args.query_parameters]
            else:
                query_params_input = args.query_parameters
            if isinstance(query_params_input, dict):
                query_params = json.dumps(query_params_input)
            else:
                try:
                    query_params_dict = json.loads(query_params_input.replace("'", '"'))
                    query_params = json.dumps(query_params_dict)
                except Exception as e:
                    print(f"Invalid query parameter input, ignoring.")

        if args.no_scroll:
            oc_layout = UNRESTRICTED_LAYOUT
            oc_scrollY = True
            oc_scrollCollapse = False
            oc_paging = False
        else:
            oc_layout = DEFAULT_LAYOUT
            oc_scrollY = "475px"
            oc_scrollCollapse = True
            oc_paging = True

        if not args.silent:
            tab = widgets.Tab()
            titles = []
            children = []
            first_tab_output = widgets.Output(layout=oc_layout)
            children.append(first_tab_output)

        if args.mode == 'explain':
            query_start = time.time() * 1000  # time.time() returns time in seconds w/high precision; x1000 to get in ms
            res = self.client.opencypher_http(cell, explain=args.explain_type, query_params=query_params,
                                              plan_cache=args.plan_cache)
            query_time = time.time() * 1000 - query_start
            res_replace_chars = res.content.replace(b'$', b'\&#36;')
            explain = res_replace_chars.decode("utf-8")
            res.raise_for_status()
            if not args.silent:
                oc_metadata = build_opencypher_metadata_from_query(query_type='explain', results=None,
                                                                   results_type='explain', res=res,
                                                                   query_time=query_time)
                titles.append('Explain')
                explain_bytes = explain.encode('utf-8')
                base64_str = base64.b64encode(explain_bytes).decode('utf-8')
                first_tab_html = opencypher_explain_template.render(table=explain,
                                                                    link=f"data:text/html;base64,{base64_str}")
        elif args.mode == 'query':
            if not self.client.is_analytics_domain() and args.query_timeout is not None:
                print("queryTimeoutMilliseconds is not supported for Neptune DB, ignoring.")

            query_start = time.time() * 1000  # time.time() returns time in seconds w/high precision; x1000 to get in ms
            oc_http = self.client.opencypher_http(cell, query_params=query_params,
                                                  plan_cache=args.plan_cache,
                                                  query_timeout=args.query_timeout)
            query_time = time.time() * 1000 - query_start
            if oc_http.status_code == 400 and not self.client.is_analytics_domain() and args.plan_cache != "auto":
                try:
                    oc_http_ex = json.loads(oc_http.content.decode('utf-8'))
                    if (oc_http_ex["code"] == "MalformedQueryException"
                            and oc_http_ex["detailedMessage"].startswith("Invalid input")):
                        print("Please ensure that you are on NeptuneDB 1.3.2.0 or later when attempting to use "
                              "--plan-cache.")
                except:
                    pass
            oc_http.raise_for_status()

            try:
                res = oc_http.json()
            except JSONDecodeError:
                # handle JOLT format
                res_list = oc_http.text.split()
                print(res_list)
                res = []
                for result in res_list:
                    result_map = json.loads(result)
                    if "data" in result_map:
                        res.append(result_map["data"])
                res_format = "jolt"

            if not args.silent:
                oc_metadata = build_opencypher_metadata_from_query(query_type='query', results=res,
                                                                   results_type=res_format, query_time=query_time)
                first_tab_html = ""
                results_df, has_results = oc_results_df(res, res_format)
                if has_results:
                    titles.append('Console')
                try:
                    gn = OCNetwork(group_by_property=args.group_by, display_property=args.display_property,
                                   group_by_raw=args.group_by_raw,
                                   group_by_depth=args.group_by_depth,
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
                        titles.append('Graph')
                        children.append(force_graph_output)
                except (TypeError, ValueError) as network_creation_error:
                    logger.debug(f'Unable to create network from result. Skipping from result set: {res}')
                    logger.debug(f'Error: {network_creation_error}')

        elif args.mode == 'bolt':
            res_format = 'bolt'
            query_start = time.time() * 1000
            if query_params:
                res = self.client.opencyper_bolt(cell, **query_params)
            else:
                res = self.client.opencyper_bolt(cell)
            query_time = time.time() * 1000 - query_start
            if not args.silent:
                oc_metadata = build_opencypher_metadata_from_query(query_type='bolt', results=res,
                                                                   results_type=res_format, query_time=query_time)
                first_tab_html = ""
                results_df, has_results = oc_results_df(res, res_format)
                if has_results:
                    titles.append('Console')
                # Need to eventually add code to parse and display a network for the bolt format here

        if not args.silent:
            if args.mode != 'explain':
                # Display JSON tab
                json_output = widgets.Output(layout=oc_layout)
                with json_output:
                    print(json.dumps(res, indent=2))
                children.append(json_output)
                titles.append('JSON')

            # Display Query Metadata Tab
            metadata_output = widgets.Output(layout=oc_layout)
            titles.append('Query Metadata')
            children.append(metadata_output)

            if first_tab_html == "" and results_df is None:
                tab.children = children[1:]  # the first tab is empty, remove it and proceed
            else:
                tab.children = children

            for i in range(len(titles)):
                tab.set_title(i, titles[i])
            display(tab)

            with metadata_output:
                display(HTML(oc_metadata.to_html()))

            if results_df is not None:
                with first_tab_output:
                    visible_results, final_pagination_options, final_pagination_menu = generate_pagination_vars(
                        args.results_per_page)
                    oc_columndefs = [
                        {"type": "string", "targets": "_all"},
                        {"width": "5%", "targets": 0},
                        {"visible": True, "targets": 0},
                        {"searchable": False, "targets": 0},
                        {"className": "nowrap dt-left", "targets": "_all"},
                        {"createdCell": JavascriptFunction(index_col_js), "targets": 0},
                        {"createdCell": JavascriptFunction(cell_style_js), "targets": "_all", }
                    ]
                    if args.hide_index:
                        oc_columndefs[1]["visible"] = False
                    init_notebook_mode(connected=args.connected_table)
                    show(results_df,
                         connected=args.connected_table,
                         scrollX=True,
                         scrollY=oc_scrollY,
                         columnDefs=oc_columndefs,
                         paging=oc_paging,
                         scrollCollapse=oc_scrollCollapse,
                         lengthMenu=[final_pagination_options, final_pagination_menu],
                         pageLength=visible_results,
                         buttons=[
                             "pageLength",
                             {
                                 "extend": "copyHtml5",
                                 "text": "Copy",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "csvHtml5",
                                 "title": OC_RESULTS_FILENAME,
                                 "text": "Download CSV",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             },
                             {
                                 "extend": "excelHtml5",
                                 "filename": OC_RESULTS_FILENAME,
                                 "title": None,
                                 "text": "Download XLSX",
                                 "exportOptions": RESULTS_EXPORT_OPTIONS
                             }
                         ]
                         )
            elif first_tab_html != "":
                with first_tab_output:
                    display(HTML(first_tab_html))

        if args.mode == QueryMode.EXPLAIN:
            stored_results = explain
        elif results_df is not None:
            json_results = res
            res_store_type = args.store_format
            res_export_path = args.export_to

            if res_store_type in PANDAS_FORMATS or res_export_path != '':
                results_df = process_df_for_store(language='oc',
                                                  results_df=results_df)

            stored_results = get_results_for_store(store_type=res_store_type,
                                                   pandas_results=results_df,
                                                   json_results=json_results)

            export_csv_results(export_path=res_export_path,
                               results_df=results_df)
        else:
            stored_results = res

        store_to_ns(args.store_to, stored_results, local_ns)

    def handle_opencypher_status(self, line, local_ns):
        """
        This is refactored into its own handler method so that we can invoke it from
        %opencypher_status or from %oc_status
        """
        parser = argparse.ArgumentParser()
        parser.add_argument('-q', '--queryId', default='',
                            help='The ID of a running OpenCypher query. '
                                 'Only displays the status of the specified query.')
        parser.add_argument('-c', '--cancelQuery', action='store_true', default=False,
                            help='Tells the status command to cancel a query. This parameter does not take a value.')
        parser.add_argument('-w', '--includeWaiting', action='store_true', default=False,
                            help='Neptune DB only. When set to true and other parameters are not present, causes '
                                 'status information for waiting queries to be returned as well as for running '
                                 'queries. This parameter does not take a value.')
        parser.add_argument('--state', type=str.upper, default='ALL',
                            help=f'Neptune Analytics only. Specifies what subset of query states to retrieve the '
                                 f'status of. Default is ALL. Accepted values: {OPENCYPHER_STATUS_STATE_MODES}')
        parser.add_argument('-m', '--maxResults', type=int, default=200,
                            help=f'Neptune Analytics only. Sets an upper limit on the set of returned queries whose '
                                 f'status matches --state. Default is 200.')
        parser.add_argument('-s', '--silent-cancel', action='store_true', default=False,
                            help='If silent_cancel=true then the running query is cancelled and the HTTP response '
                                 'code is 200. If silent_cancel is not present or silent_cancel=false, '
                                 'the query is cancelled with an HTTP 500 status code.')
        parser.add_argument('--silent', action='store_true', default=False, help="Display no output.")
        parser.add_argument('--store-to', type=str, default='', help='store query result to this variable')
        args = parser.parse_args(line.split())

        using_analytics = self.client.is_analytics_domain()
        if not args.cancelQuery:
            query_id = ''
            include_waiting = None
            state = ''
            max_results = None
            if args.includeWaiting and not args.queryId and not self.client.is_analytics_domain():
                include_waiting = args.includeWaiting
            elif args.state and not args.queryId and self.client.is_analytics_domain():
                state = args.state
                max_results = args.maxResults
            else:
                query_id = args.queryId
            res = self.client.opencypher_status(query_id=query_id,
                                                include_waiting=include_waiting,
                                                state=state,
                                                max_results=max_results,
                                                use_analytics_endpoint=using_analytics)
            if using_analytics and res.status_code == 400 and 'Bad route: /queries' in res.json()["message"]:
                res = self.client.opencypher_status(query_id=query_id,
                                                    include_waiting=include_waiting,
                                                    state=state,
                                                    max_results=max_results,
                                                    use_analytics_endpoint=False)
            res.raise_for_status()
        else:
            if args.queryId == '':
                if not args.silent:
                    print(OPENCYPHER_CANCEL_HINT_MSG)
                return
            else:
                res = self.client.opencypher_cancel(args.queryId,
                                                    silent=args.silent_cancel,
                                                    use_analytics_endpoint=using_analytics)
                if using_analytics and res.status_code == 400 and 'Bad route: /queries' in res.json()["message"]:
                    res = self.client.opencypher_cancel(args.queryId,
                                                        silent=args.silent_cancel,
                                                        use_analytics_endpoint=False)
                res.raise_for_status()
        if using_analytics and args.cancelQuery:
            if not args.silent:
                print(f'Submitted cancellation request for query ID: {args.queryId}')
        else:
            js = res.json()
            store_to_ns(args.store_to, js, local_ns)
            if not args.silent:
                print(json.dumps(js, indent=2))
