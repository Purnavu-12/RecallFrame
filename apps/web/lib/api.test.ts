import { describe, expect, it } from "vitest";
import { formatTime } from "./api";

describe("formatTime", () => {
  it("formats short timestamps from milliseconds", () => {
    expect(formatTime(8 * 60_000 + 31_999)).toBe("8:31");
  });

  it("keeps hours when the source is longer than an hour", () => {
    expect(formatTime(3_661_999)).toBe("1:01:01");
  });

  it("clamps fractional milliseconds down to a whole second", () => {
    expect(formatTime(999)).toBe("0:00");
  });
});
