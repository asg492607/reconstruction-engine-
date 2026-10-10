#!/usr/bin/env bash
# Exit on error
set -o errexit

echo "=========================================================="
echo "  RRE 2.0 - Render Free Tier Backend Build Pipeline"
echo "=========================================================="

echo "[1/3] Upgrading pip & Installing Python Dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "[2/3] Preparing Storage & Data Directories..."
mkdir -p data storage

echo "[3/3] Initializing Database Schema & Seeding Law Enforcement Accounts..."
python scripts/init_and_seed.py

echo "=========================================================="
echo "  Backend Build Complete! Starting RRE 2.0 API on Render"
echo "=========================================================="
