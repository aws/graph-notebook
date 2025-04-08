/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const path = require("path");
const webpack = require("webpack");
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');
const version = require("./package.json").version;

// Webpack loader rules for TypeScript, JavaScript, and CSS files
const rules = [
  {
    // TypeScript files
    test: /\.tsx?$/,
    exclude: /node_modules/,
    use: ["ts-loader", "source-map-loader"],
  },
  {
    // JavaScript files
    test: /\.jsx?$/,
    exclude: /node_modules/,
    use: "source-map-loader"
  },
  {
    // CSS files
    test: /\.css$/,
    exclude: /node_modules/,
    use: ["style-loader", "css-loader"],
  },
];

// Packages that should be treated as external dependencies
const externals = ['@jupyter-widgets/base'];

// Configuration for module resolution
const resolve = {
  modules: ["node_modules", path.resolve(__dirname, "src")],
  extensions: [".ts", ".tsx", ".js", ".jsx"],
};


const mode = "production";

// Base webpack plugins used across all configurations
const basePlugins = [
  new webpack.IgnorePlugin({
    resourceRegExp: /\.d\.ts$/,  // Ignore TypeScript declaration files
  }),
];

// Watch configuration to ignore certain directories
const watchOptions = {
  ignored: [
    "dist/**",
    "docs/**",
    "lib/**",
    "labextension/**",
    "nbextension/**",
    "node_modules/**",
  ],
};

// Module Federation Plugin configuration for JupyterLab extension
const labModuleFederationConfig = {
  name: 'graph_notebook_widgets',
  library: { type: 'amd' },
  filename: 'remoteEntry.js',
  exposes: {
    './extension': './src/plugin',
    './index': './src/index'
  },
  shared: {
    '@jupyter-widgets/base': { 
      singleton: true,
      requiredVersion: '^6.0.4'
    },
    '@jupyter/ydoc': {
      singleton: true,
      requiredVersion: '^3.0.0',
      strictVersion: false 
    }
  }
};

// Export array of webpack configurations
module.exports = [
  // 1. Notebook extension AMD module
  {
    mode,
    entry: "./src/extension.js",
    output: {
      filename: "extension.js",
      path: path.resolve(__dirname, "nbextension"),
      libraryTarget: "amd",
      library: "graph_notebook_widgets",
      publicPath: "nbextensions/graph_notebook_widgets/",
    },
    module: { rules },
    devtool: "source-map",
    externals,
    resolve,
    plugins: basePlugins,
    watchOptions,
  },

  // 2. Notebook extension
  {
    mode,
    entry: "./src/extension.ts",
    output: {
      filename: "index.js",
      path: path.resolve(__dirname, "nbextension"),
      libraryTarget: "amd",
      library: "graph_notebook_widgets",
      publicPath: "nbextensions/graph_notebook_widgets/",
    },
    module: { rules },
    devtool: "source-map",
    externals,
    resolve,
    plugins: basePlugins,
    watchOptions,
  },

  // 3. Lab extension with Module Federation
  {
    mode,
    entry: "./src/index.ts",
    output: {
      filename: '[name].js',
      chunkFilename: '[name].[contenthash].js',
      path: path.resolve(__dirname, 'labextension/static'),
      publicPath: 'static/',
      libraryTarget: 'amd'
    },
    devtool: "source-map",
    module: { rules },
    externals: {
      ...externals,
      'jquery': 'jQuery'  // Ensure jQuery is treated as external
    },
    resolve,
    plugins: [
      ...basePlugins,
      new ModuleFederationPlugin(labModuleFederationConfig),
    ],
    watchOptions
  },

  // 4. Documentation widget bundle
  {
    mode,
    entry: "./src/index.ts",
    output: {
      filename: "embed-bundle.js",
      path: path.resolve(__dirname, "docs", "source", "_static"),
      libraryTarget: "amd",
    },
    module: { rules },
    devtool: "source-map",
    externals,
    resolve,
    plugins: basePlugins,
    watchOptions,
  }
];