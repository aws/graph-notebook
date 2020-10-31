/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const data = require("../package.json");

/**
 * The _model_module_version/_view_module_version this package implements.
 *
 * The html widget manager assumes that this is the same as the npm package
 * version number.
 */
export const MODULE_VERSION = data.version;

/*
 * The current package name.
 */
export const MODULE_NAME = data.name;
