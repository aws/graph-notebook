/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const path = require("path");
const webpack = require("webpack");
const version = require("./package.json").version;
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');


// Custom webpack rules are generally the same for all webpack bundles, hence
// stored in a separate local variable.
const rules = [
  {
    test: /\.tsx?$/,
    exclude: /node_modules/,
    use: ["ts-loader", "source-map-loader"],
  },
  { test: /\.jsx?$/, 
    exclude: /node_modules/, 
    use: "source-map-loader" 
  },
  {
    test: /\.css$/,
    exclude: /node_modules/,
    use: ["style-loader", "css-loader"],
  },
];

// Packages that shouldn't be bundled but loaded at runtime
const externals = ['@jupyter-widgets/base'];

const resolve = {
  modules: ["node_modules", path.resolve(__dirname, "src")],
  // Add '.ts' and '.tsx' as resolvable extensions.
  extensions: [".ts", ".tsx", ".js", ".jsx"],
};

const mode = "production";

const basePlugins = [
  new webpack.IgnorePlugin({
    resourceRegExp: /\.d\.ts$/,
  }),
];

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

module.exports = [
  // Notebook extension AMD module
  {
    mode,
    entry: "./src/extension.js",
    output: {
      filename: "extension.js",
      path: path.resolve(__dirname, "nbextension"),
      libraryTarget: "amd",
    },
    module: { rules },
    devtool: "source-map",
    externals,
    resolve,
    plugins: basePlugins,
    watchOptions,
  },

  // Notebook extension
  {
    mode,
    entry: "./src/extension.ts",
    output: {
      filename: "index.js",
      path: path.resolve(__dirname, "nbextension"),
      libraryTarget: "amd",
    },
    module: { rules },
    devtool: "source-map",
    externals,
    resolve,
    plugins: basePlugins,
    watchOptions,
  },

  // Lab extension (main widget bundle)
  {
    mode,
    entry: "./src/index.ts",
    output: {
      filename: '[name].js',
      chunkFilename: '[name].[contenthash].js', // For other chunks
      path: path.resolve(__dirname, 'labextension/static'),
      publicPath: 'static/',
      libraryTarget: 'amd',
      clean: true
    },
    devtool: "source-map",
    module: { rules },
    externals: {
      ...externals,
      'jquery': 'jQuery'
    },
    resolve,
    plugins: [
      ...basePlugins,
      new ModuleFederationPlugin({
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
            requiredVersion: '^6.0.4',
            eager: true  // Add this
          },
          '@jupyter-widgets/jupyterlab-manager': { 
            singleton: true,
            requiredVersion: '^5.0.0',
            eager: true  // Add this
          }
        }
        
            
      }),
    ],
    watchOptions
  },

  // Documentation widget bundle
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