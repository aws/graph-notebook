import { Application, IPlugin } from "@lumino/application";
import { Widget } from "@lumino/widgets";
import { IJupyterWidgetRegistry } from "@jupyter-widgets/base";


import { ForceModel, ForceView } from "./force_widget";
// import { MODULE_NAME, MODULE_VERSION } from "./version"; // Uncomment this



function activateWidgetExtension(
  app: Application<Widget>,
  registry: IJupyterWidgetRegistry
): void {
  console.warn('🛠 Checking widget_manager:', registry['widget_manager']);
  if (!registry['widget_manager']) {
    console.error("🚨 widget_manager is missing! Check Jupyter widgets setup.");
  }
  


  // Log initial state
  console.warn('🔄 Initial Registry State:', {
    registryExists: !!registry,
    registryType: registry?.constructor.name,
    registryKeys: Object.keys(registry),
    registryMethods: Object.getOwnPropertyNames(Object.getPrototypeOf(registry))
  });

  try {
    // Log ForceModel configuration
    console.warn('🔧 ForceModel Configuration:', {
      defaults: new ForceModel().defaults(),
      staticProps: {
        model_name: ForceModel.model_name,
        model_module: ForceModel.model_module,
        model_module_version: ForceModel.model_module_version,
        view_name: ForceModel.view_name,
        view_module: ForceModel.view_module,
        view_module_version: ForceModel.view_module_version
      }
    });

    // Register widget with correct interface
    const result = registry.registerWidget({
      name: ForceModel.model_module,
      version: ForceModel.model_module_version,
      exports: {
        ForceModel: ForceModel,
        ForceView: ForceView
      }
    });

    // Check registration details
    console.warn('✅ Registration Details:', {
      result,
      registry: {
        models: registry['_models'] ? [...registry['_models'].entries()].map(([k,v]) => k) : [],
        types: registry['_widget_types'] ? Object.keys(registry['_widget_types']) : []
      },
      modelLookup: {
        byModule: registry['_models']?.has(ForceModel.model_module),
        byName: registry['_models']?.has(ForceModel.model_name),
        byFullPath: registry['_models']?.has(`${ForceModel.model_module}@${ForceModel.model_module_version}`)
      }
    });

  } catch (error) {
    console.error('❌ Registration failed:', {
      error,
      modelModule: ForceModel.model_module,
      moduleVersion: ForceModel.model_module_version
    });
  }

  // Add a delayed check
  setTimeout(() => {
    console.warn('Delayed Registry Check:', {
      models: registry['_models'] ? [...registry['_models'].keys()] : [],
      widgetTypes: registry['_widget_types'] ? Object.keys(registry['_widget_types']) : [],
      hasModel: registry['_models']?.has(ForceModel.model_module)
    });
  }, 1000);
}

  

export default {
  id: 'graph_notebook_widgets:plugin',
  requires: [IJupyterWidgetRegistry],
  activate: (app: Application<Widget>, registry: IJupyterWidgetRegistry | null) => {
    if (!registry) {
      console.error("❌ IJupyterWidgetRegistry is not available!");
      return;
    }
    activateWidgetExtension(app, registry);
  },
  autoStart: true
} as IPlugin<Application<Widget>, void>;