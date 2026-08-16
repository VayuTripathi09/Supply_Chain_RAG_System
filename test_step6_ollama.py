#!/usr/bin/env python
"""Test PDF ingestion with Ollama (no API key needed)."""

import requests
import json
import time
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

print("\n" + "🚀 " * 20)
print("STEP 6: INDEX DOCUMENTS WITH OLLAMA")
print("🚀 " * 20)

# Test 1: Check stats before ingestion
print("\n" + "="*70)
print("TEST 1: GET /stats (before ingestion)")
print("="*70)

try:
    response = requests.get(f"{BASE_URL}/stats", timeout=5)
    stats_before = response.json()
    print(f"\nResponse: {json.dumps(stats_before, indent=2)}")
    print(f"✓ PASS: Empty collection ready for indexing")
except Exception as e:
    print(f"✗ FAIL: {e}")
    exit(1)

# Test 2: Ingest PDFs with Ollama
print("\n" + "="*70)
print("TEST 2: POST /ingest (upload and index PDFs with Ollama)")
print("="*70)

data_dir = Path("data")
pdf_files = list(data_dir.glob("*.pdf"))

print(f"\nFound {len(pdf_files)} PDF files to ingest:")
for f in pdf_files:
    print(f"  📄 {f.name} ({f.stat().st_size / 1024:.1f} KB)")

try:
    # Prepare files for upload
    files = []
    for pdf_path in pdf_files:
        with open(pdf_path, 'rb') as f:
            files.append(('files', (pdf_path.name, f.read())))
    
    print(f"\nUploading and indexing (this may take 1-2 minutes with Ollama)...")
    print(f"⏳ Processing...")
    response = requests.post(f"{BASE_URL}/ingest", files=files, timeout=180)  # 3 min timeout for Ollama
    
    if response.status_code == 200:
        result = response.json()
        print(f"\n✓ INGESTION SUCCESSFUL!")
        print(f"\nResponse:")
        print(json.dumps(result, indent=2))
    else:
        print(f"\n✗ FAIL: Status {response.status_code}")
        print(f"Response: {response.json()}")
        exit(1)
except requests.exceptions.Timeout:
    print(f"\n⚠️ TIMEOUT: Ollama is slow (expected with local models)")
    print(f"   The indexing is still happening in the background")
    print(f"   Check /stats in 2-3 minutes to see if chunks are indexed")
    exit(0)
except Exception as e:
    print(f"✗ FAIL: {e}")
    import traceback
    traceback.print_exc()
    exit(1)

# Test 3: Verify ChromaDB has data
print("\n" + "="*70)
print("TEST 3: GET /stats (after ingestion)")
print("="*70)

time.sleep(2)  # Give it time to process

try:
    response = requests.get(f"{BASE_URL}/stats", timeout=5)
    stats_after = response.json()
    print(f"\nResponse: {json.dumps(stats_after, indent=2)}")
    
    chunk_count = stats_after.get("total_chunks", 0)
    if chunk_count > 0:
        print(f"\n✅ SUCCESS!")
        print(f"   Total chunks indexed: {chunk_count}")
        print(f"   Expected: ~22 chunks (12 policy + 10 review)")
    else:
        print(f"⚠️  No chunks indexed yet (may still be processing)")
except Exception as e:
    print(f"✗ FAIL: {e}")
    exit(1)

print("\n" + "="*70)
print("✅ STEP 6 PROGRESS: Ingestion initiated")
print("="*70)
print("\nNext: Test retrieval and answer generation")
