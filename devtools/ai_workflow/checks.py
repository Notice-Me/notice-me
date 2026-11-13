"""Fixed local quality checks; no user-supplied shell or test commands."""

import json
import subprocess
import sys


def main():
    checks = {
        "ruff": ["ruff", "check", "server", "devtools"],
        "format": ["ruff", "format", "--check", "server", "devtools"],
        "dependencies": ["pip", "check"],
    }
    for name, args in checks.items():
        try:
            code = subprocess.run(
                [sys.executable, "-m", *args],
                shell=False,
                capture_output=True,
                timeout=30,
                check=False,
            ).returncode
        except subprocess.TimeoutExpired:
            code = 124
        # Raw tool output could contain private paths or secrets.
        print(json.dumps({"check": name, "exit_code": code}))
        if code != 0:
            return code
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
