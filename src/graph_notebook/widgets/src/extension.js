"use strict";

window["requirejs"].config({
  map: {
    "*": {
      graph_notebook_widgets: "nbextensions/graph_notebook_widgets/index",
    },
  },
});
// Export the required load_ipython_extension function
const load_ipython_extension = function () {};
export { load_ipython_extension };
