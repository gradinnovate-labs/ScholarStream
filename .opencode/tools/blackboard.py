#!/usr/bin/env python3
"""ScholarStream Blackboard - Shared state management for agent coordination"""
import json
import hashlib
from typing import Dict, List, Any, Optional, Callable
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, asdict, field
from threading import Lock
import bisect


@dataclass
class BlackboardEntry:
    agent: str
    content: Any
    timestamp: str
    confidence: float
    tags: List[str] = field(default_factory=list)
    entry_type: str = "info"

    def to_dict(self) -> Dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'BlackboardEntry':
        return cls(**data)

    def get_id(self) -> str:
        content_str = json.dumps(self.content, sort_keys=True, default=str)
        hash_input = f"{self.agent}{self.timestamp}{content_str}"
        return hashlib.md5(hash_input.encode()).hexdigest()[:12]


class ScholarStreamBlackboard:
    DEFAULT_STORAGE_PATH = "database/blackboard.json"

    def __init__(self, storage_path: Optional[str] = None):
        self.entries: List[BlackboardEntry] = []
        self.knowledge_base: Dict[str, Any] = {}
        self.subscribers: Dict[str, Any] = {}
        self.lock = Lock()
        self.storage_path = Path(storage_path) if storage_path else Path(self.DEFAULT_STORAGE_PATH)
        self._dirty = False
        if self.storage_path:
            self._load_from_disk()
            self._dirty = False

    def post(self, agent: str, content: Any,
             confidence: float = 1.0, tags: Optional[List[str]] = None,
             entry_type: str = "info") -> BlackboardEntry:
        entry = BlackboardEntry(
            agent=agent,
            content=content,
            timestamp=datetime.now().isoformat(),
            confidence=confidence,
            tags=tags or [],
            entry_type=entry_type
        )

        with self.lock:
            # Use insert + sort for compatibility (bisect.insort with key is Python 3.10+ only)
            self.entries.append(entry)
            self.entries.sort(key=lambda e: e.timestamp)
            self._notify_subscribers(entry)
            self._dirty = True

        return entry

    def query(self, agent: str, query_tags: List[str],
              since: Optional[str] = None,
              entry_type: Optional[str] = None,
              min_confidence: float = 0.0,
              max_results: int = 50) -> List[BlackboardEntry]:
        with self.lock:
            results = []

            for entry in self.entries:
                if since and entry.timestamp <= since:
                    continue

                if entry_type and entry.entry_type != entry_type:
                    continue

                if entry.confidence < min_confidence:
                    continue

                if not self._matches_tags(entry.tags, query_tags):
                    continue

                results.append(entry)

        sorted_results = sorted(results, key=lambda e: e.confidence, reverse=True)
        return sorted_results[:max_results]

    def get_latest_by_agent(self, agent: str, limit: int = 10) -> List[BlackboardEntry]:
        with self.lock:
            agent_entries = [e for e in self.entries if e.agent == agent]
            return agent_entries[-limit:]

    def get_by_id(self, entry_id: str) -> Optional[BlackboardEntry]:
        with self.lock:
            for entry in self.entries:
                if entry.get_id() == entry_id:
                    return entry
            return None

    def subscribe(self, agent: str, callback: Callable, topics: List[str]):
        with self.lock:
            for topic in topics:
                if topic not in self.subscribers:
                    self.subscribers[topic] = []
                self.subscribers[topic].append((agent, callback))

    def unsubscribe(self, agent: str, topics: Optional[List[str]] = None):
        with self.lock:
            if topics:
                for topic in topics:
                    if topic in self.subscribers:
                        new_list = []
                        for item in self.subscribers[topic]:
                            if len(item) == 2 and item[0] != agent:
                                new_list.append(item)
                        self.subscribers[topic] = new_list
            else:
                for topic in self.subscribers:
                    new_list = []
                    for item in self.subscribers[topic]:
                        if len(item) == 2 and item[0] != agent:
                            new_list.append(item)
                    self.subscribers[topic] = new_list

    def store_knowledge(self, key: str, value: Any, agent: str):
        with self.lock:
            self.knowledge_base[key] = {
                "value": value,
                "agent": agent,
                "timestamp": datetime.now().isoformat()
            }
            self._dirty = True

    def retrieve_knowledge(self, key: str) -> Optional[Any]:
        with self.lock:
            if key in self.knowledge_base:
                return self.knowledge_base[key]["value"]
            return None

    def get_all_knowledge(self, prefix: Optional[str] = None) -> Dict[str, Any]:
        with self.lock:
            if prefix:
                return {
                    k: v["value"]
                    for k, v in self.knowledge_base.items()
                    if k.startswith(prefix)
                }
            return {k: v["value"] for k, v in self.knowledge_base.items()}

    def clear(self, agent: Optional[str] = None):
        with self.lock:
            if agent:
                self.entries = [e for e in self.entries if e.agent != agent]
            else:
                self.entries = []
            self._dirty = True

    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            by_agent: Dict[str, int] = {}
            by_type: Dict[str, int] = {}

            for entry in self.entries:
                by_agent[entry.agent] = by_agent.get(entry.agent, 0) + 1
                by_type[entry.entry_type] = by_type.get(entry.entry_type, 0) + 1

            return {
                "total_entries": len(self.entries),
                "knowledge_keys": len(self.knowledge_base),
                "by_agent": by_agent,
                "by_type": by_type,
                "subscribers": len(self.subscribers)
            }

    def save_now(self):
        with self.lock:
            if self._dirty and self.storage_path:
                self._save_to_disk()
                self._dirty = False

    def __del__(self):
        self.save_now()

    def _matches_tags(self, entry_tags: List[str], query_tags: List[str]) -> bool:
        if not query_tags:
            return True

        entry_tags_lower = [tag.lower() for tag in entry_tags]
        query_tags_lower = [tag.lower() for tag in query_tags]

        return all(
            any(q in entry_tag for entry_tag in entry_tags_lower)
            for q in query_tags_lower
        )

    def _notify_subscribers(self, entry: BlackboardEntry):
        for tag in entry.tags:
            if tag in self.subscribers:
                for item in self.subscribers[tag]:
                    try:
                        if len(item) == 2:
                            callback = item[1]
                            callback(entry)
                    except Exception as e:
                        print(f"Error notifying subscriber: {e}")

    def _save_to_disk(self):
        if not self.storage_path:
            return

        try:
            data = {
                "entries": [e.to_dict() for e in self.entries],
                "knowledge_base": self.knowledge_base
            }

            self.storage_path.parent.mkdir(parents=True, exist_ok=True)
            self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Error saving blackboard: {e}")

    def _load_from_disk(self):
        if not self.storage_path or not self.storage_path.exists():
            return

        try:
            data = json.loads(self.storage_path.read_text(encoding="utf-8"))

            self.entries = [
                BlackboardEntry.from_dict(e) for e in data.get("entries", [])
            ]
            self.knowledge_base = data.get("knowledge_base", {})
        except Exception as e:
            print(f"Error loading blackboard: {e}")
            self.entries = []
            self.knowledge_base = {}


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="ScholarStream Blackboard CLI"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    stats_parser = subparsers.add_parser("stats", help="Show blackboard statistics")

    query_parser = subparsers.add_parser("query", help="Query blackboard")
    query_parser.add_argument("--tags", nargs="+", help="Tags to search")
    query_parser.add_argument("--max", type=int, default=10, help="Max results")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    bb = ScholarStreamBlackboard()

    if args.command == "stats":
        stats = bb.get_stats()
        print("\nBlackboard Statistics")
        print("=" * 40)
        print(f"Total Entries: {stats['total_entries']}")
        print(f"Knowledge Keys: {stats['knowledge_keys']}")
        print(f"Subscribers: {stats['subscribers']}")
        print("\nBy Agent:")
        for agent, count in stats['by_agent'].items():
            print(f"  {agent}: {count}")
        print("\nBy Type:")
        for entry_type, count in stats['by_type'].items():
            print(f"  {entry_type}: {count}")

    elif args.command == "query":
        results = bb.query("cli", args.tags or [], max_results=args.max)
        print(f"\nQuery Results ({len(results)} entries):")
        print("=" * 40)
        for entry in results[:args.max]:
            print(f"\n[{entry.agent}] {entry.timestamp}")
            print(f"Type: {entry.entry_type} | Confidence: {entry.confidence}")
            print(f"Tags: {', '.join(entry.tags)}")
            print(f"Content: {entry.content}")


if __name__ == "__main__":
    main()
