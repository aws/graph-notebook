/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const webpackConfig = require("./webpack.config.js");

const rules = webpackConfig[1].module.rules;
rules.unshift({
  test: /\.tsx?$/,
  enforce: "pre",
  exclude: /node_modules/,
  use: [{ loader: "eslint-loader", options: { emitWarning: true } }],
});

module.exports = function (config) {
  config.set({
    basePath: "",
    frameworks: ["mocha", "chai", "sinon"],
    files: ["src/**/*.spec.ts"],
    exclude: [],
    preprocessors: {
      "src/**/*.spec.ts": ["webpack"],
    },
    webpack: {
      mode: "development",
      devtool: "eval-source-map",
      module: {
        rules: rules,
      },
      resolve: webpackConfig[1].resolve,
      plugins: webpackConfig[1].plugins,
    },
    webpackMiddleware: {
      stats: {
        colors: true,
      },
      // stats: "detailed"
    },
    reporters: ["progress", "mocha"],
    port: 9876,
    colors: true,
    logLevel: config.LOG_INFO,
    autoWatch: true,
    browsers: ["Firefox"],
    singleRun: true,
    concurrency: Infinity,
  });
};
