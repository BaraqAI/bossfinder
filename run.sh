#!/usr/bin/env bash
/home/mishka/anaconda3/bin/uvicorn bossfinder.api:app --host 0.0.0.0 --port 8000 --reload
