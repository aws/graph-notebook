/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

/**
 * Theme manager for graph-notebook widgets
 * 
 * Detect and adapt to JupyterLab themes by applying CSS variables from the current Jupyterkab 
 * theme to widget elements.
 */

/**
 * Initialize theme detection and apply the custom theme styles to make the widgets compatible
 * with JupyterLab's themes.
 */
export function initThemeDetection(): void {
  const isJupyterLab = document.body.classList.contains('jp-Notebook') || 
                       document.body.classList.contains('jp-NotebookPanel');
  
  if (!isJupyterLab) {
    console.log('Not running in JupyterLab, skipping theme detection');
    
    return;
  }

  applyThemeStyles();
  
  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      if (mutation.attributeName === 'data-jp-theme-name' || 
          mutation.attributeName === 'class') {
        applyThemeStyles();
      }
    });
  });
  
  // Observe document body for theme change
  observer.observe(document.body, { 
    attributes: true,
    attributeFilter: ['data-jp-theme-name', 'class']
  });
}

/**
 * Apply theme-specific styles
 */
function applyThemeStyles(): void {
  // Update SVG icon stroke
  const featherIcons = document.querySelectorAll('.feather');

  featherIcons.forEach((icon: Element) => {
      (icon as SVGElement).style.stroke = 'var(--icon-stroke)';
  });
}
