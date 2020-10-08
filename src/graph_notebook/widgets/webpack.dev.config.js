/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const path = require("path");
const webpackConfig = require("./webpack.config.js");

const devServer = {
  contentBase: path.resolve(__dirname, "nbextension", "static"),
  headers: {
    "Access-Control-Allow-Origin": "*",
    "Access-Control-Allow-Methods": "*",
    "Access-Control-Allow-Headers": "*",
  },
  hotOnly: true,
  inline: true,
  port: 9000,
};

const extensionModule = webpackConfig[0];
extensionModule.mode = "development";
extensionModule.entry = "extension.dev.js";
extensionModule.devServer = devServer;

const indexModule = webpackConfig[1];
indexModule.mode = "development";
indexModule.entry = "index.dev.ts";
indexModule.output.publicPath = "http://localhost:9000/";
indexModule.devServer = devServer;

module.exports = [extensionModule, indexModule];
