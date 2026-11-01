#!/bin/bash
echo "Starting CrisisMind Python Backend..."
cd backend
[ -f .env ] || cp .env.example .env
python -m pip install -r requirements.txt
python main.py
