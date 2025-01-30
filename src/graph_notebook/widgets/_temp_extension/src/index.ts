import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin
} from '@jupyterlab/application';

/**
 * Initialization data for the graph_notebook_widgets extension.
 */
const plugin: JupyterFrontEndPlugin<void> = {
  id: 'graph_notebook_widgets:plugin',
  description: 'A Custom Jupyter Library for rendering NetworkX MultiDiGraphs using vis-network',
  autoStart: true,
  activate: (app: JupyterFrontEnd) => {
    console.log('JupyterLab extension graph_notebook_widgets is activated!');
  }
};

export default plugin;
