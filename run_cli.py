#!/usr/bin/env python3
"""Quick CLI to run BossFinder without the API server."""

import sys
import json
from dotenv import load_dotenv

load_dotenv()

from src.bossfinder.crew import run_bossfinder


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_cli.py <company name>")
        sys.exit(1)

    company = " ".join(sys.argv[1:])
    print(f"\n🔍 BossFinder: searching for key people at '{company}'...\n")

    result = run_bossfinder(company)

    print(f"\n{'='*60}")
    print(f"Results for: {result.company}")
    print(f"Total unique people found: {result.search_metadata.get('total_unique_people', len(result.people))}")
    print(f"{'='*60}\n")

    print(json.dumps(result.model_dump(), indent=2))


if __name__ == "__main__":
    main()
