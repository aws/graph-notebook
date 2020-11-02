/*
Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
SPDX-License-Identifier: Apache-2.0
 */

import { Message } from "./types";
import { assert, expect } from "chai";
import { spy } from "sinon";

describe("force_widget", function () {
  describe("Message", function () {
    it("should initalize a message", function () {
      const method = "test";
      const data = { a: 1 };
      const message: Message = new Message(method, data);
      assert.equal(method, message.method);
      assert.deepEqual(data, message.data);
    });
  });

  describe("console", function () {
    it("should log an info", function () {
      const consoleSpy = spy(console, "info");
      const message = "test";
      const data = { a: 1 };
      console.info(message, data);
      expect(consoleSpy.calledWith(message, data)).to.be.ok;
    });
  });
});
