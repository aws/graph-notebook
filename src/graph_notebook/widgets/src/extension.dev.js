/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

"use strict";

window["requirejs"].config({
  map: {
    "*": {
      graph_notebook_widgets: "http://localhost:9000/index.js"
    },
  },
});
// Export the required load_ipython_extension function
const load_ipython_extension = function () {};
export { load_ipython_extension };
