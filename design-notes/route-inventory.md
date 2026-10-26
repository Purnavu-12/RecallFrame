# Route inventory

| Route | User goal | Data contract |
| --- | --- | --- |
| `/` | Browse/import the private video library | `GET /api/videos`, upload/import |
| `/videos/[id]` | Play source, browse transcript/chapters, ask grounded questions | video detail, stream, questions, insights |
| `/search` | Search across indexed transcripts | `GET /api/search?q=` |
| `/saved` | Revisit and delete saved insights | `GET/POST/DELETE /api/insights` |
| `/map` | Explore evidence-linked concepts | `GET /api/knowledge-map` |
| `/settings` | Inspect local processing and provider state | `GET /api/settings` |

All browser API requests pass through the same-origin Next.js route handler. The API is not published as a host port.
