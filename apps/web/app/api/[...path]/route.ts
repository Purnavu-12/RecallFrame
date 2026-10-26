import type { NextRequest } from "next/server";

export const runtime = "nodejs";
export const dynamic = "force-dynamic";

async function proxy(
  request: NextRequest,
  context: { params: Promise<{ path: string[] }> },
) {
  const requestOrigin = request.headers.get("origin");
  // `nextUrl.origin` is Next's container listener origin (0.0.0.0:3000)
  // in Docker, not the browser-facing loopback host and port.
  const host = request.headers.get("host");
  const publicOrigin = host
    ? `${request.nextUrl.protocol}//${host}`
    : request.nextUrl.origin;
  if (
    requestOrigin &&
    requestOrigin !== publicOrigin &&
    request.method !== "GET" &&
    request.method !== "HEAD"
  ) {
    return Response.json(
      { detail: "Cross-origin changes are not allowed." },
      { status: 403 },
    );
  }
  const { path } = await context.params;
  const apiOrigin = process.env.API_BASE_URL ?? "http://127.0.0.1:8000";
  const target = new URL(
    `/api/${path.map(encodeURIComponent).join("/")}`,
    apiOrigin,
  );
  target.search = request.nextUrl.search;
  const headers = new Headers();
  for (const name of ["accept", "content-type", "range", "if-range"]) {
    const value = request.headers.get(name);
    if (value) headers.set(name, value);
  }

  const init: RequestInit & { duplex?: "half" } = {
    method: request.method,
    headers,
    cache: "no-store",
    redirect: "manual",
  };
  if (request.method !== "GET" && request.method !== "HEAD") {
    init.body = request.body;
    init.duplex = "half";
  }

  try {
    const upstream = await fetch(target, init);
    const responseHeaders = new Headers();
    for (const name of [
      "content-type",
      "content-length",
      "content-range",
      "accept-ranges",
      "cache-control",
    ]) {
      const value = upstream.headers.get(name);
      if (value) responseHeaders.set(name, value);
    }
    return new Response(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch {
    return Response.json(
      {
        detail:
          "RecallFrame API is unavailable. Start the local stack and try again.",
      },
      { status: 503 },
    );
  }
}

export const GET = proxy;
export const HEAD = proxy;
export const POST = proxy;
export const PUT = proxy;
export const PATCH = proxy;
export const DELETE = proxy;
