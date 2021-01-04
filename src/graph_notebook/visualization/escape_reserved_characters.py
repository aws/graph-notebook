"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""

def escape_reserved_characters(content: str):
    return content.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
