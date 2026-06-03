#!/usr/bin/env python3
"""Fleet Commitment Tracker - Phase 1 Implementation

Tracks Tier 1 commitments: decisions, facts, and explicit statements
with source attribution and verification.
"""

import yaml
import json
import re
from pathlib import Path
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, asdict

COMMITMENTS_DIR = Path("memory/commitments")

@dataclass
class Commitment:
    id: str
    timestamp: str
    source: Dict[str, str]
    commitment: str
    confidence: float
    verification: str  # "auto", "confirmed", "rejected"
    status: str      # "active", "completed", "revoked", "superseded"
    context: Optional[str] = None
    assigned_to: Optional[str] = None
    deadline: Optional[str] = None
    completed_at: Optional[str] = None
    superseded_by: Optional[str] = None
    tags: Optional[List[str]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        d = asdict(self)
        return {k: v for k, v in d.items() if v is not None}

class CommitmentStore:
    def __init__(self, base_dir: str = "memory/commitments"):
        self.base_dir = Path(base_dir)
        self.decisions_dir = self.base_dir / "decisions"
        self.facts_dir = self.base_dir / "facts"
        self.code_dir = self.base_dir / "code-choices"
        self.revoked_dir = self.base_dir / "revoked"
        
        # Create directories
        for d in [self.decisions_dir, self.facts_dir, self.code_dir, self.revoked_dir]:
            d.mkdir(parents=True, exist_ok=True)
    
    def _next_id(self, date_str: str) -> str:
        """Generate next ID for date."""
        pattern = f"dec-{date_str}-"
        existing = []
        for f in self.decisions_dir.glob(f"{date_str}*.yaml"):
            with open(f) as fp:
                data = yaml.safe_load(fp)
                if data:
                    for entry in data:
                        existing.append(entry.get("id", ""))
        
        max_num = 0
        for e in existing:
            if pattern in e:
                try:
                    num = int(e.split("-")[-1])
                    max_num = max(max_num, num)
                except ValueError:
                    pass
        
        return f"{pattern}{max_num + 1:03d}"
    
    def capture(
        self,
        text: str,
        agent: str,
        session: str,
        message_id: str,
        confidence: float = 1.0,
        context: Optional[str] = None,
        verification: str = "auto",
        tags: Optional[List[str]] = None
    ) -> Commitment:
        """Capture a new commitment."""
        now = datetime.now(timezone.utc)
        date_str = now.strftime("%Y-%m-%d")
        
        commitment = Commitment(
            id=self._next_id(date_str),
            timestamp=now.isoformat(),
            source={
                "agent": agent,
                "session": session,
                "message_id": message_id
            },
            commitment=text,
            confidence=confidence,
            verification=verification,
            status="active",
            context=context,
            tags=tags or []
        )
        
        self._append_commitment(commitment, date_str)
        return commitment
    
    def _append_commitment(self, commitment: Commitment, date_str: str):
        """Append commitment to appropriate file."""
        filepath = self.decisions_dir / f"{date_str}-infrastructure.yaml"
        
        existing = []
        if filepath.exists():
            with open(filepath) as f:
                existing = yaml.safe_load(f) or []
        
        existing.append(commitment.to_dict())
        
        with open(filepath, 'w') as f:
            yaml.dump(existing, f, default_flow_style=False, sort_keys=False)
    
    def recall(self, query: str, exact: bool = False) -> List[Commitment]:
        """Search commitments by query."""
        results = []
        
        for filepath in self.decisions_dir.glob("*.yaml"):
            with open(filepath) as f:
                data = yaml.safe_load(f) or []
                for entry in data:
                    text = entry.get("commitment", "")
                    if exact:
                        if query.lower() in text.lower():
                            results.append(Commitment(**entry))
                    else:
                        # Simple keyword matching for now
                        query_words = query.lower().split()
                        text_lower = text.lower()
                        if any(q in text_lower for q in query_words):
                            results.append(Commitment(**entry))
        
        return sorted(results, key=lambda x: x.timestamp, reverse=True)
    
    def get_by_id(self, commitment_id: str) -> Optional[Commitment]:
        """Get exact commitment by ID."""
        # ID format: dec-YYYY-MM-DD-NNN
        parts = commitment_id.split("-")
        if len(parts) < 4:
            return None
        
        date_str = f"{parts[1]}-{parts[2]}-{parts[3]}"
        
        filepath = self.decisions_dir / f"{date_str}-infrastructure.yaml"
        if not filepath.exists():
            return None
        
        with open(filepath) as f:
            data = yaml.safe_load(f) or []
            for entry in data:
                if entry.get("id") == commitment_id:
                    return Commitment(**entry)
        
        return None
    
    def complete(self, commitment_id: str) -> bool:
        """Mark commitment as completed."""
        commitment = self.get_by_id(commitment_id)
        if not commitment:
            return False
        
        # Update logic would go here
        return True
    
    def list_conflicts(self) -> List[Dict[str, Any]]:
        """Detect potential conflicts between commitments."""
        conflicts = []
        
        # Simple conflict detection: look for contradictory terms
        all_commitments = []
        for filepath in self.decisions_dir.glob("*.yaml"):
            with open(filepath) as f:
                data = yaml.safe_load(f) or []
                all_commitments.extend(data)
        
        # Look for pairs that might conflict
        for i, c1 in enumerate(all_commitments):
            for c2 in all_commitments[i+1:]:
                # Example: "not part of core" vs "is part of core"
                if self._might_conflict(c1.get("commitment", ""), c2.get("commitment", "")):
                    conflicts.append({
                        "commitment_a": c1.get("id"),
                        "commitment_b": c2.get("id"),
                        "text_a": c1.get("commitment"),
                        "text_b": c2.get("commitment"),
                        "status": "detected"
                    })
        
        return conflicts
    
    def _might_conflict(self, text1: str, text2: str) -> bool:
        """Heuristic for detecting potential conflicts."""
        # Very simple: look for negation of same terms
        negation_words = ["not", "no", "never", "don't", "won't"]
        
        text1_lower = text1.lower()
        text2_lower = text2.lower()
        
        # If one has negation and other doesn't, might conflict
        t1_has_neg = any(w in text1_lower for w in negation_words)
        t2_has_neg = any(w in text2_lower for w in negation_words)
        
        if t1_has_neg != t2_has_neg:
            # Extract key terms (simplified)
            words1 = set(re.findall(r'\b\w{4,}\b', text1_lower))
            words2 = set(re.findall(r'\b\w{4,}\b', text2_lower))
            overlap = words1 & words2
            if len(overlap) >= 3:
                return True
        
        return False


# Pattern detection for automatic capture
COMMITMENT_PATTERNS = [
    # Explicit decisions
    r"(?i)\b(we will|let's|we should|we need to|i want to|decided to)\b.+",
    # Negations of capability
    r"(?i)\b(is not|are not|will not|won't|don't|doesn't)\s+(?:part of|in|using)\b.+",
    # Task assignments
    r"(?i)\b(you|woodhouse|ray|liz)\s+(should|need to|must|will)\s+.+",
    # Architecture statements
    r"(?i)\b(architecture|design|protocol|approach)\s+(is|will be)\s+.+",
]

def detect_commitment(text: str) -> Optional[Dict[str, Any]]:
    """Check if text contains a commitment pattern."""
    for pattern in COMMITMENT_PATTERNS:
        match = re.search(pattern, text)
        if match:
            return {
                "detected": True,
                "pattern": pattern,
                "matched_text": match.group(0),
                "full_text": text,
                "confidence": 0.7  # Pattern match confidence
            }
    return None


if __name__ == "__main__":
    # Demo
    store = CommitmentStore()
    
    # Test detection
    test_texts = [
        "A2A protocol is not part of our core functionality any longer",
        "We will use the new approach for this project",
        "Just a general statement without commitment",
    ]
    
    print("Testing commitment detection:")
    for text in test_texts:
        result = detect_commitment(text)
        print(f"  '{text[:50]}...' -> {result is not None}")
    
    # Test recall
    print("\nSearching for 'A2A':")
    results = store.recall("A2A")
    for r in results:
        print(f"  {r.id}: {r.commitment[:60]}...")
    
    # Test conflicts
    print("\nChecking for conflicts:")
    conflicts = store.list_conflicts()
    print(f"  Found {len(conflicts)} potential conflicts")
