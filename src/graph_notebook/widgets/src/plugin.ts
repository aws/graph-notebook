/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

import { JupyterFrontEnd, JupyterFrontEndPlugin } from '@jupyterlab/application';
import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";
import { ForceModel, ForceView } from "./force_widget";
import { MODULE_NAME, MODULE_VERSION } from "./version";

const EXTENSION_ID = "graph_notebook_widgets:plugin";

/**
 * Activate the widget extension.
 */
function activate(app: JupyterFrontEnd, registry: IJupyterWidgetRegistry): void {
  console.log("🔧 Activating graph-notebook widget extension...");
  registry.registerWidget({
    name: MODULE_NAME,
    version: MODULE_VERSION,
    exports: { ForceModel, ForceView },
  });
  console.log("✅ Widget registration successful");
}

/**
 * graph_notebook_widgets plugin definition.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: EXTENSION_ID,
  requires: [IJupyterWidgetRegistry],
  activate,
  autoStart: true,
};

export default plugin;