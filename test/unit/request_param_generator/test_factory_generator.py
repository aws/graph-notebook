"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

import unittest

from graph_notebook.configuration.generate_config import AuthModeEnum
from graph_notebook.authentication.iam_credentials_provider.credentials_factory import IAMAuthCredentialsProvider
from graph_notebook.authentication.iam_credentials_provider.env_credentials_provider import EnvCredentialsProvider
from graph_notebook.request_param_generator.default_request_generator import DefaultRequestGenerator
from graph_notebook.request_param_generator.factory import create_request_generator
from graph_notebook.request_param_generator.iam_request_generator import IamRequestGenerator
from graph_notebook.request_param_generator.sparql_request_generator import SPARQLRequestGenerator


class TestRequestParamGeneratorFactory(unittest.TestCase):
    def test_create_request_generator_sparql(self):
        mode = AuthModeEnum.DEFAULT
        command = 'sparql'
        rpg = create_request_generator(mode, command=command)
        self.assertEqual(SPARQLRequestGenerator, type(rpg))

    def test_create_request_generator_default(self):
        mode = AuthModeEnum.DEFAULT
        rpg = create_request_generator(mode)
        self.assertEqual(DefaultRequestGenerator, type(rpg))

    def test_create_request_generator_iam_env(self):
        mode = AuthModeEnum.IAM
        rpg = create_request_generator(mode, IAMAuthCredentialsProvider.ENV)
        self.assertEqual(IamRequestGenerator, type(rpg))
        self.assertEqual(EnvCredentialsProvider, type(rpg.credentials_provider))
