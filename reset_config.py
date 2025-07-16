#!/usr/bin/env python3
import json
import sys


def reset_config():
    try:

        with open("config.json", "r") as f:

            config = json.load(f)
        if "custom" in config and "personal_info" in config["custom"]:
            personal_info = config["custom"]["personal_info"]

            for key, value in personal_info.items():
                if isinstance(value, str):
                    personal_info[key] = ""
                elif isinstance(value, list):
                    personal_info[key] = []

        if "custom" in config:
            if "words" in config["custom"]:
                config["custom"]["words"] = []
            if "numbers" in config["custom"]:
                config["custom"]["numbers"] = []

        with open("config.json", "w") as f:
            json.dump(config, f, indent=4)

        print("✅ Config reset successfully!")
        print(
            "All personal_info strings, custom words, and custom numbers have been emptied.")

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
