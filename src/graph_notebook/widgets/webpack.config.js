/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

const path = require("path");
const webpack = require("webpack");
const version = require("./package.json").version;

// Custom webpack rules are generally the same for all webpack bundles, hence
// stored in a separate local variable.
const rules = [
  // {test: /\.tsx?$/, enforce: 'pre', exclude: /node_modules/, use: [{ loader: 'eslint-loader', options: { emitWarning: true }}]},
  {
    test: /\.tsx?$/,
    exclude: /node_modules/,
    use: ["ts-loader", "source-map-loader"],
  },
  { test: /\.jsx?$/, exclude: /node_modules/, use: "source-map-loader" },
  {
    test: /\.css$/,
    exclude: /node_modules/,
    use: ["style-loader", "css-loader"],
  },
];

// Packages that shouldn't be bundled but loaded at runtime
const externals = {
  "@jupyter-widgets/base": "@jupyter-widgets/base",
};

const resolve = {
  modules: ["node_modules", path.resolve(__dirname, "src")],
  // Add '.ts' and '.tsx' as resolvable extensions.
  extensions: [".ts", ".tsx", ".js", ".jsx"],
};

const mode = "production";

const plugins = [
  // Replace WatchIgnorePlugin with IgnorePlugin for resources that should be ignored during build
  new webpack.IgnorePlugin({
    resourceRegExp: /\.d\.ts$/, // Ignore declaration files
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
  /**
   * Loader for the Notebook extension amd module
   */

  {
    mode: mode,
    entry: "./src/extension.js",
    output: {
      filename: "extension.js",
      path: path.resolve(__dirname, "nbextension"),
      library: {
        name: "graph_notebook_widgets",
        type: "var",
      },
    },
    module: {
      rules: rules,
    },
    devtool: "source-map",
    externals: externals,
    resolve: resolve,
    plugins: plugins,
    watchOptions: watchOptions,
  },

  /**
   * Notebook extension
   *
   * This bundle only contains the part of the JavaScript that is run on load of
   * the notebook.
   */
  {
    mode: mode,
    entry: "./src/extension.ts",
    output: {
      filename: "index.js",
      path: path.resolve(__dirname, "nbextension"),
      // Using amd target without giving a library name requires the module being loaded by a RequireJS module loader.
      // See https://webpack.js.org/configuration/output/#outputlibrary and src/extension.js.
      library: {
        name: "graph_notebook_widgets",
        type: "amd",
      },
    },
    module: {
      rules: rules,
    },
    devtool: "source-map",
    externals: externals,
    resolve: resolve,
    plugins: plugins,
    watchOptions: watchOptions,
  },

  /**
   * Embeddable graph_notebook_widget bundle
   *
   * This bundle is almost identical to the notebook extension bundle. The only
   * difference is in the configuration of the webpack public path for the
   * static assets.
   *
   * The target bundle is always `dist/index.js`, which is the path required by
   * the custom widget embedder.
   */
  {
    mode: mode,
    entry: "./src/index.ts",
    output: {
      filename: "index.js",
      path: path.resolve(__dirname, "dist"),
      library: {
        name: "graph_notebook_widgets",
        type: "amd",
      },
      publicPath:
        `https://unpkg.com/graph_notebook_widget@${version}/dist/`,
    },
    devtool: "source-map",
    module: {
      rules: rules,
    },
    externals: externals,
    resolve: resolve,
    plugins: plugins,
    watchOptions: watchOptions,
  },

  /**
   * Documentation widget bundle
   *
   * This bundle is used to embed widgets in the package documentation.
   */
  {
    mode: mode,
    entry: "./src/index.ts",
    output: {
      filename: "embed-bundle.js",
      path: path.resolve(__dirname, "docs", "source", "_static"),
      library: {
        name: "graph_notebook_widgets",
        type: "amd",
      },
    },
    module: {
      rules: rules,
    },
    devtool: "source-map",
    externals: externals,
    resolve: resolve,
    plugins: plugins,
    watchOptions: watchOptions,
  },
];
