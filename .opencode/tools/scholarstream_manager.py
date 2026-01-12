#!/usr/bin/env python3
"""ScholarStream Manager - Unified management interface for all ScholarStream tools"""
import argparse
import sys
import json
from pathlib import Path
from typing import Dict, Optional
import subprocess

tools_path = Path(__file__).parent
sys.path.insert(0, str(tools_path))

from directory_manager import ScholarStreamDirectoryManager
from url_validator import URLValidator
from blackboard import ScholarStreamBlackboard


class ScholarStreamManager:
    """Unified interface for all ScholarStream management operations"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.dir_manager = ScholarStreamDirectoryManager(base_path)
        self.url_validator = URLValidator()
        self.blackboard = ScholarStreamBlackboard()

    def create_week(self, week_num: int, topic: str,
                   hours: int = 3, audience: str = "beginner",
                   direction: str = "theory", emphasis: str = "depth") -> Dict:
        """
        Create a new week and initialize blackboard state

        Args:
            week_num: Week number
            topic: Course topic
            hours: Duration in hours
            audience: Target audience
            direction: Teaching direction
            emphasis: Emphasis areas

        Returns:
            Dictionary with creation results
        """
        week_dir = self.base_path / f"week{week_num:02d}"

        dir_result = self.dir_manager.create_week_structure(week_num)

        if dir_result["status"] == "created":
            self.blackboard.post(
                agent="manager",
                content={
                    "week": week_num,
                    "topic": topic,
                    "hours": hours,
                    "audience": audience,
                    "direction": direction,
                    "emphasis": emphasis,
                    "status": "initialized",
                    "created_at": dir_result.get("created_at")
                },
                confidence=1.0,
                tags=["week", f"week{week_num}", "initialization", "planning"],
                entry_type="task"
            )

            self.blackboard.store_knowledge(
                f"week_{week_num:02d}_config",
                {
                    "topic": topic,
                    "hours": hours,
                    "audience": audience,
                    "direction": direction,
                    "emphasis": emphasis
                },
                agent="manager"
            )

            self.blackboard.save_now()

            return {
                "status": "success",
                "week": week_num,
                "message": f"Week {week_num} created and initialized",
                "directory": dir_result["week_dir"],
                "blackboard_entry_id": None
            }
        else:
            return {
                "status": "exists",
                "week": week_num,
                "message": dir_result["message"],
                "directory": dir_result["path"]
            }

    def validate_week(self, week_num: int, validate_urls: bool = True) -> Dict:
        """
        Validate a complete week structure and URLs

        Args:
            week_num: Week number
            validate_urls: Whether to validate URLs

        Returns:
            Validation results
        """
        week_dir = self.base_path / f"week{week_num:02d}"

        if not week_dir.exists():
            return {
                "status": "error",
                "message": f"Week {week_num} does not exist"
            }

        dir_validation = self.dir_manager.validate_week_structure(week_num)

        url_validation = {}
        if validate_urls and dir_validation.get("valid", False):
            plan_dir = week_dir / "plan"
            if plan_dir.exists():
                url_validation = self.url_validator.validate_directory(str(plan_dir))

        overall_valid = dir_validation["valid"] and (
            not validate_urls or
            url_validation.get("total_invalid", 0) == 0
        )

        result = {
            "status": "success" if overall_valid else "warning",
            "week": week_num,
            "valid": overall_valid,
            "directory_validation": dir_validation,
            "url_validation": url_validation
        }

        self.blackboard.post(
            agent="manager",
            content=result,
            confidence=1.0,
            tags=["week", f"week{week_num}", "validation"],
            entry_type="result"
        )

        self.blackboard.save_now()

        return result

    def get_week_status(self, week_num: int) -> Optional[Dict]:
        """
        Get comprehensive status of a week

        Args:
            week_num: Week number

        Returns:
            Status dictionary or None
        """
        week_dir = self.base_path / f"week{week_num:02d}"

        if not week_dir.exists():
            return None

        summary = self.dir_manager.get_week_summary(week_num)
        config = self.blackboard.retrieve_knowledge(f"week_{week_num:02d}_config")

        blackboard_entries = self.blackboard.get_latest_by_agent("manager", limit=50)

        status = {
            "week": week_num,
            "path": str(week_dir),
            "config": config,
            "summary": summary
        }

        return status

    def run_planner_agent(self, week_num: int, topic: str,
                         hours: int, audience: str, direction: str, emphasis: str):
        """
        Invoke the planner agent for a week

        Args:
            week_num: Week number
            topic: Course topic
            hours: Duration in hours
            audience: Target audience
            direction: Teaching direction
            emphasis: Emphasis areas
        """
        self.blackboard.post(
            agent="manager",
            content=f"Invoking planner agent for week {week_num}",
            confidence=1.0,
            tags=["week", f"week{week_num}", "agent_invocation", "planner"],
            entry_type="task"
        )

        print(f"✓ Invoking @planner for week {week_num}")
        print(f"  Topic: {topic}")
        print(f"  Hours: {hours}")
        print(f"  Audience: {audience}")
        print(f"  Direction: {direction}")
        print(f"  Emphasis: {emphasis}")
        print("\nTo invoke planner agent, use:")
        print(f'  @planner Week={week_num} Topic="{topic}" Hours={hours} '
              f'Audience="{audience}" Direction="{direction}" Emphasis="{emphasis}"')

    def run_slide_generator(self, week_num: int):
        """
        Invoke the slide generator agent for a week

        Args:
            week_num: Week number
        """
        self.blackboard.post(
            agent="manager",
            content=f"Invoking slide-generator for week {week_num}",
            confidence=1.0,
            tags=["week", f"week{week_num}", "agent_invocation", "slide-generator"],
            entry_type="task"
        )

        print(f"✓ Invoking @slide-generator for week {week_num}")
        print("\nTo invoke slide-generator agent, use:")
        print(f'  @slide-generator 生成 week{week_num:02d} 的簡報')

    def generate_report(self, week_num: Optional[int] = None) -> str:
        """
        Generate a comprehensive report

        Args:
            week_num: Specific week or None for all weeks

        Returns:
            Formatted report string
        """
        lines = []
        lines.append("\n" + "=" * 60)
        lines.append("ScholarStream Status Report")
        lines.append("=" * 60)

        if week_num:
            status = self.get_week_status(week_num)
            if status:
                lines.append(f"\nWeek {week_num:02d}")
                lines.append("-" * 40)
                lines.append(f"Path: {status['path']}")
                lines.append(f"Total Files: {status['summary']['total_files']}")
                if status['config']:
                    lines.append(f"\nConfig:")
                    lines.append(f"  Topic: {status['config']['topic']}")
                    lines.append(f"  Hours: {status['config']['hours']}")
                    lines.append(f"  Audience: {status['config']['audience']}")
            else:
                lines.append(f"\nWeek {week_num} does not exist")
        else:
            weeks = self.dir_manager.list_weeks()
            lines.append(f"\nTotal Weeks: {len(weeks)}")
            lines.append("")
            lines.append("Week Overview:")
            lines.append("-" * 40)
            for week in weeks:
                week_num = week.get('week', 0)
                summary = self.dir_manager.get_week_summary(week_num)
                total_files = summary['total_files'] if summary else 0
                lines.append(f"Week {week_num:02d}: {total_files} files "
                          f"(Plan: {week.get('has_plan', False)}, Slides: {week.get('has_slides', False)}, "
                          f"Assignments: {week.get('has_assignments', False)})")

        bb_stats = self.blackboard.get_stats()
        lines.append(f"\nBlackboard Stats:")
        lines.append(f"  Total Entries: {bb_stats['total_entries']}")
        lines.append(f"  Knowledge Keys: {bb_stats['knowledge_keys']}")
        lines.append(f"  Subscribers: {bb_stats['subscribers']}")

        lines.append("\n" + "=" * 60)

        return "\n".join(lines)

    def export_state(self, output_path: str):
        """
        Export ScholarStream state to JSON

        Args:
            output_path: Path to output file
        """
        state = {
            "weeks": self.dir_manager.list_weeks(),
            "blackboard_stats": self.blackboard.get_stats(),
            "knowledge_base": self.blackboard.get_all_knowledge()
        }

        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        output_file.write_text(json.dumps(state, indent=2), encoding="utf-8")

        print(f"✓ State exported to {output_path}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ScholarStream Manager - Unified management interface"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    create_parser = subparsers.add_parser("create", help="Create new week")
    create_parser.add_argument("week", type=int, help="Week number")
    create_parser.add_argument("topic", help="Course topic")
    create_parser.add_argument("--hours", type=int, default=3, help="Duration in hours")
    create_parser.add_argument("--audience", default="beginner",
                           choices=["beginner", "intermediate", "advanced", "decision-maker"])
    create_parser.add_argument("--direction", default="theory",
                           choices=["theory", "implementation", "application"])
    create_parser.add_argument("--emphasis", default="depth",
                           choices=["depth", "practice", "cases"])

    validate_parser = subparsers.add_parser("validate", help="Validate week")
    validate_parser.add_argument("week", type=int, help="Week number")
    validate_parser.add_argument("--skip-urls", action="store_true",
                             help="Skip URL validation")

    status_parser = subparsers.add_parser("status", help="Get week status")
    status_parser.add_argument("week", type=int, help="Week number")

    report_parser = subparsers.add_parser("report", help="Generate report")
    report_parser.add_argument("--week", type=int, help="Specific week (default: all)")
    report_parser.add_argument("--output", help="Export report to file")

    planner_parser = subparsers.add_parser("planner", help="Invoke planner agent")
    planner_parser.add_argument("week", type=int, help="Week number")
    planner_parser.add_argument("topic", help="Course topic")
    planner_parser.add_argument("--hours", type=int, default=3, help="Duration in hours")
    planner_parser.add_argument("--audience", default="beginner")
    planner_parser.add_argument("--direction", default="theory")
    planner_parser.add_argument("--emphasis", default="depth")

    slides_parser = subparsers.add_parser("slides", help="Invoke slide-generator")
    slides_parser.add_argument("week", type=int, help="Week number")

    export_parser = subparsers.add_parser("export", help="Export state")
    export_parser.add_argument("output", help="Output file path")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = ScholarStreamManager()

    if args.command == "create":
        result = manager.create_week(
            week_num=args.week,
            topic=args.topic,
            hours=args.hours,
            audience=args.audience,
            direction=args.direction,
            emphasis=args.emphasis
        )
        print(f"✓ {result['message']}")

    elif args.command == "validate":
        result = manager.validate_week(args.week, not args.skip_urls)
        if result["valid"]:
            print(f"✓ Week {args.week} validation passed")
        else:
            print(f"⚠ Week {args.week} has issues:")
            if result["directory_validation"]["issues"]:
                for issue in result["directory_validation"]["issues"]:
                    print(f"  - {issue}")
            if "url_validation" in result and result["url_validation"].get("total_invalid", 0) > 0:
                print(f"  - {result['url_validation']['total_invalid']} invalid URLs")

    elif args.command == "status":
        status = manager.get_week_status(args.week)
        if status:
            print(f"\nWeek {args.week:02d} Status")
            print("-" * 40)
            print(json.dumps(status, indent=2))
        else:
            print(f"Week {args.week} does not exist")

    elif args.command == "report":
        report = manager.generate_report(args.week)
        if args.output:
            Path(args.output).write_text(report, encoding="utf-8")
            print(f"✓ Report exported to {args.output}")
        else:
            print(report)

    elif args.command == "planner":
        manager.run_planner_agent(
            week_num=args.week,
            topic=args.topic,
            hours=args.hours,
            audience=args.audience,
            direction=args.direction,
            emphasis=args.emphasis
        )

    elif args.command == "slides":
        manager.run_slide_generator(args.week)

    elif args.command == "export":
        manager.export_state(args.output)


if __name__ == "__main__":
    main()
