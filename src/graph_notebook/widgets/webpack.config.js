const path = require("path");
const webpack = require("webpack");
const version = require("./package.json").version;
const ModuleFederationPlugin = require('webpack/lib/container/ModuleFederationPlugin');


const rules = [
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

// Update externals configuration
const externals = ['@jupyter-widgets/base'];

const resolve = {
  modules: ["node_modules", path.resolve(__dirname, "src")],
  extensions: [".ts", ".tsx", ".js", ".jsx"],
};

const mode = "production";

// Separate plugin configurations for different targets
const basePlugins = [
  new webpack.IgnorePlugin({
    resourceRegExp: /\.d\.ts$/,
  }),
];

const labPlugins = [
  ...basePlugins,
  new ModuleFederationPlugin({
    name: 'graph_notebook_widgets',
    library: { type: 'amd' },
    filename: 'remoteEntry.js',
    exposes: {
      './index': './src/index',
      './extension': './src/plugin'
    },
    shared: {
      '@jupyter-widgets/base': { singleton: true }
    }
  })
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

  // Lab extension
// In your webpack.config.js - update the lab extension configuration:
  {
    mode,
    entry: "./src/index.ts",
    output: {
      filename: '[name].js',
      chunkFilename: '[name].[contenthash].js', // For other chunks
      path: path.resolve(__dirname, 'labextension/static'),
      publicPath: 'static/',
      libraryTarget: 'amd'
    },
    devtool: "source-map",
    module: { rules },
    externals: {
      ...externals,
      'jquery': 'jQuery'  // Add this
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
            requiredVersion: '^6.0.4'
          }
        }
      }),
    // Add webpack.DefinePlugin to help with debugging
    new webpack.DefinePlugin({
      'process.env.DEBUG': JSON.stringify(true)
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
