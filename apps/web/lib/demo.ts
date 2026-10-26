export const demoSegments = [
  {
    id: "demo-segment-1",
    start_ms: 0,
    end_ms: 48_000,
    text: "A browser sends a request to the application. A load balancer is the entry point that receives traffic before it reaches the application servers.",
  },
  {
    id: "demo-segment-2",
    start_ms: 48_000,
    end_ms: 92_000,
    text: "The load balancer chooses a healthy server and distributes requests across the available instances. This gives the system room to handle more traffic.",
  },
  {
    id: "demo-segment-3",
    start_ms: 92_000,
    end_ms: 140_000,
    text: "Health checks help the load balancer stop routing traffic to an instance that is not responding. That can keep one failed server from interrupting every request.",
  },
];

export const demoChapters = [
  { title: "Request path", start_ms: 0, end_ms: 48_000 },
  { title: "Distribute traffic", start_ms: 48_000, end_ms: 92_000 },
  { title: "Health checks", start_ms: 92_000, end_ms: 140_000 },
];
