#!/usr/bin/env python3
"""Batch runner: run BossFinder for a list of companies and save results to output/."""

import sys
import json
import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

from src.bossfinder.crew import run_bossfinder

COMPANIES = [
    ("NVIDIA", "nvidia"),
    ("Microsoft Azure", "microsoft-azure"),
    ("Amazon AWS", "amazon-aws"),
    ("Alphabet Google Cloud", "alphabet-google-cloud"),
    ("Broadcom", "broadcom"),
    ("SK Hynix", "sk-hynix"),
    ("Micron Technology", "micron-technology"),
    ("Super Micro Computer", "super-micro-computer"),
    ("Lambda Labs", "lambda-labs"),
]

output_dir = Path(__file__).parent / "output"
output_dir.mkdir(exist_ok=True)

start_index = int(sys.argv[1]) if len(sys.argv) > 1 else 0

for company_name, slug in COMPANIES[start_index:]:
    out_file = output_dir / f"{slug}.json"
    if out_file.exists():
        print(f"\n[SKIP] {company_name} already exists at {out_file}")
        continue

    print(f"\n{'='*60}")
    print(f"[RUN] BossFinder: {company_name}")
    print(f"{'='*60}")
    try:
        result = run_bossfinder(company_name)
        data = result.model_dump()
        out_file.write_text(json.dumps(data, indent=2))
        print(f"[OK]  Saved {len(result.people)} people to {out_file}")
    except Exception as e:
        err_msg = str(e)
        print(f"[ERROR] {company_name}: {err_msg}")
        if any(kw in err_msg.lower() for kw in ("credit", "quota", "billing", "insufficient", "rate limit", "429")):
            print("[STOP] Stopping due to API credit/quota issue.")
            sys.exit(1)
        # Save partial error info
        out_file.write_text(json.dumps({"company": company_name, "error": err_msg}, indent=2))
        print(f"[WARN] Error saved to {out_file}, continuing...")

print("\n[DONE] Batch complete.")
