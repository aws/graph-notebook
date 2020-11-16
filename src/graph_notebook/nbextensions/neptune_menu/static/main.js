/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

define([
    'base/js/namespace',
    'base/js/events',
], function(Jupyter, events) {
    const seedKernelValues = (host, port, iam, ssl) => {
        const kernel = IPython.notebook.kernel;
        const command = 'host=\'' + host + '\'\n' +
            'port=\'' + port + '\'\n' +
            'ssl=\'' + ssl + '\'\n' +
            'iam=\'' + iam + '\'';
        kernel.execute(command);
    };

    const addMenuItems = (host, port, iam, ssl) => {
        const neptuneMenuItem = document.createElement("li");
        neptuneMenuItem.className = "dropdown";

        // name of menu item
        const dropDownToggle = document.createElement('a');
        dropDownToggle.className = "dropdown-toggle";
        dropDownToggle.setAttribute("href", "#");
        dropDownToggle.setAttribute("data-toggle", "dropdown");
        const neptuneMenuName = document.createTextNode("Neptune");
        dropDownToggle.appendChild(neptuneMenuName);

        // options for menu item
        const ul = document.createElement('ul');
        ul.style.minWidth = "30em";
        ul.id = "neptune_menu";
        ul.className = "dropdown-menu";
        const textNode = document.createTextNode("menu_item");

        // menu items
        // host menu item
        const hostLi = document.createElement('li');
        hostLi.style.marginLeft = '5px';
        hostLi.id = "neptune_host";
        const hostDiv = document.createElement('div');
        const hostLabel = document.createElement('label');
        const hostLabelContent = document.createTextNode("Host: " + host);
        hostLabel.overflow = 'scroll';
        hostLabel.appendChild(hostLabelContent);
        hostDiv.appendChild(hostLabel);
        hostLi.appendChild(hostDiv);

        // port menu item
        const portLi = document.createElement('li');
        portLi.id = "neptune_port";
        portLi.style.marginLeft = '5px';
        const portDiv = document.createElement('div');
        const portLabel = document.createElement('label');
        const portLabelContent = document.createTextNode("Port: " + port);
        portLabel.appendChild(portLabelContent);
        portDiv.appendChild(portLabel);
        portLi.appendChild(portDiv);

        // iam menu item
        const iamLi = document.createElement('li');
        iamLi.id = "neptune_iam";
        iamLi.style.marginLeft = '5px';
        const iamDiv = document.createElement('div');
        const iamLabel = document.createElement('label');
        const iamLabelContent = document.createTextNode("IAM Auth: " + iam);
        iamLabel.appendChild(iamLabelContent);
        iamDiv.appendChild(iamLabel);
        iamLi.appendChild(iamDiv);

        //ssl menu item
        const sslLi = document.createElement('li');
        sslLi.id = "neptune_ssl";
        sslLi.style.marginLeft = '5px';
        const sslDiv = document.createElement('div');
        const sslLabel = document.createElement('label');
        const sslLabelContent = document.createTextNode("SSL: " + ssl);
        sslLabel.appendChild(sslLabelContent);
        sslDiv.appendChild(sslLabel);
        sslLi.appendChild(sslDiv);

        // append all the menu items
        ul.appendChild(hostLi);
        ul.appendChild(portLi);
        ul.appendChild(iamLi);
        ul.appendChild(sslLi);

        neptuneMenuItem.appendChild(dropDownToggle);
        neptuneMenuItem.appendChild(ul);

        // add to nav bar
        const navBar = document.getElementsByClassName("nav navbar-nav")[0];
        navBar.appendChild(neptuneMenuItem);

    };

    const callbacks = {
        iopub : {
            output : configCallback,
        }
    };

    let host='', port='', iam='off', ssl='on';

    function configCallback(data){
        console.log('neptune menu callback...');
        const raw = data['content']['text'];
        const config = JSON.parse(raw);
        host = config['host'];
        port = config['port'];
        if(config['auth_mode'] === "IAM"){
            iam = 'on';
        }

        if (config['ssl']){
            ssl = 'on';
        } else {
            ssl = 'off';
        }

        seedKernelValues(host, port, iam, ssl);
        addMenuItems(host, port, iam, ssl)
    }

    const createMenu = (kernel) => {
        console.log("kernel type is ", kernel.name);
        if(kernel.name === "gremlin_kernel" || kernel.name === "sparql_kernel"){
            console.log("skipping neptune menu creation");
            return;
        }
        console.log('creating neptune menu from config...');
        kernel.execute('%load_ext graph_notebook.magics');
        kernel.execute(
            "%graph_notebook_config silent",
            callbacks);
    };

    if (Jupyter.notebook.kernel) {
        createMenu(Jupyter.notebook.kernel);
    } else {
        Jupyter.notebook.events.one('kernel_ready.Kernel', (e) => {
            createMenu(Jupyter.notebook.kernel);
        });
    }
    console.log('finished setup for neptune_menu');
});