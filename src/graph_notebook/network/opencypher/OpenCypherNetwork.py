from networkx import MultiDiGraph

from graph_notebook.network.EventfulNetwork import EventfulNetwork, DEFAULT_LABEL_MAX_LENGTH


class OpenCypherNetwork(EventfulNetwork):
    def __init__(self, graph: MultiDiGraph = None, callbacks=None, label_max_length=DEFAULT_LABEL_MAX_LENGTH):
        if graph is None:
            graph = MultiDiGraph()
        self.label_max_length = label_max_length
        super().__init__(graph, callbacks)

    def add_results(self, results):
        """
        receives a query result, and decides between a few options for
        formats including:

        1. Direct node/edge materialization

        """