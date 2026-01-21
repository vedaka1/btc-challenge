#!/bin/bash

alembic upgrade head
python btc_challenge/main.py