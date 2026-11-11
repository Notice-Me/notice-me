"""Export the running application's contract without API credentials or network calls."""

import argparse
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from app.config import Settings
from app.main import create_app


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output", type=Path, default=Path(__file__).resolve().parents[2] / "docs/openapi.json"
    )
    args = parser.parse_args()
    with TemporaryDirectory() as folder:
        settings = Settings(_env_file=None, db_path=Path(folder) / "contract.db", data_mode="mock")
        schema = create_app(settings, seed_demo=False).openapi()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(schema, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print("Exported OpenAPI: " + str(args.output))


if __name__ == "__main__":
    main()
