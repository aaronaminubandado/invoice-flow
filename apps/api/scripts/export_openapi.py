"""Export OpenAPI schema for packages/api-types generation."""
import json
import os
import sys
from pathlib import Path

API_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(API_ROOT))

# Importing the application constructs the SQLAlchemy engine, but exporting the
# schema does not connect to it. Supply a valid local-shaped URL for clean
# checkouts where no .env exists.
if not os.getenv("DATABASE_URL"):
    os.environ["DATABASE_URL"] = (
        "postgresql+asyncpg://postgres:postgres@localhost:5432/invoiceflow"
    )

from app.main import app  # noqa: E402

out = API_ROOT / "openapi.json"
out.write_text(json.dumps(app.openapi(), indent=2))
print(f"Wrote {out}")
