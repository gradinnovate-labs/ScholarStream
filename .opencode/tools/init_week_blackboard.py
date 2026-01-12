#!/usr/bin/env python3
"""
Initialize Blackboard for a specific week in ScholarStream

Usage:
    python .opencode/tools/init_week_blackboard.py \\
        --week 1 \\
        --topic "Dynamic Programming" \\
        --duration 4 \\
        --audience "CS 3rd Year" \\
        --direction "implementation" \\
        --emphasis "practical"

The script will:
1. Initialize Blackboard at .opencode/.blackboard.json
2. Store week configuration
3. Post initialization event
4. Verify the storage
"""

import argparse
import sys
from pathlib import Path

# Add opencode tools to path
sys.path.insert(0, str(Path(__file__).parent))

from blackboard import ScholarStreamBlackboard


def init_week_blackboard(
    week_num: int,
    topic: str,
    duration: float,
    audience: str,
    direction: str,
    emphasis: str,
    sections_count: int = 0,
    urls_count: int = 0
) -> bool:
    """
    Initialize Blackboard for a specific week

    Args:
        week_num: Week number (1, 2, 3, ...)
        topic: Course topic name
        duration: Duration in hours
        audience: Target audience description
        direction: Teaching direction (theory/implementation/application)
        emphasis: Emphasis points (practical/academic/etc)
        sections_count: Number of sections (default 0, will be updated later)
        urls_count: Number of validated URLs (default 0, will be updated later)

    Returns:
        True if successful, False otherwise
    """
    try:
        # Initialize Blackboard
        bb = ScholarStreamBlackboard()

        # Store week configuration
        bb.store_knowledge(
            f"week_{week_num:02d}_config",
            {
                "topic": topic,
                "duration_hours": duration,
                "audience": audience,
                "direction": direction,
                "emphasis": emphasis,
                "created_at": __import__('datetime').datetime.now().isoformat()
            },
            agent="planner"
        )

        # Post initialization event
        bb.post(
            agent="planner",
            content={
                "event": "blackboard_initialized",
                "week": week_num,
                "topic": topic,
                "status": "ready_for_research"
            },
            confidence=1.0,
            tags=[f"week{week_num}", "initialized", "planner"],
            entry_type="system"
        )

        bb.save_now()

        # Verify storage
        config = bb.retrieve_knowledge(f"week_{week_num:02d}_config")
        if not config:
            print(f"❌ Error: Failed to verify configuration storage")
            return False

        # Print success message
        print(f"✅ Blackboard initialized successfully for Week {week_num}")
        print(f"   Topic: {topic}")
        print(f"   Duration: {duration} hours")
        print(f"   Audience: {audience}")
        print(f"   Direction: {direction}")
        print(f"   Emphasis: {emphasis}")
        print(f"   Storage key: week_{week_num:02d}_config")

        return True

    except Exception as e:
        print(f"❌ Error initializing Blackboard: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Initialize Blackboard for a ScholarStream week",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic initialization
  python .opencode/tools/init_week_blackboard.py --week 1 --topic "Dynamic Programming" --duration 4 --audience "CS 3rd Year"

  # Full specification
  python .opencode/tools/init_week_blackboard.py \\
      --week 1 \\
      --topic "Dynamic Programming" \\
      --duration 4 \\
      --audience "CS 3rd Year" \\
      --direction "implementation" \\
      --emphasis "practical"

  # Minimal required arguments
  python .opencode/tools/init_week_blackboard.py -w 1 -t "Fibonacci" -d 2 -a "Beginners"
        """
    )

    parser.add_argument(
        "-w", "--week",
        type=int,
        required=True,
        help="Week number (1, 2, 3, ...)"
    )

    parser.add_argument(
        "-t", "--topic",
        type=str,
        required=True,
        help="Course topic name"
    )

    parser.add_argument(
        "-d", "--duration",
        type=float,
        required=True,
        help="Duration in hours"
    )

    parser.add_argument(
        "-a", "--audience",
        type=str,
        required=True,
        help="Target audience description"
    )

    parser.add_argument(
        "--direction",
        type=str,
        default="implementation",
        choices=["theory", "implementation", "application"],
        help="Teaching direction (default: implementation)"
    )

    parser.add_argument(
        "--emphasis",
        type=str,
        default="practical",
        help="Emphasis points (default: practical)"
    )

    parser.add_argument(
        "--sections",
        type=int,
        default=0,
        help="Number of sections (default: 0, updated later)"
    )

    parser.add_argument(
        "--urls",
        type=int,
        default=0,
        help="Number of validated URLs (default: 0, updated later)"
    )

    args = parser.parse_args()

    # Initialize Blackboard
    success = init_week_blackboard(
        week_num=args.week,
        topic=args.topic,
        duration=args.duration,
        audience=args.audience,
        direction=args.direction,
        emphasis=args.emphasis,
        sections_count=args.sections,
        urls_count=args.urls
    )

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
