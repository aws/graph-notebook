/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

define([
    'require',
    'jquery',
    'base/js/namespace',
], function (
    requirejs,
    $,
    Jupyter,
) {
    "use strict";

    var initialize = function () {
        // add our extension's css to the page
        $('<link/>')
            .attr({
                rel: 'stylesheet',
                type: 'text/css',
                href: requirejs.toUrl('./playable_cells.css')
            })
            .appendTo('head');
    };

    var load_ipython_extension = function () {
        return Jupyter.notebook.config.loaded.then(initialize);
    };

    // return object to export public methods
    return {
        load_ipython_extension : load_ipython_extension
    };
});