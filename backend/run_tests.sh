#!/bin/bash
export DATABASE_URL=sqlite+aiosqlite:///./test.db
export PYTHONPATH=$PYTHONPATH:$(pwd)/..
pytest tests -v
