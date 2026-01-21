#!/bin/bash

alembic upgrade head
PYTHONPATH=. python btc_challenge/main.py