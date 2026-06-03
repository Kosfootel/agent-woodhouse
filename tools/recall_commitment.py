#!/usr/bin/env python3
"""Recall commitments by query or ID.

Usage:
    python tools/recall_commitment.py "A2A protocol"        # Search
    python tools/recall_commitment.py --id dec-2026-05-17-001  # Exact lookup
"""

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.commitment_tracker import CommitmentStore

def main():
    parser = argparse.ArgumentParser(description="Recall commitments")
    parser.add_argument("query", nargs="?", help="Search query")
    parser.add_argument("--id", help="Exact commitment ID")
    parser.add_argument("--exact", action="store_true", help="Exact match")
    parser.add_argument("--conflicts", action="store_true", help="Show conflicts")
    parser.add_argument("--limit", type=int, default=10, help="Result limit")
    
    args = parser.parse_args()
    
    store = CommitmentStore()
    
    if args.conflicts:
        conflicts = store.list_conflicts()
        print(f"\nPotential Conflicts: {len(conflicts)}")
        for c in conflicts:
            print(f"\n  {c['commitment_a']} vs {c['commitment_b']}")
            print(f"    A: {c['text_a'][:50]}...")
            print(f"    B: {c['text_b'][:50]}...")
        return
    
    if args.id:
        commitment = store.get_by_id(args.id)
        if commitment:
            print(f"\n✓ Found commitment {commitment.id}:")
            print(f"  Text: {commitment.commitment}")
            print(f"  Timestamp: {commitment.timestamp}")
            print(f"  Source: {commitment.source['agent']}, session {commitment.source['session']}")
            print(f"  Message ID: {commitment.source['message_id']}")
            print(f"  Status: {commitment.status}")
            if commitment.context:
                print(f"  Context: {commitment.context}")
        else:
            print(f"✗ Commitment {args.id} not found")
        return
    
    if not args.query:
        print("Error: Provide a query or --id")
        sys.exit(1)
    
    results = store.recall(args.query, exact=args.exact)
    
    if not results:
        print(f"\nNo commitments found for '{args.query}'")
        return
    
    print(f"\nFound {len(results[:args.limit])} commitment(s) for '{args.query}':")
    print("=" * 60)
    
    for r in results[:args.limit]:
        print(f"\n📌 {r.id} ({r.status})")
        print(f"   '{r.commitment[:80]}{'...' if len(r.commitment) > 80 else ''}'")
        print(f"   ↳ {r.source['agent']}, message {r.source['message_id']}")
        if r.context:
            print(f"   Context: {r.context[:60]}...")

if __name__ == "__main__":
    main()
