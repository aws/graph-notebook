/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

import { Application, IPlugin } from '@lumino/application';

import { Widget } from '@lumino/widgets';

import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";

import { ForceModel, ForceView } from "./force_widget";

// import { MODULE_NAME, MODULE_VERSION } from "./version";

// const EXTENSION_ID = "graph_notebook_widgets:plugin";

// At the top of plugin.ts
console.warn('🔄 graph_notebook_widgets plugin file loaded');

window.addEventListener('error', (event) => {
  console.error('Global error in graph_notebook_widgets:', event.error);
});

window.addEventListener('unhandledrejection', (event) => {
  console.error('Unhandled promise rejection in graph_notebook_widgets:', event.reason);
});

// function activateWidgetExtension(
//   app: Application<Widget>,
//   registry: IJupyterWidgetRegistry
// ): void {
//   console.warn('🔵 Plugin activation start:', {
//     moduleName: MODULE_NAME,
//     moduleVersion: MODULE_VERSION,
//     hasRegistry: !!registry
//   });

//   if (!registry) {
//     console.error('❌ Widget registry not available');
//     return;
//   }

//   try {
//     console.warn('📦 Registering widget model:', {
//       name: ForceModel.model_name,
//       module: ForceModel.model_module,
//       version: ForceModel.model_module_version
//     });

//     registry.registerWidget({
//       name: MODULE_NAME,
//       version: MODULE_VERSION,
//       exports: {
//         ForceModel: ForceModel,
//         ForceView: ForceView
//       }
//     });

//     console.warn('✅ Widget registration successful');
    
//     // Verify registration without using resolve
//     console.warn('📦 Registration details:', {
//       modelName: ForceModel.model_name,
//       modelModule: ForceModel.model_module,
//       modelVersion: ForceModel.model_module_version,
//       viewName: ForceModel.view_name,
//       viewModule: ForceModel.view_module,
//       viewVersion: ForceModel.view_module_version
//     });

//   } catch (error) {
//     console.error('❌ Registration failed:', error);
//     console.error('Debug info:', {
//       ForceModel: !!ForceModel,
//       ForceView: !!ForceView,
//       modelProps: Object.keys(ForceModel),
//       viewProps: Object.keys(ForceView)
//     });
//   }

//   console.warn('🔵 Plugin activation complete');
// }







// function activateWidgetExtension(
//   app: Application<Widget>,
//   registry: IJupyterWidgetRegistry
// ): void {
//   console.warn('🔵 Plugin activation start:', {
//     moduleName: MODULE_NAME,
//     moduleVersion: MODULE_VERSION,
//     hasRegistry: !!registry,
//     registryType: registry ? registry.constructor.name : 'undefined'
//   });

//   if (!registry) {
//     console.error('❌ Widget registry not available');
//     return;
//   }

//   try {
//     // Log model info before registration
//     console.warn('📦 Model info:', {
//       modelName: ForceModel.model_name,
//       modelModule: ForceModel.model_module,
//       modelVersion: ForceModel.model_module_version,
//       modelClass: ForceModel.name
//     });

//     registry.registerWidget({
//       name: MODULE_NAME,
//       version: MODULE_VERSION,
//       exports: {
//         ForceModel: ForceModel,
//         ForceView: ForceView
//       }
//     });

//     // Verify registration was successful
//     const registered = registry['_models']?.get(MODULE_NAME);
//     console.warn('✅ Registration result:', {
//       success: !!registered,
//       registeredName: registered?.name,
//       registeredVersion: registered?.version
//     });

//   } catch (error) {
//     console.error('❌ Registration failed:', error);
//     throw error;  // Re-throw to ensure error is visible
//   }
// }



function activateWidgetExtension(
  app: Application<Widget>,
  registry: IJupyterWidgetRegistry
): void {
  console.warn('🔄 Starting widget registration:', {
    registry: !!registry,
    registryType: registry?.constructor.name
  });

  // Log the ForceModel details before registration
  console.warn('📦 ForceModel details:', {
    modelName: ForceModel.model_name,
    modelModule: ForceModel.model_module,
    modelVersion: ForceModel.model_module_version
  });

  try {
    // Register with minimal configuration
    const result = registry.registerWidget({
      name: ForceModel.model_module,
      version: ForceModel.model_module_version,
      exports: {
        ForceModel: ForceModel,
        ForceView: ForceView
      }
    });

    console.warn('✅ Registration attempt complete:', {
      result,
      registryModels: registry['_models'] ? [...registry['_models'].keys()] : [],
      hasModel: !!registry['_models']?.get(ForceModel.model_module)
    });

  } catch (error) {
    console.error('❌ Registration failed:', error);
  }
}


export default {
  id: 'graph_notebook_widgets:plugin',
  requires: [IJupyterWidgetRegistry],
  activate: activateWidgetExtension,
  autoStart: true
} as IPlugin<Application<Widget>, void>;


// const plugin: IPlugin<Application<Widget>, void> = {
//   id: 'graph_notebook_widgets:plugin',
//   autoStart: true,
//   requires: [IJupyterWidgetRegistry],
//   activate: (app: Application<Widget>, registry: IJupyterWidgetRegistry) => {
//     registry.registerWidget({
//       name: MODULE_NAME,
//       version: MODULE_VERSION,
//       exports: {
//         ForceModel,
//         ForceView
//       }
//     });
//   }
// };

// export default plugin;

    