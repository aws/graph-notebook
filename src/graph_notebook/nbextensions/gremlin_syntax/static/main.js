/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

require(['notebook/js/codecell'], function(codecell) {
    codecell.CodeCell.options_default.highlight_modes['text/x-groovy'] = {'reg':["^%%gremlin"]} ;
    Jupyter.notebook.events.one('kernel_ready.Kernel', function(){
        Jupyter.notebook.get_cells().map(function(cell) {
            if (cell.cell_type === 'code') {
                cell.auto_highlight();
            }
        });
    });
});