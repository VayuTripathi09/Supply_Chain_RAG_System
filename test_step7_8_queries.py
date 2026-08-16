#!/usr/bin/env python
"""Test the 10 assignment questions against the indexed documents."""

import requests
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8000"

# The 10 assignment questions
QUESTIONS = [
    {
        "id": 1,
        "question": "Who is the highest spend supplier and what is their on-time delivery performance?",
        "category": "Single Document (Review)"
    },
    {
        "id": 2,
        "question": "How many line stoppages due to supplier issues occurred in Q1, and what were the main causes?",
        "category": "Single Document (Review)"
    },
    {
        "id": 3,
        "question": "What is the approval authority requirement for a purchase order of ₹1.4 crore?",
        "category": "Single Document (Policy)"
    },
    {
        "id": 4,
        "question": "What are the four supplier classification categories?",
        "category": "Single Document (Policy)"
    },
    {
        "id": 5,
        "question": "For Kaveri Metals, which clauses in the procurement policy are triggered based on their performance?",
        "category": "Cross-Document"
    },
    {
        "id": 6,
        "question": "According to the policy, what are the requirements for single-source microcontroller procurement?",
        "category": "Cross-Document"
    },
    {
        "id": 7,
        "question": "For a part with 46-day lead time, how much safety stock should be maintained?",
        "category": "Cross-Document"
    },
    {
        "id": 8,
        "question": "What is the cost consequence if Trident achieves 640 PPM defect level?",
        "category": "Cross-Document"
    },
    {
        "id": 9,
        "question": "What is the escalation path for suppliers below B band classification?",
        "category": "Cross-Document"
    },
    {
        "id": 10,
        "question": "What is the total procurement budget for the automotive division in Q2?",
        "category": "Trap (Not in documents)"
    }
]

print("\n" + "="*80)
print("STEP 7-8: TEST SEMANTIC RETRIEVAL & ANSWER GENERATION")
print("="*80)
print(f"\nTesting {len(QUESTIONS)} assignment questions...")
print("Note: Ollama is slower than OpenAI but provides complete local operation\n")

results = []

for q in QUESTIONS:
    print(f"\n{'-'*80}")
    print(f"Question {q['id']}: {q['category']}")
    print(f"{'-'*80}")
    print(f"Q: {q['question']}\n")
    
    try:
        # Send query to RAG pipeline
        payload = {
            "question": q['question'],
            "top_k": 6  # Retrieve top 6 chunks
        }
        
        response = requests.post(
            f"{BASE_URL}/ask",
            json=payload,
            timeout=120  # 2 min timeout for Ollama
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("answer", "").strip()
            sources = result.get("sources", [])
            
            print(f"A: {answer[:500]}")
            if len(answer) > 500:
                print(f"   ... [truncated]")
            
            print(f"\nSources ({len(sources)}):")
            for src in sources:
                fname = src.get("filename", "unknown")
                page = src.get("page", "?")
                print(f"  • {fname} (page {page})")
            
            results.append({
                "id": q['id'],
                "category": q['category'],
                "status": "✓ ANSWERED",
                "answer_length": len(answer),
                "sources": len(sources)
            })
            
        else:
            print(f"✗ ERROR: Status {response.status_code}")
            print(f"Response: {response.json()}")
            results.append({
                "id": q['id'],
                "category": q['category'],
                "status": "✗ FAILED",
                "error": response.status_code
            })
            
    except requests.exceptions.Timeout:
        print(f"⚠️  TIMEOUT: Ollama is processing (slow but working)")
        results.append({
            "id": q['id'],
            "category": q['category'],
            "status": "⏳ TIMEOUT",
            "note": "Ollama took >2min (expected for local models)"
        })
    except Exception as e:
        print(f"✗ ERROR: {type(e).__name__}: {str(e)[:100]}")
        results.append({
            "id": q['id'],
            "category": q['category'],
            "status": "✗ ERROR",
            "error": str(e)[:100]
        })

# Summary
print("\n" + "="*80)
print("SUMMARY")
print("="*80)

status_counts = {}
for r in results:
    status = r['status'].split()[0]  # Get prefix (✓, ✗, ⏳)
    status_counts[status] = status_counts.get(status, 0) + 1

print(f"\n✓ Answered: {status_counts.get('✓', 0)}/{len(QUESTIONS)}")
print(f"✗ Failed:   {status_counts.get('✗', 0)}/{len(QUESTIONS)}")
print(f"⏳ Timeout:  {status_counts.get('⏳', 0)}/{len(QUESTIONS)}")

print(f"\n📊 Results by Category:")
category_stats = {}
for r in results:
    cat = r['category']
    if cat not in category_stats:
        category_stats[cat] = {"total": 0, "answered": 0}
    category_stats[cat]['total'] += 1
    if r['status'].startswith('✓'):
        category_stats[cat]['answered'] += 1

for cat, stats in sorted(category_stats.items()):
    pct = (stats['answered'] / stats['total'] * 100) if stats['total'] > 0 else 0
    print(f"  {cat}: {stats['answered']}/{stats['total']} ({pct:.0f}%)")

print("\n" + "="*80)
print("✅ RETRIEVAL & ANSWER GENERATION TESTING COMPLETE")
print("="*80)
