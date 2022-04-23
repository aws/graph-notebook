/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

import { Application, IPlugin } from "@phosphor/application";

import { Widget } from "@phosphor/widgets";

import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";

import { ForceModel, ForceView } from "./force_widget";

import { MODULE_NAME, MODULE_VERSION } from "./version";

const EXTENSION_ID = "graph_notebook_widgets:plugin";

/**
 * Activate the widget extension.
 */
function activateWidgetExtension(
  app: Application<Widget>,
  registry: IJupyterWidgetRegistry
): void {
  registry.registerWidget({
    name: MODULE_NAME,
    version: MODULE_VERSION,
    exports: { ForceModel: ForceModel, ForceView: ForceView },
  });
}

/**
 * The example plugin.
 */
const plugin: IPlugin<Application<Widget>, void> = {
  id: EXTENSION_ID,
  requires: [IJupyterWidgetRegistry],
  activate: activateWidgetExtension,
  autoStart: true,
} as unknown as IPlugin<Application<Widget>, void>;

export default plugin;
