/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

import {
  DOMWidgetModel,
  DOMWidgetView,
  ISerializers,
} from "@jupyter-widgets/base";
// import { Network } from "vis-network/standalone";
import ForceGraph from 'force-graph';

import * as d3 from 'd3-force-3d';


import {
  DynamicObject,
  ForceDraggableOptions,
  ForceNetwork,
  ForceResizableOptions,
  // GraphNode,
  // GraphLink,
  Message,
} from "./types";
import { MODULE_NAME, MODULE_VERSION } from "./version";

import feather from "feather-icons";
import $ from "jquery";
import 'jquery-ui/ui/widgets/draggable';
import 'jquery-ui/ui/widgets/resizable';
import { DraggableOptions, ResizableOptions } from 'jquery-ui';

// Import the CSS
import "../css/widget.css";

feather.replace();

/*
graph_notebook_widgets is a module to define the front-end modules for our kernel-sid ForceWidget.
It is made up of two classes (ForceModel and ForceView). The ForceModel contains only metadata which also exists on
the browser.

The ForceView is the class used by the browser for rendering. Because it is going to render elements
on the DOM, it extends widget.DOMWidgetView, and must provide an implementation for the class "render"
*/
export class ForceModel extends DOMWidgetModel {
  // eslint-disable-next-line @typescript-eslint/explicit-function-return-type
  defaults() {
    return {
      ...super.defaults(),
      _model_name: ForceModel.model_name,
      _model_module: ForceModel.model_module,
      _model_module_version: ForceModel.model_module_version,
      _view_name: ForceModel.view_name,
      _view_module: ForceModel.view_module,
      _view_module_version: ForceModel.view_module_version,
    };
  }

  static serializers: ISerializers = {
    ...DOMWidgetModel.serializers,
    // Add any extra serializers here
  };

  static model_name = "ForceModel";
  static model_module = MODULE_NAME;
  static model_module_version = MODULE_VERSION;
  static view_name = "ForceView"; // Set to null if no view
  static view_module = MODULE_NAME; // Set to null if no view
  static view_module_version = MODULE_VERSION;
}

export class ForceView extends DOMWidgetView {
  private networkDiv: HTMLDivElement = document.createElement("div");
  private canvasDiv: HTMLDivElement = document.createElement("div");
  private menu: HTMLDivElement = document.createElement("div");
  private expandDiv: HTMLDivElement = document.createElement("div");
  private searchDiv: HTMLDivElement = document.createElement("div");
  private searchOptionsDiv: HTMLDivElement = document.createElement("div");
  private resetDiv: HTMLDivElement = document.createElement("div");
  private detailsDiv: HTMLDivElement = document.createElement("div");
  private physicsDiv: HTMLDivElement = document.createElement("div");
  // private nodeDataset: NodeDataSet = new NodeDataSet(new Array<VisNode>(), {});
  // private edgeDataset: EdgeDataSet = new EdgeDataSet(new Array<VisEdge>(), {});
  // private vis: Network | null = null;

  private graph: any = null;
  private graphData: {
    nodes: any[];
    links: any[];
  } = {
    nodes: [],
    links: []
  };

  private handleResize = () => {
    if (this.graph) {
      this.graph
        .width(this.canvasDiv.clientWidth)
        .height(this.canvasDiv.clientHeight);
    }
  };

  private visOptions: DynamicObject = {};
  private detailsPanel = document.createElement("div");
  private detailsHeader = document.createElement("div");
  private graphPropertiesTable = document.createElement("table");
  private emptyDetailsMessage = document.createElement("p");
  private graphTableDiv = document.createElement("div");
  private resizeHandle = document.createElement("div");
  private detailsContainer = document.createElement("div");
  private noDataMessage = "No additional data from data source found.";
  private noElementSelectedMessage =
    "Select a single node or edge to see more.";
  private expandBtn = document.createElement("button");
  private excludeIDsFromSearch = false;
  private closeButton = document.createElement("button");
  private detailsText = document.createElement("p");
  private searchOptionsBtn = document.createElement("button");
  private searchMatchColorEdge = "rgba(9,120,209,1)";
  private searchMatchColorNode = {
    background: "rgba(210, 229, 255, 1)",
    border: "#0978D1",
  };
  private resetBtn = document.createElement("button");
  // private doingReset = false;
  private detailsBtn = document.createElement("button");
  private selectedNodeID: string | number = "";
  private physicsBtn = document.createElement("button");

  dispose(): void {
    window.removeEventListener('resize', this.handleResize);
    if (this.graph) {
      // @ts-ignore
      this.graph._destructor();
    }
  }

  render(): void {
    // Add jQuery UI CSS via CDN
    const jqueryUICss = document.createElement('link');
    jqueryUICss.rel = 'stylesheet';
    jqueryUICss.href = 'https://code.jquery.com/ui/1.13.2/themes/base/jquery-ui.css';
    document.head.appendChild(jqueryUICss);

    // Check jQuery availability
    if (!$) {
        console.error('jQuery not initialized');
        return;
    }

    this.networkDiv.classList.add("network-div");
    this.canvasDiv.style.height = "600px";
    this.canvasDiv.style.width = "100%";
    this.networkDiv.appendChild(this.canvasDiv);

    this.menu.classList.add("menu-div");

    this.networkDiv.appendChild(this.menu);
    this.networkDiv.appendChild(this.detailsPanel);

    /*
    When rendering the ForceView, the widget is given a div to attach everything to which will be added to the
    output section of the cell it was displayed in. This div can be accessed using "this.el"
    */
    this.el.appendChild(this.networkDiv);

    /*
    You can retrieve state from the Kernel's widget model by calling "this.get('trait_name')" which will retrieve the json
    representation of the traitlet that 'trait_name' corresponds to. If the trait is a number or string, only that data will be
    returned, not json.
     */

    // const network = this.model.get("network");
    this.visOptions = this.model.get("options");
    // this.populateDatasets(network);
    // const dataset = {
    //   nodes: this.nodeDataset,
    //   edges: this.edgeDataset,
    // };

    // this.vis = new Network(
    //   this.canvasDiv,
    //   dataset,
    //   this.stripCustomPhysicsOptions()
    // );

    
    this.graph = new ForceGraph(this.canvasDiv)
    .nodeId('id')
    .nodeLabel('label')
    .nodeColor('color')
    .linkSource('source')
    .linkTarget('target')
    .linkLabel('label')
    .backgroundColor('#ffffff')
    // Add warmup/cooldown settings
    .cooldownTicks(100)
    .warmupTicks(50)
    // Add force configurations
    .d3Force('charge', d3.forceManyBody().strength(-300))
    .d3Force('link', d3.forceLink().id((d: any) => d.id).distance(100))
    .d3Force('center', d3.forceCenter());
  
  


    window.addEventListener('resize', this.handleResize);

  // Update data handling
  const network = this.model.get("network");
  this.updateGraphData(network);

  this.graph
  .onNodeDragEnd(node => {
    node.fx = node.x;
    node.fy = node.y;
  })
  .onBackgroundClick(() => this.handleEmptyClick())
  .onLinkClick(link => this.handleEdgeClick(link))
  .enableNodeDrag(true)
  .enableZoom(true)
  .enablePanInteraction(true);

this.updateForceGraphOptions();


setTimeout(() => {
  this.graph?.pauseAnimation();
}, this.visOptions.physics.simulationDuration);


    /*
      To listen to messages sent from the kernel, you can register callback methods in the view class,
      this can be done using the "this.listenTo" method.

      For our purposes, the first param will always be 'this.model'. The second param is the message name which we
      are subscribing to. For messages triggered by a kernel trait changing its state, the message name will be
      'change:trait_name'. The third param is a reference to the callback function to be invoked when the given
      message occurs. This callback can receive the payload of the message if it would like to. The fourth and final
      parameter is used to keep a way to reference 'this' in the scope of the ForceView class.
    */
    this.listenTo(this.model, "msg:custom", this.interceptCustom);
    this.listenTo(this.model, "change:network", this.changeNetwork);
    this.listenTo(this.model, "change:options", this.changeOptions);

    // Wait for jQuery UI CSS to load before building actions
    jqueryUICss.onload = () => {
      console.warn('jQuery UI CSS loaded, initializing actions');
      this.buildActions();
      this.registerVisEvents();
      this.registerWidgetEvents();
    };

    // Fallback if CSS fails to load
    jqueryUICss.onerror = () => {
      console.error('Failed to load jQuery UI CSS, continuing without styles');
      this.buildActions();
      this.registerVisEvents();
      this.registerWidgetEvents();
    };
  }

  /**
   * Take the json from a given network, and update our datasets
   * used to render the vis Network.
   *
   * @remarks
   * Used at the initial rendering of the force widget, or any time
   * we override the network entirely
   *
   * @param network - The network to update this ForceView's datasets
   */
  // populateDatasets(network: ForceNetwork): void {
  //   const edges = this.linksToEdges(network.graph.links);
  //   this.nodeDataset.update(network.graph.nodes);
  //   this.edgeDataset.update(edges);
  // }

  // Add these methods for force-graph specific functionality
private updateForceGraphOptions(): void {
  if (!this.graph) return;
  
  this.graph
    .d3Force('charge', d3.forceManyBody().strength(-300))
    .d3Force('link', d3.forceLink().id((d: any) => d.id).distance(100))
    .d3Force('center', d3.forceCenter())
    .cooldownTime(this.visOptions.physics?.stabilization?.timeToActivate || 1000)
    .warmupTicks(this.visOptions.physics?.stabilization?.iterations || 50);

}

  // In updateGraphData
  updateGraphData(network: ForceNetwork): void {
    this.graphData = {
      nodes: network.graph.nodes.map(node => ({
        ...node,
        label: node.label || node.id,
        color: node.color || '#1f77b4'
      })),
      links: network.graph.links.map(link => ({
        ...link,
        label: link.label
      }))
    };
    
    if (this.graph) {
      this.graph.graphData(this.graphData);
    }
  }
  


  /**
   * Triggered when the network traitlet on the Kernel-side is overridden. In this case,
   * the currently rendered network will cleared with the nodes and links present in the new network
   */
  changeNetwork(): void {
    const network = this.model.get("network");
    this.updateGraphData(network);
  }
  

  /**
   * Triggered when the options traitlet is overridden on the Kernel-side. This will trigger updating the
   * options of the vis rendering.
   */
  changeOptions(): void {
    this.visOptions = this.model.get("options");
    if (!this.graph) return;
    
    // Convert vis.js options to force-graph options
    const forceOptions = {
      nodeColor: this.visOptions.nodes?.color || '#1f77b4',
      linkColor: this.visOptions.edges?.color || '#999',
      nodeRelSize: this.visOptions.nodes?.size || 6,
      linkWidth: this.visOptions.edges?.width || 1,
      linkDirectionalArrowLength: this.visOptions.edges?.arrows?.to ? 3.5 : 0
    };
    
    Object.entries(forceOptions).forEach(([key, value]) => {
      this.graph[key](value);
    });
    
    // Handle physics options
    if (this.visOptions.physics?.enabled === false) {
      this.graph.pauseAnimation();
    } else {
      this.graph.resumeAnimation();
    }
    
    this.updateForceGraphOptions();
  }

  /**
   * Returns a modified visOptions, with the custom simulationDuration and disablePhysicsAfterInitialSimulation physics
   * options removed. This prevents an error from being thrown when VisJS parses visOptions.
   */
  // stripCustomPhysicsOptions() {
  //   const visOptionsNoCustomPhysics = Object.assign(
  //     {},
  //     JSON.parse(JSON.stringify(this.visOptions))
  //   );
  //   delete visOptionsNoCustomPhysics["physics"]["simulationDuration"];
  //   delete visOptionsNoCustomPhysics["physics"][
  //     "disablePhysicsAfterInitialSimulation"
  //   ];
  //   return visOptionsNoCustomPhysics;
  // }

  /**
   * Take custom messages from the kernel and route them to the appropriate handler.
   * Each custom message will have a method field, and a corresponding data field which contains the payload
   * from the message.
   *
   * @remarks
   * NOTE: The method field is only present because all our custom messages build their payloads in this
   * fashion.
   */
  interceptCustom(msg: Message): void {
    const msgData = msg["data"];
    switch (msg["method"]) {
      case "add_node":
        this.addNode(msgData);
        break;
      case "add_node_data":
        this.addNodeData(msgData);
        break;
      case "add_node_property":
        this.addNodeProperty(msgData);
        break;
      case "add_edge":
        this.addEdge(msgData);
        break;
      case "add_edge_data":
        this.addEdgeData(msgData);
        break;
      default:
        console.log("unsupported method found", msg["method"]);
    }
  }

  /**
     * Add a node to the nodes dataset, merging the new node with the existing one
     * if this id is already present.
     *
     * The payload coming to this handler from the Kernel will look like:
     {
          "node_id": "1234",
          "data": {
            "label": "SJC",
            "properties": {
              "type": "airport",
              "runways": "4"
            }
          }
        }
     */
        addNode(msgData: DynamicObject): void {
          if (!msgData.hasOwnProperty("node_id")) return;
        
          const id: string = msgData["node_id"];
          const nodeIndex = this.graphData.nodes.findIndex(n => n.id === id);
          const nodeData = {
            id: id,
            label: msgData.data?.label || id,
            ...msgData.data
          };
        
          if (nodeIndex === -1) {
            this.graphData.nodes.push(nodeData);
          } else {
            this.graphData.nodes[nodeIndex] = {...this.graphData.nodes[nodeIndex], ...nodeData};
          }
        
          if (this.graph) {
            this.graph.graphData(this.graphData);
          }
        }

  /**
     * Handler to add new data to a node. The input to this is the same as the input to
     * adding a node, because adding a node checks for whether a given id existed,
     * and merges them if the node does.
     *
     * Example input:
     {
          "node_id": "1234",
          "data": {
            "properties": {
              "new_prop": "value"
            }
          }
        }
     */
  addNodeData(msgData: DynamicObject): void {
    this.addNode(msgData);
  }

  /**
     * Add a key-value pair to a node under its "properties" field
     * If the node does not exist, we will create it with this property.
     * Example input:

     {
          "node_id": "1234",
          "key": "foo",
          "value": "bar"
        }

     * Example result:
     {
          "node_id": "1234",
          "data": {
            "label": "SJC",
            "properties": {
              "type": "airport",
              "runways": "4",
              "foo": "bar"
            }
          }
        }
     */
  addNodeProperty(msgData: DynamicObject): void {
    const properties: DynamicObject = new DynamicObject();
    properties[msgData["key"]] = msgData["value"];

    this.addNode({
      node_id: msgData["node_id"],
      data: { properties: properties },
    });
  }

  /**
     * Add an edge to the edgeDataset. Before attempting to add an edge, we will
     * ensure that it has the fields we need to create a VisEdge as they are represented
     * by the add_edge EventfulNetwork method. That payload looks like:
     *
     * @remarks
     * NOTE: we have two different labels here because the top-level "label" is used for displaying,
     * while the inner "properties" label field is the actual value that the underlying structure had.
     * For example, for GremlinNetworks, each edge will have a label, but a user might want to choose the property
     * "code" for us in displaying. In that case, the value of the property "code" would be set to the top-level
     * "label" field.
     {
          "edge_id": "to",
          "from_id": "MKE2DFW",
          "label": "to",
          "to_id": "DFW",
          "data": {
            "label": "to"
          }
     }
     */
     addEdge(msgData: DynamicObject): void {
      if (!msgData.hasOwnProperty("from_id") || 
          !msgData.hasOwnProperty("to_id") || 
          !msgData.hasOwnProperty("edge_id")) return;
    
      const edgeID = `${msgData["from_id"]}:${msgData["to_id"]}:${msgData["edge_id"]}`;
      const linkIndex = this.graphData.links.findIndex(l => l.id === edgeID);
      const linkData = {
        id: edgeID,
        source: msgData["from_id"],
        target: msgData["to_id"],
        label: msgData.label || msgData["edge_id"],
        ...msgData.data
      };
    
      if (linkIndex === -1) {
        this.graphData.links.push(linkData);
      } else {
        this.graphData.links[linkIndex] = {...this.graphData.links[linkIndex], ...linkData};
      }
    
      if (this.graph) {
        this.graph.graphData(this.graphData);
      }
    }

  /**
   * Handler to add more data to an edge. The received payload is identical to
   * that of adding an edge, so we defer to that handler instead.
   */
  addEdgeData(data: DynamicObject): void {
    this.addEdge(data);
  }


  /**
   * Handler to route events observed on the vis network.
   */
  registerVisEvents(): void {
    if (!this.graph) return;

    this.graph
      .onNodeClick(node => {
        this.handleNodeClick(node.id);
      })
      .onLinkClick(link => {
        this.handleEdgeClick(link.id);
      });
  }


  /**
   * handle deselecting any number of nodes, ensuring the a node which was selected and is a current valid
   * search match does not recieve the wrong border color indicating a search match.
   * @param nodeID
   */
  handleDeselectNode(nodeID: string | number): void {
    console.log("handle deselect");
    
    const node = this.graphData.nodes.find(n => n.id === nodeID);
    if (!node) {
      return;
    }
  
    if (nodeID !== undefined && nodeID !== null && node.id === nodeID) {
      if (!node.group) {
        node.color = this.searchMatchColorNode;
      }
    } else {
      node.color = this.visOptions.nodes.color;
    }
    
    if (this.graph) {
      this.graph.nodeColor(n => n.color);
      this.graph.pauseAnimation();
    }
    this.selectedNodeID = "";
  }

  /**
   * When an empty click is detected, the details panel needs to be cleared to show the appropriate message
   */
  handleEmptyClick(): void {
    this.hideGraphProperties();
    this.detailsText.innerText = "Details";
    this.setDetailsMessage(this.noElementSelectedMessage);
  }

  /**
   * Hide the generated table of graph properties and show an empty message
   */
  hideGraphProperties(): void {
    if (this.emptyDetailsMessage.classList.contains("displayNone")) {
      this.emptyDetailsMessage.classList.toggle("displayNone");
    }

    if (!this.graphTableDiv.classList.contains("displayNone")) {
      this.graphTableDiv.classList.toggle("displayNone");
    }
  }

  /**
   * Build the Properties section of the details panel from a given node or edge.
   *
   * @param data - a node or edge
   */
  buildGraphPropertiesTable(data: any): void {
    const graphTable = $(this.graphPropertiesTable);
    let rows: Array<HTMLElement>;
    if (data.hasOwnProperty("properties")) {
      rows = this.buildTableRows(data.properties);
      $(graphTable).empty();
      $(graphTable).append(...rows);
      this.showGraphProperties();
    } else {
      this.hideGraphProperties();
      this.setDetailsMessage(this.noDataMessage);
    }
  }

  /**
   * ensure that the table containing graph properties is visible, and that the empty
   * message advising the user to select a node or edge is hidden
   */
  showGraphProperties(): void {
    if (this.graphTableDiv.classList.contains("displayNone")) {
      this.graphTableDiv.classList.toggle("displayNone");
    }

    if (!this.emptyDetailsMessage.classList.contains("displayNone")) {
      this.emptyDetailsMessage.classList.toggle("displayNone");
    }
  }

  setDetailsMessage(message: string): void {
    $(this.emptyDetailsMessage).text(message);
  }

  /**
   * Take an arbitrary object and convert its kvps into tr elements
   * with two columns. The first column is the key, the second is the value.
   *
   * @param data - a dictionary to turn into rows of a table
   */
  buildTableRows(data: DynamicObject): Array<HTMLElement> {
    const rows: Array<HTMLElement> = new Array<HTMLElement>();
    const sorted = Object.entries(data).sort((a, b) => {
      return a[0].localeCompare(b[0]);
    });
    sorted.forEach((entry: Array<any>) => {
      const row = document.createElement("tr");
      const property = document.createElement("td");
      const value = document.createElement("td");
      property.appendChild(document.createTextNode(entry[0].toString()));
      value.appendChild(document.createTextNode(entry[1].toString()));
      row.appendChild(property);
      row.appendChild(value);
      rows.push(row);
    });

    if (rows.length === 0) {
      const row = document.createElement("tr");
      const td = document.createElement("td");
      td.appendChild(
        document.createTextNode("No additional data from data source found.")
      );
      row.appendChild(td);
      rows.push(row);
    }
    return rows;
  }


  /**
   * Handle a single node being clicked. This will build details tables for all
   * key-value pairs which are on the edge. all key-value pairs which appear under the
   * "properties" top-level key will be treated as data which exists on the graph which
   * was queried to gather this data. All others are treated as data which is used by vis.
   *
   * @param nodeID - the id of the edge as represented by this.vis
   */
  handleNodeClick(nodeID: string | number): void {
    const node = this.graphData.nodes.find(n => n.id === nodeID);
    if (!node) return;
    this.handleDeselectNode(this.selectedNodeID);
    
    if (node.label !== undefined && node.label !== "") {
      this.detailsText.innerText = "Details - " + node.label;
    } else {
      this.detailsText.innerText = "Details";
    }
  
    this.buildGraphPropertiesTable(node);
    
    // Highlight selected node
    this.graph
      .nodeColor(n => n.id === nodeID ? '#ff0000' : this.visOptions.nodes?.color || '#1f77b4')
      .linkWidth(link => (link.source.id === nodeID || link.target.id === nodeID) ? 2 : 1);
      
    this.selectedNodeID = nodeID;
  }

  /**
   * Handle a single edge being clicked. This will build details tables for all
   * key-value pairs which are on the edge. all key-value pairs which appear under the
   * "properties" top-level key will be treated as data which exists on the graph which
   * was queried to gather this data. All others are treated as data which is used by vis.
   *
   * @param edgeID - the id of the edge as represented by this.vis
   */
  handleEdgeClick(linkID: string | number): void {
    const linkData = this.graphData.links.find(l => l.id === linkID);
    if (!linkData) return;
  
    if (linkData.title !== undefined && linkData.title !== "") {
      this.detailsText.innerText = "Details - " + linkData.title;
    } else {
      this.detailsText.innerText = "Details";
    }
  
    this.buildGraphPropertiesTable(linkData);
  }

  /**
   * Searches for the provided text under all nodes and edges in this.vis
   * If any property or key contains the text, that edge or node will be highlighted
   *
   * NOTE: Case sensitive.
   * @param text - The content to search for
   */
  handleSearchInput(text: string): void {
    if (!this.graph) return;
  
    if (text === "") {
      // Reset all nodes and links to default appearance
      this.graph
        .nodeColor(this.visOptions.nodes?.color || '#1f77b4')
        .linkColor(this.visOptions.edges?.color || '#999')
        .nodeRelSize(6);
      return;
    }
  
    // Highlight matching nodes and their links
    this.graph
      .nodeColor(node => {
        const matches = this.search(text, node, 0, this.excludeIDsFromSearch);
        return matches ? this.searchMatchColorNode.background : this.visOptions.nodes?.color || '#1f77b4';
      })
      .linkColor(link => {
        const matches = this.search(text, link, 0, this.excludeIDsFromSearch);
        return matches ? this.searchMatchColorEdge : this.visOptions.edges?.color || '#999';
      });
  }
  

  /**
   * Builds the side panel of actions and any other elements that they rely on.
   * Currently, this includes action icons for Search, Details, and Maximize
   * as well as a panel which is revealed when the details action is toggled.
   * This extra panel will show the details of a given selected node.
   */
  buildActions(): void {
    const rightActions = document.createElement("div");
    rightActions.classList.add("right-actions");
    this.menu.append(rightActions);

    this.expandDiv.classList.add("menu-action", "expand-div");
    this.searchDiv.classList.add("menu-action", "search-div");
    this.searchOptionsDiv.classList.add("menu-action", "search-options-div");
    this.resetDiv.classList.add("menu-action", "reset-div");
    this.detailsDiv.classList.add("menu-action", "details-div");
    this.physicsDiv.classList.add("menu-action", "physics-div");

    this.searchOptionsBtn.title = "Exclude/Include UUIDs in Search";
    this.searchOptionsBtn.innerHTML = feather.icons["user-check"].toSvg();
    this.searchOptionsDiv.appendChild(this.searchOptionsBtn);
    rightActions.append(this.searchOptionsDiv);
    this.searchOptionsBtn.onclick = (): void => {
      this.excludeIDsFromSearch = !this.excludeIDsFromSearch;
      if (this.excludeIDsFromSearch) {
        this.searchOptionsBtn.innerHTML = feather.icons["user-x"].toSvg();
      } else {
        this.searchOptionsBtn.innerHTML = feather.icons["user-check"].toSvg();
      }
    };

    const searchInput = document.createElement("input");
    searchInput.classList.add("search-bar");
    searchInput.type = "search";
    searchInput.placeholder = "search";
    searchInput.onkeyup = (): void => {
      this.handleSearchInput(searchInput.value);
    };

    this.searchDiv.append(searchInput);
    rightActions.append(this.searchDiv);

    this.resetBtn.title = "Reset Graph View";
    this.resetBtn.innerHTML = feather.icons["refresh-cw"].toSvg();
    this.resetDiv.appendChild(this.resetBtn);
    rightActions.append(this.resetDiv);
    this.resetBtn.onclick = (): void => {
      if (this.graph) {
        this.graph.zoomToFit(400);
        this.graph.resumeAnimation();
      }
    };
    this.physicsBtn.title = "Enable/Disable Graph Physics";
    if (
      this.visOptions.physics.enabled == true &&
      this.visOptions.physics.disablePhysicsAfterInitialSimulation == false
    ) {
      this.physicsBtn.innerHTML = feather.icons["unlock"].toSvg();
    } else {
      this.physicsBtn.innerHTML = feather.icons["lock"].toSvg();
    }
    this.physicsDiv.appendChild(this.physicsBtn);
    rightActions.append(this.physicsDiv);

    this.physicsBtn.onclick = (): void => {
      this.visOptions.physics.disablePhysicsAfterInitialSimulation = false;
      this.visOptions.physics.enabled = !this.visOptions.physics.enabled;
      this.changeOptions();
      if (this.visOptions.physics.enabled == true) {
        this.physicsBtn.innerHTML = feather.icons["unlock"].toSvg();
      } else {
        this.physicsBtn.innerHTML = feather.icons["lock"].toSvg();
      }
    };

    this.detailsBtn.innerHTML = feather.icons["list"].toSvg();
    this.detailsBtn.title = "Details";
    this.detailsDiv.appendChild(this.detailsBtn);
    rightActions.append(this.detailsDiv);
    this.detailsBtn.onclick = (): void => {
      this.handleDetailsToggle();
    };

    this.closeButton.onclick = (): void => {
      this.handleDetailsToggle();
    };

    //build the div which the details button toggles
    this.detailsContainer.classList.add("details-container");

    this.detailsPanel.classList.add("details", "hidden");
    this.detailsPanel.style.top = "100px";
    this.detailsPanel.style.left = "100px";

    this.detailsHeader.classList.add("details-header");
    this.detailsText.className = "details-text";
    this.closeButton.className = "close-button";
    this.detailsHeader.append(this.detailsText, this.closeButton);

    this.closeButton.innerText = "x";
    this.detailsText.innerText = "Details";

    const detailsFooter = document.createElement("div");
    detailsFooter.classList.add("details-footer");

    const detailsFooterButton = document.createElement("button");
    detailsFooterButton.classList.add("details-footer-button");
    detailsFooterButton.textContent = "Close";
    detailsFooter.append(detailsFooterButton);
    detailsFooterButton.onclick = (): void => {
      this.handleDetailsToggle();
    };

    this.detailsPanel.appendChild(this.detailsContainer);

    this.graphPropertiesTable.classList.add("properties-table");

    this.graphTableDiv.classList.add("properties-content", "displayNone");
    this.graphTableDiv.append(this.graphPropertiesTable);
    this.emptyDetailsMessage.textContent =
      "Select a single node or edge to see more.";
    this.emptyDetailsMessage.classList.add("emptyDetails");

    this.resizeHandle.classList.add("resizeHandle");
    this.detailsContainer.append(
      this.detailsHeader,
      this.emptyDetailsMessage,
      this.graphTableDiv,
      detailsFooter
    );

    this.expandBtn.innerHTML = feather.icons["maximize-2"].toSvg();
    this.expandBtn.title = "Fullscreen";
    this.expandBtn.onclick = (): void => {
      this.toggleExpand();
    };
    this.expandDiv.appendChild(this.expandBtn);
    rightActions.append(this.expandDiv);

    const dragOptions: DraggableOptions = new ForceDraggableOptions();
    dragOptions.handle = ".details-header";
    dragOptions.containment = "parent";
    $(this.detailsPanel).draggable(dragOptions);
    
    const resizeOptions: ResizableOptions = new ForceResizableOptions();
    resizeOptions.handles = "s, e, w, se, sw";
    resizeOptions.resize = (event, ui): void => {
      this.detailsContainer.style.height = ui.size.height.toString() + "px";
      this.detailsContainer.style.width = ui.size.width.toString() + "px";
    };
    $(this.detailsPanel).resizable(resizeOptions);

    const zoomInDiv = document.createElement("div");
    const zoomOutDiv = document.createElement("div");
    const zoomResetDiv = document.createElement("div");

    const zoomInButton = document.createElement("button");
    zoomInButton.title = "Zoom In";
    zoomInButton.onclick = () => {
      const currentZoom = this.graph.zoom();
      this.graph.zoom(currentZoom * 1.2, 400);
    };

    const zoomOutButton = document.createElement("button");
    zoomOutButton.title = "Zoom Out";
    zoomOutButton.onclick = () => {
      const currentZoom = this.graph.zoom();
      this.graph.zoom(currentZoom * 0.8, 400);
    };
    const zoomResetButton = document.createElement("button");
    zoomResetButton.title = "Reset Zoom to Fit";
    zoomResetButton.onclick = () => {
      this.graph.zoomToFit(400, 40);
    };

    zoomInButton.innerHTML = feather.icons["zoom-in"].toSvg();
    zoomOutButton.innerHTML = feather.icons["zoom-out"].toSvg();
    zoomResetButton.innerHTML = feather.icons["square"].toSvg();

    zoomInDiv.classList.add("menu-action", "zoom-in-div");
    zoomOutDiv.classList.add("menu-action", "zoom-out-div");
    zoomResetDiv.classList.add("menu-action", "zoom-reset-div");
    zoomInDiv.append(zoomInButton);
    zoomOutDiv.append(zoomOutButton);
    zoomResetDiv.append(zoomResetButton);

    const bottomRightActions = document.createElement("div");
    bottomRightActions.classList.add("bottom-right");
    bottomRightActions.append(zoomInDiv, zoomResetDiv, zoomOutDiv);
    this.networkDiv.append(bottomRightActions);
  }

  handleDetailsToggle(): void {
    this.detailsBtn.classList.toggle("active");
    this.detailsPanel.classList.toggle("hidden");
  }

  /**
   * Search the provided data for an instance of the given text
   * @param text - the search term
   * @param data - data to be searched
   * @param excludeIDs - boolean indicating whether we want to highlight ID matches
   */
  search(text: string, data: any, depth: number, excludeIDs: boolean): boolean {
    if (Array.isArray(data)) {
      for (let i = 0; i < data.length; i++) {
        if (this.search(text, data[i], depth + 1, excludeIDs)) {
          return true;
        }
      }
      return false;
    } else if (typeof data === "object") {
      let found = false;

      // an object can be null
      if (data === null || data === undefined) {
        return found;
      }

      Object.entries(data).forEach((entry) => {
        if (found) {
          return true;
        }

        // we want to ignore the top level set of properties on an object except for "properties"
        // because otherwise we would search for vis-specific settings.
        if (depth === 0) {
          // Also include top level label, in case of label by ID
          if (["properties", "label"].includes(entry[0].toString())) {
            found = this.search(text, entry[1], depth + 1, excludeIDs);
          } else {
            console.log("Not properties or label key, ignoring.");
          }
        } else {
          if (
            !(
              this.excludeIDsFromSearch &&
              [
                "~id",
                "~start",
                "~end",
                "T.id",
                "Direction.IN",
                "Direction.OUT",
              ].includes(entry[0].toString())
            )
          ) {
            found = this.search(text, entry, depth + 1, excludeIDs);
          } else {
            console.log("entry[0] is ID property, skipping.");
          }
        }
      });
      return found;
    } else if (data === null || data === undefined) {
      return false;
    } else {
      // If recursion reached variable not a map or array, check it.
      return data.toString().indexOf(text) !== -1;
    }
  }

  /**
   * Take this widget to full screen mode, ensuring that the positioning of the details
   * panel remains in the same relative position that it was in before full screen mode.
   */
  toggleExpand(): void {
    const elem = this.networkDiv;

    const doc_fullScreenElement_multibrowser = document as Document & {
      webkitFullscreenElement?: Element;
      mozFullScreenElement?: Element;
      msFullscreenElement?: Element;
    }
    const elem_requestFullscreen_multibrowser = document.documentElement as HTMLElement & {
      mozRequestFullScreen(): Promise<void>;
      webkitRequestFullscreen(): Promise<void>;
      msRequestFullscreen(): Promise<void>;
    };
    const doc_exitFullscreen_multibrowser = document as Document & {
      mozCancelFullScreen(): Promise<void>;
      webkitExitFullscreen(): Promise<void>;
      msExitFullscreen(): Promise<void>;
    };

    const fullScreenElement_multibrowser =
      doc_fullScreenElement_multibrowser.fullscreenElement ||
      doc_fullScreenElement_multibrowser.webkitFullscreenElement ||
      doc_fullScreenElement_multibrowser.mozFullScreenElement ||
      doc_fullScreenElement_multibrowser.msFullscreenElement;
    const requestFullscreen_multibrowser =
      elem_requestFullscreen_multibrowser.requestFullscreen ||
      elem_requestFullscreen_multibrowser.mozRequestFullScreen ||
      elem_requestFullscreen_multibrowser.webkitRequestFullscreen ||
      elem_requestFullscreen_multibrowser.msRequestFullscreen;
    const exitFullscreen_multibrowser =
      doc_exitFullscreen_multibrowser.exitFullscreen ||
      doc_exitFullscreen_multibrowser.webkitExitFullscreen ||
      doc_exitFullscreen_multibrowser.msExitFullscreen ||
      doc_exitFullscreen_multibrowser.mozCancelFullScreen;

    const fullscreenchange = (event) => {
      const detailsTop = parseInt(this.detailsPanel.style.top);
      const detailsLeft = parseInt(this.detailsPanel.style.left);
      if (fullScreenElement_multibrowser) {
        this.detailsPanel.style.left =
          (detailsLeft / 650) * window.innerWidth + "px";
        this.detailsPanel.style.top =
          (detailsTop / 650) * window.innerHeight + "px";
        this.expandBtn.innerHTML = feather.icons["minimize-2"].toSvg();
        this.expandBtn.title = "Exit Fullscreen";
      } else {
        this.detailsPanel.style.left =
          (detailsLeft / window.innerWidth) * 650 + "px";
        const top = (detailsTop / window.innerHeight) * 650;
        const newTop =
          this.detailsPanel.offsetHeight + top < 650
            ? top
            : top - this.detailsPanel.offsetHeight;
        this.detailsPanel.style.top = newTop + "px";
        console.log(newTop);

        this.expandBtn.innerHTML = feather.icons["maximize-2"].toSvg();
        this.expandBtn.title = "Fullscreen";
        document.removeEventListener("fullscreenchange", fullscreenchange);
      }
      this.expandBtn.classList.toggle("active");
    };
    if (!fullScreenElement_multibrowser) {
      if (requestFullscreen_multibrowser) {
        document.addEventListener("fullscreenchange", fullscreenchange);
        requestFullscreen_multibrowser.call(elem);
        this.canvasDiv.style.height = "100%";
      }
    } else {
      if (exitFullscreen_multibrowser) {
        exitFullscreen_multibrowser.call(document);
        this.canvasDiv.style.height = "600px";
      }
    }

    return;
  }

  /**
   * Register any needed events to this.el, the containing element for this widget
   */
  registerWidgetEvents(): void {
    const observerConfig = {
      attributes: true,
      childList: false,
      subtree: true,
    };
    let observer: MutationObserver;
    const observerCallback = (mutationsList, observer) => {
      for (const mutation of mutationsList) {
        if (mutation.type === "attributes") {
          if (
            mutation.attributeName === "width" &&
            mutation.oldValue === null &&
            mutation.target[mutation.attributeName] !== null &&
            mutation.target[mutation.attributeName] !== undefined &&
            mutation.target[mutation.attributeName] > 0
          ) {
            this.graph?.zoomToFit(400);
            observer.disconnect();
          }
        }
      }
    };
  
    observer = new MutationObserver(observerCallback);
    observer.observe(this.el, observerConfig);
  }
}
