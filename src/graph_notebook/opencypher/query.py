# """
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: Apache-2.0
# """
#
# import logging
#
# from neo4j import GraphDatabase
#
# from graph_notebook.opencypher.client_provider.default_client import AbstractCypherClientProvider
#
# logging.basicConfig()
# logger = logging.getLogger("opencypher")
#
# OPENCYPHER_ACTION = 'openCypher'
#
#
# def do_opencypher_query(query, host, port, use_ssl, request_param_generator, extra_headers=None):
#     if extra_headers is None:
#         extra_headers = {}
#
#     if 'content-type' not in extra_headers:
#         extra_headers['content-type'] = 'application/x-www-form-urlencoded'
#
#     data = {
#         'query': query
#     }
#
#     res = call_and_get_response('post', OPENCYPHER_ACTION, host, port, request_param_generator, use_ssl, data,
#                                 extra_headers)
#     return res.json()
#
#
# def _run_bolt_transaction(transaction, query, kwargs):
#     res = transaction.run(query, **kwargs)
#     return res
#
#
# def get_bolt_client(host, port, use_ssl, client_provider: AbstractCypherClientProvider):
#     return client_provider.get_driver(host, port, use_ssl)
#
#
# def do_opencypher_bolt_query(query, host, port, use_ssl: bool, client_provider: AbstractCypherClientProvider, **kwargs):
#     driver = get_bolt_client(host, port, use_ssl, client_provider)
#     with driver.session() as session:
#         res = session.run(query, kwargs)
#         data = res.data()
#     driver.close()
#     return data
