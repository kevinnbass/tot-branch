import re
import sys
import pathlib
import yaml
import difflib

ROOT = pathlib.Path(__file__).parents[1]

PATTERN_YML = ROOT / "multi_coder_analysis" / "regex" / "hop_patterns.yml"
HEADER_TXT = ROOT / "multi_coder_analysis" / "prompts" / "global_header.txt"


def main() -> None:
    try:
        yml = yaml.safe_load(PATTERN_YML.read_text(encoding="utf-8"))
    except Exception as exc:
        print(f"❌  Could not parse YAML: {exc}")
        sys.exit(1)

    header_text = HEADER_TXT.read_text(encoding="utf-8")

    missing = []
    for hop in yml.values():
        for rule in hop:
            name = rule.get("name", "").strip()
            if name and name not in header_text:
                missing.append(name)

    if missing:
        print("❌  Pattern names missing from global_header.txt:\n" + "\n".join(missing))
        sys.exit(1)

    print("✅  YAML patterns mirrored in codebook")


if __name__ == "__main__":
    main() 