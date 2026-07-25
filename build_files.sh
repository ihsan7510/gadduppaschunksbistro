#!/bin/bash
echo "Creating virtual environment..."
python3 -m venv venv
source venv/bin/activate

echo "Installing dependencies..."
pip install -r requirements.txt

echo "Collecting static files..."
python3 manage.py collectstatic --no-input --clear

echo "Running database migrations..."
python3 manage.py migrate --no-input

echo "Seeding initial data..."
python3 seed_data.py

echo "Deactivating virtual environment..."
deactivate
