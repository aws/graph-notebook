// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// Entry point for the notebook bundle containing custom model definitions.
//
// Setup notebook base URL
//
// Some static assets may be required by the custom widget javascript. The base
// url for the notebook is not known at build time and is therefore computed
// dynamically.

declare global {
  interface Window {
    __webpack_public_path__: string;
  }
}

// eslint-disable-next-line @typescript-eslint/camelcase
window.__webpack_public_path__ =
  document.body.getAttribute("data-base-url") +
  "nbextensions/graph_notebook_widgets";

export * from "./index";
