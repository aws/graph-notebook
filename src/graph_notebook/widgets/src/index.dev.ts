/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

export * from "./version";
export * from "./force_widget";

if (module.hot) {
  module.hot.accept(function () {
    console.log("new module failed");
  });
}
