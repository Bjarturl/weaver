#!/usr/bin/env python3
import json
import sys


def reset_section(section):
    for key, val in section.items():
        if isinstance(val, dict):
            reset_section(val)
        elif isinstance(val, list):
            section[key] = []
        elif isinstance(val, str):
            section[key] = ""
        else:
            section[key] = None


def reset_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            cfg = json.load(f)

        if "words" in cfg:
            reset_section(cfg["words"])

        with open("config.json", "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=4)

        print("✅ Config reset successfully!")
        print("All values under `words` have been cleared.")
    except FileNotFoundError:
        print("❌ Error: config.json not found")
        sys.exit(1)
    except json.JSONDecodeError:
        print("❌ Error: Invalid JSON in config.json")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    reset_config()
