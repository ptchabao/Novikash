#!/bin/bash

# Setup script for NoviKash Fintech API

echo "Creating virtual environment..."
python3 -m venv venv

echo "Activating virtual environment..."
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Setup complete! You can now run the app with:"
echo "venv/bin/uvicorn app.main:app --reload"
