#!/usr/bin/env python3
"""
Generate security/data/modules.json from all modules/*/agent-card.json files.

Reads all agent-card.json files, extracts name, capabilities, and consumers,
and writes a single OPA data document. Re-run whenever agent-card.json changes.

Usage:
    uv run python scripts/gen_opa_data.py
    uv run python scripts/gen_opa_data.py --dry-run

Output:
    security/data/modules.json — OPA data document for capability policies.
    Format: { "modules": { "<module_id>": { "capabilities": [...], "consumers": [...], "url": "..." } } }
"""
import argparse
import json
import pathlib


def collect_agent_cards(modules_root: pathlib.Path) -> dict:
    modules = {}
    for card_path in sorted(modules_root.rglob("agent-card.json")):
        card = json.loads(card_path.read_text())
        module_id = card.get("name") or card_path.parent.name
        # Normalise capabilities to list (some cards use array, some use object)
        caps = card.get("capabilities", [])
        if isinstance(caps, dict):
            caps = [k for k, v in caps.items() if v]
        modules[module_id] = {
            "capabilities": caps,
            "consumers": card.get("consumers", []),
            "url": card.get("url", card.get("endpoints", {}).get("a2a", "")),
        }
    return {"modules": modules}


def main():
    parser = argparse.ArgumentParser(
        description="Generate security/data/modules.json from agent-card.json files."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print generated JSON to stdout instead of writing to disk.",
    )
    args = parser.parse_args()
    repo_root = pathlib.Path(__file__).parent.parent
    data = collect_agent_cards(repo_root / "modules")
    output_path = repo_root / "security" / "data" / "modules.json"
    if args.dry_run:
        print(json.dumps(data, indent=2))
    else:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(data, indent=2))
        print(f"Written: {output_path} ({len(data['modules'])} modules)")


if __name__ == "__main__":
    main()
