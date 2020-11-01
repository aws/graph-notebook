"""
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
"""
import graph_notebook
from graph_notebook.network.EventfulNetwork import EventfulNetwork
from graph_notebook.options import OPTIONS_DEFAULT_DIRECTED
from traitlets import Unicode, Dict, Instance
from ipywidgets import DOMWidget, register

MAX_LABEL_LENGTH = 10


def graph_to_json(network: EventfulNetwork, trait):
    return network.to_json()


@register
class Force(DOMWidget):
    """
    Custom widget meant to render a network as a graph.

    A Jupyter widget has three primary pieces. One which exists on the iPython Kernel (this class) and two which
    exist on the browser (under ../js/lib/widgets.js in this case). When rendering a widget, this class's fields
    _view_name and _view_module tell the browser where to find its view class, and _model_name and _model_module tell
    the browser where to find its model class.

    Under ../js/lib/widgets.js you will find that we define the module "graph_notebook_widgets" which is both our
    _view_module and _model_module. This module exports two classes "ForceView" which corresponds to _view_name
    and "ForceModel" which corresponds to _model_name.

    The "ForceModel" also contains this same information, including version info.

    A custom widget can have fields in it known as "traitlets" which can be tagged with various features. The two
    we make use of are "sync" which tells the kernel to trigger events when a traitlet is overridden
    (NOTE: NOT TRIGGERED WHEN YOU APPEND OR CHANGE AN INNER FIELD), and "to_json" which can override how that sync takes place.
    For traitlets of type Instance, this must be overriden so that the kernel knows how to serialize the overrides that are
    triggered when "sync" is set to True.

    After metadata fields, we have three other fields which are used to sync state between the front-end and kernel.
    1. options -> The visjs physics options to use when rendering our network.
        - See https://visjs.github.io/vis-network/docs/network/#options for more info.
    2. message -> Notification system to tell the user what actions have taken place. For example, issuing a query for the user to gather more data.
    3. network -> The instance of an EventfulNetwork which will trigger messages to the front-end whenever methods are called to modify the underlying graph.

    By default, we will register one placeholder event which will trigger on all method calls of the network traitlet.
    This will wrap the parameters of the method call with an event and send it as a message to the front-end to keep the
    browser network in sync.

    You can find more information on Widgets here: https://ipywidgets.readthedocs.io/en/latest/examples/Widget%20Basics.html
    """
    # Name of the widget view class in front-end
    _view_name = Unicode('ForceView').tag(sync=True)

    # Name of the widget model class in front-end
    _model_name = Unicode('ForceModel').tag(sync=True)

    # Name of the front-end module containing widget view
    _view_module = Unicode('graph_notebook_widgets').tag(sync=True)

    # Name of the front-end module containing widget model
    _model_module = Unicode('graph_notebook_widgets').tag(sync=True)

    # Version of the front-end module containing widget view
    _view_module_version = Unicode(graph_notebook.__version__).tag(sync=True)
    # Version of the front-end module containing widget model
    _model_module_version = Unicode(graph_notebook.__version__).tag(sync=True)

    options = Dict().tag(sync=True)
    message = Unicode().tag(sync=True)
    network = Instance(klass=EventfulNetwork).tag(sync=True, to_json=graph_to_json)

    def __init__(self, network: EventfulNetwork = EventfulNetwork(), options: dict = OPTIONS_DEFAULT_DIRECTED,
                 with_callback: bool = True, **kwargs):
        if with_callback:
            network.register_universal_callback(self.eventful_network_callback)

        super().__init__(network=network, options=options, **kwargs)

    def eventful_network_callback(self, network, event_name, data):
        pass
