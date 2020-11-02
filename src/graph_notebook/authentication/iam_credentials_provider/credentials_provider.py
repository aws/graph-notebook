"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

from abc import ABC, abstractmethod


class Credentials(object):
    def __init__(self, key, secret, region, token=''):
        self.key = key
        self.secret = secret
        self.token = token
        self.region = region


class CredentialsProviderBase(ABC):
    @abstractmethod
    def get_iam_credentials(self) -> Credentials:
        pass
