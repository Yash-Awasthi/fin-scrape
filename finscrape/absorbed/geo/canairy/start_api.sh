#!/bin/bash
cd /opt/render/project
export PYTHONPATH="/opt/render/project/src:/opt/render/project:$PYTHONPATH"
python -m uvicorn api.main:app --host 0.0.0.0 --port $PORT