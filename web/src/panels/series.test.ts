import { beforeEach, describe, expect, it } from "vitest";

import { history, record, reset } from "./series";

describe("price series", () => {
  beforeEach(reset);

  it("starts empty and ignores missing prices", () => {
    record("AAPL", null);
    record("AAPL", undefined);
    record("AAPL", Number.NaN);
    expect(history("AAPL")).toEqual([]);
  });

  it("keeps symbols apart", () => {
    record("AAPL", 1);
    record("MSFT", 2);
    expect(history("AAPL")).toEqual([1]);
    expect(history("MSFT")).toEqual([2]);
  });

  it("drops a repeated price so a closed market draws nothing", () => {
    record("AAPL", 10);
    record("AAPL", 10);
    record("AAPL", 10);
    expect(history("AAPL")).toEqual([10]);
  });

  it("keeps a value that returns after a move", () => {
    for (const p of [10, 11, 10]) record("AAPL", p);
    expect(history("AAPL")).toEqual([10, 11, 10]);
  });

  it("bounds the buffer, keeping the newest points", () => {
    for (let i = 0; i < 60; i++) record("AAPL", i);
    const points = history("AAPL");
    expect(points).toHaveLength(40);
    expect(points[points.length - 1]).toBe(59);
    expect(points[0]).toBe(20);
  });
});
