#!/usr/bin/env python3
"""Capture a commitment from conversation.

Usage:
    python tools/capture_commitment.py "commitment text" --agent Woodhouse --session session_key --message-id 1234
"""

import argparse
import sys
from pathlib import Path

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tools.commitment_tracker import CommitmentStore, detect_commitment

def main():
    parser = argparse.ArgumentParser(description="Capture a commitment")
    parser.add_argument("text", help="The commitment text to capture")
    parser.add_argument("--agent", default="Woodhouse", help="Agent name")
    parser.add_argument("--session", required=True, help="Session key")
    parser.add_argument("--message-id", required=True, help="Message ID")
    parser.add_argument("--context", help="Additional context")
    parser.add_argument("--tags", nargs="+", help="Tags for categorization")
    parser.add_argument("--verify", action="store_true", help="Require verification")
    
    args = parser.parse_args()
    
    store = CommitmentStore()
    
    # Check if this looks like a commitment
    detection = detect_commitment(args.text)
    if not detection:
        print(f"Warning: '{args.text[:50]}...' doesn't match commitment patterns")
        response = input("Capture anyway? (y/n): ")
        if response.lower() != 'y':
            print("Cancelled")
            return
    
    # Capture
    verification = "required" if args.verify else "auto"
    commitment = store.capture(
        text=args.text,
        agent=args.agent,
        session=args.session,
        message_id=args.message_id,
        confidence=detection["confidence"] if detection else 0.5,
        context=args.context,
        verification=verification,
        tags=args.tags
    )
    
    print(f"\n✓ Captured commitment:")
    print(f"  ID: {commitment.id}")
    print(f"  Text: {commitment.commitment[:60]}...")
    print(f"  Source: {commitment.source['agent']}, message {commitment.source['message_id']}")
    print(f"  Status: {commitment.status}")
    
    if verification == "required":
        print(f"  \n⚠️  Verification required before storage")

if __name__ == "__main__":
    main()
