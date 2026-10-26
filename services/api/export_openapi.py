"""Export FastAPI's current OpenAPI contract for the web TypeScript client."""
import json
from pathlib import Path

from app.main import app

output = Path(__file__).resolve().parents[2] / "apps" / "web" / "lib" / "generated" / "openapi.json"
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(app.openapi(), indent=2) + "\n", encoding="utf-8")
print(f"Wrote {output}")
