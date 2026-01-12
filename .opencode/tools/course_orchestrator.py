#!/usr/bin/env python3
"""Course Orchestrator - Supports course-master agent with configuration, validation, and progress tracking"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from dataclasses import dataclass, asdict, field
from enum import Enum

# Import existing tools
tools_path = Path(__file__).parent
sys.path.insert(0, str(tools_path))

from directory_manager import ScholarStreamDirectoryManager
from url_validator import URLValidator
from blackboard import ScholarStreamBlackboard


class WeekStatus(Enum):
    """Week generation status"""
    PENDING = "pending"
    PLANNING = "planning"
    SLIDES = "slides"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class WeekConfig:
    """Configuration for a single week"""
    week: int
    topic: str
    hours: float
    audience: str
    direction: str
    emphasis: str

    def __post_init__(self):
        """Validate and normalize week number"""
        self.week = int(self.week)

    def to_dict(self) -> Dict:
        return asdict(self)


@dataclass
class WeekProgress:
    """Progress tracking for a single week"""
    week: int
    status: WeekStatus
    research_completed: bool = False
    slides_completed: bool = False
    research_sections: int = 0
    slide_pages: int = 0
    errors: List[str] = field(default_factory=list)
    started_at: Optional[str] = None
    completed_at: Optional[str] = None

    def to_dict(self) -> Dict:
        result = asdict(self)
        result['status'] = self.status.value
        return result


class CourseOrchestrator:
    """Orchestration tool for multi-week course generation"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.dir_manager = ScholarStreamDirectoryManager(base_path)
        self.url_validator = URLValidator()
        self.blackboard = ScholarStreamBlackboard()
        self.progress_file = self.base_path / ".opencode" / "course_progress.json"

    def parse_text_config(self, text: str) -> List[WeekConfig]:
        """
        Parse multi-week configuration from text input

        Format:
        Week X: topic="...", hours=..., audience="...", direction="...", emphasis="..."

        Args:
            text: Multi-line configuration text

        Returns:
            List of WeekConfig objects
        """
        weeks = []

        for line in text.strip().split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                continue

            # Parse "Week X: ..."
            if line.lower().startswith('week'):
                try:
                    # Extract week number
                    parts = line.split(':', 1)
                    week_part = parts[0].strip().split()
                    week_num = int(week_part[1])

                    # Parse key=value pairs
                    config_part = parts[1].strip()
                    params = self._parse_params(config_part)

                    week_config = WeekConfig(
                        week=week_num,
                        topic=params.get('topic', 'Unknown Topic'),
                        hours=float(params.get('hours', 3)),
                        audience=params.get('audience', 'beginner'),
                        direction=params.get('direction', 'theory'),
                        emphasis=params.get('emphasis', 'depth')
                    )
                    weeks.append(week_config)

                except (IndexError, ValueError) as e:
                    print(f"Warning: Failed to parse line: {line}")
                    print(f"Error: {e}")
                    continue

        return weeks

    def _parse_params(self, text: str) -> Dict[str, str]:
        """Parse key='value' pairs from text"""
        params = {}
        import re

        pattern = r'(\w+)=(["\'])(.*?)\2'
        matches = re.findall(pattern, text)

        for key, quote, value in matches:
            params[key] = value

        return params

    def parse_json_config(self, json_str: str) -> List[WeekConfig]:
        """
        Parse multi-week configuration from JSON

        Args:
            json_str: JSON string with 'weeks' array

        Returns:
            List of WeekConfig objects
        """
        data = json.loads(json_str)
        weeks = []

        for week_data in data.get('weeks', []):
            week_config = WeekConfig(
                week=week_data['week'],
                topic=week_data['topic'],
                hours=float(week_data.get('hours', 3)),
                audience=week_data.get('audience', 'beginner'),
                direction=week_data.get('direction', 'theory'),
                emphasis=week_data.get('emphasis', 'depth')
            )
            weeks.append(week_config)

        return weeks

    def create_week(self, week_config: WeekConfig) -> Dict:
        """
        Create directory structure and initialize blackboard for a week

        Args:
            week_config: WeekConfig object

        Returns:
            Creation result dictionary
        """
        result = {
            'week': week_config.week,
            'status': 'success',
            'messages': []
        }

        # Step 1: Create directory structure
        dir_result = self.dir_manager.create_week_structure(week_config.week)

        if dir_result['status'] == 'exists':
            result['messages'].append(f"Week {week_config.week} directory already exists")
        else:
            result['messages'].append(f"Created directory: {dir_result['week_dir']}")

        # Step 2: Initialize blackboard
        try:
            from init_week_blackboard import init_week_blackboard

            init_week_blackboard(
                week_num=week_config.week,
                topic=week_config.topic,
                duration=week_config.hours,
                audience=week_config.audience,
                direction=week_config.direction,
                emphasis=week_config.emphasis
            )
            result['messages'].append(f"Initialized blackboard for week {week_config.week}")
        except Exception as e:
            result['status'] = 'error'
            result['messages'].append(f"Failed to initialize blackboard: {e}")

        return result

    def validate_planner_output(self, week_num: int) -> Dict:
        """
        Validate planner output for a week

        Args:
            week_num: Week number

        Returns:
            Validation result dictionary
        """
        week_dir = self.base_path / f"week{week_num:02d}"
        plan_dir = week_dir / "plan"

        result = {
            'week': week_num,
            'valid': True,
            'issues': [],
            'sections_count': 0,
            'references_valid': False
        }

        if not plan_dir.exists():
            result['valid'] = False
            result['issues'].append("Plan directory does not exist")
            return result

        # Check required files
        required_files = [
            "research_summary.md",
            "references.md"
        ]

        for filename in required_files:
            if not (plan_dir / filename).exists():
                result['valid'] = False
                result['issues'].append(f"Missing required file: {filename}")

        # Check section files
        section_files = list(plan_dir.glob("section_*_research.md"))
        result['sections_count'] = len(section_files)

        if result['sections_count'] == 0:
            result['valid'] = False
            result['issues'].append("No section research files found")

        # Check URL validation report
        url_report = plan_dir / "url_validation_report.md"
        if url_report.exists():
            result['references_valid'] = True

        return result

    def validate_slides_output(self, week_num: int) -> Dict:
        """
        Validate slide-generator output for a week

        Args:
            week_num: Week number

        Returns:
            Validation result dictionary
        """
        week_dir = self.base_path / f"week{week_num:02d}"
        slides_dir = week_dir / "slides"

        result = {
            'week': week_num,
            'valid': True,
            'issues': [],
            'has_markdown': False,
            'has_pdf': False,
            'pdf_size': 0
        }

        if not slides_dir.exists():
            result['valid'] = False
            result['issues'].append("Slides directory does not exist")
            return result

        # Check markdown file
        md_files = list(slides_dir.glob("*.md"))
        if md_files:
            result['has_markdown'] = True

        # Check PDF file
        pdf_files = list(slides_dir.glob("*.pdf"))
        if pdf_files:
            result['has_pdf'] = True
            result['pdf_size'] = pdf_files[0].stat().st_size

        if not result['has_markdown']:
            result['valid'] = False
            result['issues'].append("No markdown file found")

        if not result['has_pdf']:
            result['valid'] = False
            result['issues'].append("No PDF file found")

        return result

    def update_week_status(self, week_num: int, status: WeekStatus,
                          research_sections: int = 0, slide_pages: int = 0,
                          error: Optional[str] = None) -> Dict:
        """
        Update progress tracking for a week

        Args:
            week_num: Week number
            status: New status
            research_sections: Number of research sections completed
            slide_pages: Number of slides generated
            error: Error message if status is failed

        Returns:
            Updated WeekProgress object
        """
        progress = self._load_progress()

        if week_num not in progress:
            progress[week_num] = WeekProgress(
                week=week_num,
                status=WeekStatus.PENDING
            )

        # Update status
        progress[week_num].status = status

        if status == WeekStatus.PLANNING:
            if not progress[week_num].started_at:
                progress[week_num].started_at = datetime.now().isoformat()

        elif status == WeekStatus.SLIDES:
            progress[week_num].research_completed = True
            progress[week_num].research_sections = research_sections

        elif status == WeekStatus.COMPLETED:
            progress[week_num].slides_completed = True
            progress[week_num].slide_pages = slide_pages
            progress[week_num].completed_at = datetime.now().isoformat()

        elif status == WeekStatus.FAILED and error:
            progress[week_num].errors.append(error)

        # Save to file
        self._save_progress(progress)

        return progress[week_num].to_dict()

    def generate_progress_report(self, week_configs: List[WeekConfig]) -> str:
        """
        Generate progress report for all weeks

        Args:
            week_configs: List of WeekConfig objects

        Returns:
            Formatted progress report string
        """
        progress = self._load_progress()

        now = datetime.now()
        report = []
        report.append(f"# Course Generation Progress Report")
        report.append(f"Generated: {now.strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # Statistics
        total = len(week_configs)
        completed = sum(1 for w in week_configs if progress.get(w.week, WeekProgress(w.week, WeekStatus.PENDING)).status == WeekStatus.COMPLETED)
        in_progress = sum(1 for w in week_configs if progress.get(w.week, WeekProgress(w.week, WeekStatus.PENDING)).status in [WeekStatus.PLANNING, WeekStatus.SLIDES])
        failed = sum(1 for w in week_configs if progress.get(w.week, WeekProgress(w.week, WeekStatus.PENDING)).status == WeekStatus.FAILED)

        report.append(f"## Summary")
        report.append(f"- Total Weeks: {total}")
        report.append(f"- Completed: {completed}")
        report.append(f"- In Progress: {in_progress}")
        report.append(f"- Failed: {failed}")
        report.append(f"- Pending: {total - completed - in_progress - failed}")
        report.append("")

        # Detailed status for each week
        report.append(f"## Week Details")
        report.append("")

        for week_config in sorted(week_configs, key=lambda w: w.week):
            week_num = week_config.week
            prog = progress.get(week_num, WeekProgress(week_num, WeekStatus.PENDING))

            # Status icon
            status_icons = {
                WeekStatus.PENDING: "⏳",
                WeekStatus.PLANNING: "🔄",
                WeekStatus.SLIDES: "🎨",
                WeekStatus.COMPLETED: "✅",
                WeekStatus.FAILED: "❌"
            }
            icon = status_icons.get(prog.status, "❓")

            report.append(f"### {icon} Week {week_num:02d}: {week_config.topic}")
            report.append(f"- Hours: {week_config.hours}")
            report.append(f"- Audience: {week_config.audience}")
            report.append(f"- Direction: {week_config.direction}")
            report.append(f"- Emphasis: {week_config.emphasis}")
            report.append(f"- Status: {prog.status.value}")

            if prog.research_completed:
                report.append(f"- Research: ✓ {prog.research_sections} sections")

            if prog.slides_completed:
                report.append(f"- Slides: ✓ {prog.slide_pages} pages")
                report.append(f"- Output: `./week{week_num:02d}/slides/week{week_num:02d}_slides.pdf`")

            if prog.errors:
                report.append(f"- Errors:")
                for error in prog.errors:
                    report.append(f"  - {error}")

            report.append("")

        # Output locations
        report.append(f"## Output Locations")
        report.append("")
        report.append("Completed weeks:")
        for week_config in sorted(week_configs, key=lambda w: w.week):
            week_num = week_config.week
            prog = progress.get(week_num, WeekProgress(week_num, WeekStatus.PENDING))

            if prog.status == WeekStatus.COMPLETED:
                report.append(f"- Week {week_num:02d}: `./week{week_num:02d}/slides/week{week_num:02d}_slides.pdf`")

        report.append("")

        return "\n".join(report)

    def generate_agent_commands(self, week_configs: List[WeekConfig]) -> str:
        """
        Generate sequential commands for course-master agent to execute

        Args:
            week_configs: List of WeekConfig objects

        Returns:
            Formatted command sequence string
        """
        commands = []
        commands.append("## Sequential Execution Plan")
        commands.append("")
        commands.append("The course-master agent should execute the following steps in order:")
        commands.append("")

        for i, week_config in enumerate(sorted(week_configs, key=lambda w: w.week), 1):
            week_num = week_config.week
            commands.append(f"### Week {week_num:02d}/{len(week_configs)}: {week_config.topic}")
            commands.append("")

            # Step 1: Create directory
            commands.append(f"1. **Create directory structure**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/directory_manager.py create {week_num}")
            commands.append(f"```")
            commands.append("")

            # Step 2: Initialize blackboard
            commands.append(f"2. **Initialize blackboard**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/init_week_blackboard.py \\")
            commands.append(f"    --week {week_num} \\")
            commands.append(f"    --topic \"{week_config.topic}\" \\")
            commands.append(f"    --duration {week_config.hours} \\")
            commands.append(f"    --audience \"{week_config.audience}\" \\")
            commands.append(f"    --direction {week_config.direction} \\")
            commands.append(f"    --emphasis {week_config.emphasis}")
            commands.append(f"```")
            commands.append("")

            # Step 3: Update status to planning
            commands.append(f"3. **Update status to planning**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/course_orchestrator.py \\")
            commands.append(f"    update-status --week {week_num} --status planning")
            commands.append(f"```")
            commands.append("")

            # Step 4: Call planner agent
            commands.append(f"4. **Invoke planner agent**:")
            commands.append(f"```")
            commands.append(f"@planner")
            commands.append(f"- Week: {week_num}")
            commands.append(f"- Topic: {week_config.topic}")
            commands.append(f"- Hours: {week_config.hours}")
            commands.append(f"- Audience: {week_config.audience}")
            commands.append(f"- Direction: {week_config.direction}")
            commands.append(f"- Emphasis: {week_config.emphasis}")
            commands.append(f"```")
            commands.append("")

            # Step 5: Validate planner output
            commands.append(f"5. **Validate planner output**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/course_orchestrator.py \\")
            commands.append(f"    validate-planner --week {week_num}")
            commands.append(f"```")
            commands.append("")

            # Step 6: Update status to slides
            commands.append(f"6. **Update status to slides**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/course_orchestrator.py \\")
            commands.append(f"    update-status --week {week_num} --status slides \\")
            commands.append(f"    --sections $(ls week{week_num:02d}/plan/section_*_research.md 2>/dev/null | wc -l)")
            commands.append(f"```")
            commands.append("")

            # Step 7: Call slide-generator agent
            commands.append(f"7. **Invoke slide-generator agent**:")
            commands.append(f"```")
            commands.append(f"@slide-generator 生成 week{week_num} 的簡報")
            commands.append(f"```")
            commands.append("")

            # Step 8: Validate slides output
            commands.append(f"8. **Validate slides output**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/course_orchestrator.py \\")
            commands.append(f"    validate-slides --week {week_num}")
            commands.append(f"```")
            commands.append("")

            # Step 9: Update status to completed
            commands.append(f"9. **Update status to completed**:")
            commands.append(f"```bash")
            commands.append(f"python3 .opencode/tools/course_orchestrator.py \\")
            commands.append(f"    update-status --week {week_num} --status completed \\")
            commands.append(f"    --pages $(grep -c \"^---\" week{week_num:02d}/slides/week{week_num:02d}_slides.md 2>/dev/null || echo 0)")
            commands.append(f"```")
            commands.append("")

            # Separator between weeks
            if i < len(week_configs):
                commands.append("---")
                commands.append("")

        return "\n".join(commands)

    def _load_progress(self) -> Dict[int, WeekProgress]:
        """Load progress from file"""
        if not self.progress_file.exists():
            return {}

        try:
            data = json.loads(self.progress_file.read_text(encoding='utf-8'))
            progress = {}

            for week_num, prog_data in data.items():
                progress[int(week_num)] = WeekProgress(
                    week=int(week_num),
                    status=WeekStatus(prog_data['status']),
                    research_completed=prog_data.get('research_completed', False),
                    slides_completed=prog_data.get('slides_completed', False),
                    research_sections=prog_data.get('research_sections', 0),
                    slide_pages=prog_data.get('slide_pages', 0),
                    errors=prog_data.get('errors', []),
                    started_at=prog_data.get('started_at'),
                    completed_at=prog_data.get('completed_at')
                )

            return progress

        except Exception as e:
            print(f"Warning: Failed to load progress file: {e}")
            return {}

    def _save_progress(self, progress: Dict[int, WeekProgress]):
        """Save progress to file"""
        try:
            data = {
                str(week_num): prog.to_dict()
                for week_num, prog in progress.items()
            }

            self.progress_file.parent.mkdir(parents=True, exist_ok=True)
            self.progress_file.write_text(json.dumps(data, indent=2), encoding='utf-8')

        except Exception as e:
            print(f"Warning: Failed to save progress file: {e}")


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Course Orchestrator Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # Parse text config
    parse_text_parser = subparsers.add_parser("parse-text", help="Parse multi-week configuration from text")
    parse_text_parser.add_argument("text", help="Multi-line configuration text")

    # Parse JSON config
    parse_json_parser = subparsers.add_parser("parse-json", help="Parse multi-week configuration from JSON")
    parse_json_parser.add_argument("json_file", help="Path to JSON file")

    # Create week
    create_parser = subparsers.add_parser("create", help="Create week structure")
    create_parser.add_argument("--week", type=int, required=True, help="Week number")
    create_parser.add_argument("--topic", required=True, help="Course topic")
    create_parser.add_argument("--hours", type=float, default=3, help="Duration in hours")
    create_parser.add_argument("--audience", default="beginner", help="Target audience")
    create_parser.add_argument("--direction", default="theory", help="Teaching direction")
    create_parser.add_argument("--emphasis", default="depth", help="Emphasis areas")

    # Validate planner output
    validate_planner_parser = subparsers.add_parser("validate-planner", help="Validate planner output")
    validate_planner_parser.add_argument("--week", type=int, required=True, help="Week number")

    # Validate slides output
    validate_slides_parser = subparsers.add_parser("validate-slides", help="Validate slides output")
    validate_slides_parser.add_argument("--week", type=int, required=True, help="Week number")

    # Update status
    update_status_parser = subparsers.add_parser("update-status", help="Update week status")
    update_status_parser.add_argument("--week", type=int, required=True, help="Week number")
    update_status_parser.add_argument("--status", required=True, choices=["pending", "planning", "slides", "completed", "failed"], help="New status")
    update_status_parser.add_argument("--sections", type=int, default=0, help="Research sections count")
    update_status_parser.add_argument("--pages", type=int, default=0, help="Slide pages count")
    update_status_parser.add_argument("--error", help="Error message if status is failed")

    # Generate report
    report_parser = subparsers.add_parser("report", help="Generate progress report")
    report_parser.add_argument("--config", help="Path to configuration file (JSON or text)")

    # Generate commands
    commands_parser = subparsers.add_parser("commands", help="Generate execution commands")
    commands_parser.add_argument("--config", help="Path to configuration file (JSON or text)")

    # Show progress
    show_parser = subparsers.add_parser("show", help="Show current progress")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    orchestrator = CourseOrchestrator()

    if args.command == "parse-text":
        weeks = orchestrator.parse_text_config(args.text)
        print(f"Parsed {len(weeks)} weeks:")
        for week in weeks:
            print(f"  Week {week.week}: {week.topic} ({week.hours}h, {week.audience})")

    elif args.command == "parse-json":
        json_str = Path(args.json_file).read_text(encoding='utf-8')
        weeks = orchestrator.parse_json_config(json_str)
        print(f"Parsed {len(weeks)} weeks:")
        for week in weeks:
            print(f"  Week {week.week}: {week.topic} ({week.hours}h, {week.audience})")

    elif args.command == "create":
        week_config = WeekConfig(
            week=args.week,
            topic=args.topic,
            hours=args.hours,
            audience=args.audience,
            direction=args.direction,
            emphasis=args.emphasis
        )
        result = orchestrator.create_week(week_config)
        print(f"✓ Week {args.week} {result['status'].lower()}")
        for msg in result['messages']:
            print(f"  - {msg}")

    elif args.command == "validate-planner":
        result = orchestrator.validate_planner_output(args.week)
        if result['valid']:
            print(f"✓ Week {args.week} planner output is valid")
            print(f"  - Sections: {result['sections_count']}")
            print(f"  - References validated: {result['references_valid']}")
        else:
            print(f"✗ Week {args.week} planner output has issues:")
            for issue in result['issues']:
                print(f"  - {issue}")

    elif args.command == "validate-slides":
        result = orchestrator.validate_slides_output(args.week)
        if result['valid']:
            print(f"✓ Week {args.week} slides output is valid")
            print(f"  - Markdown: {result['has_markdown']}")
            print(f"  - PDF: {result['has_pdf']} ({result['pdf_size']} bytes)")
        else:
            print(f"✗ Week {args.week} slides output has issues:")
            for issue in result['issues']:
                print(f"  - {issue}")

    elif args.command == "update-status":
        status_map = {
            "pending": WeekStatus.PENDING,
            "planning": WeekStatus.PLANNING,
            "slides": WeekStatus.SLIDES,
            "completed": WeekStatus.COMPLETED,
            "failed": WeekStatus.FAILED
        }
        orchestrator.update_week_status(
            week_num=args.week,
            status=status_map[args.status],
            research_sections=args.sections,
            slide_pages=args.pages,
            error=args.error
        )
        print(f"✓ Updated week {args.week} status to {args.status}")

    elif args.command == "report":
        # Load configuration
        weeks = []
        if args.config:
            config_path = Path(args.config)
            if config_path.suffix == '.json':
                weeks = orchestrator.parse_json_config(config_path.read_text(encoding='utf-8'))
            else:
                weeks = orchestrator.parse_text_config(config_path.read_text(encoding='utf-8'))

        report = orchestrator.generate_progress_report(weeks)
        print(report)

    elif args.command == "commands":
        # Load configuration
        weeks = []
        if args.config:
            config_path = Path(args.config)
            if config_path.suffix == '.json':
                weeks = orchestrator.parse_json_config(config_path.read_text(encoding='utf-8'))
            else:
                weeks = orchestrator.parse_text_config(config_path.read_text(encoding='utf-8'))

        commands = orchestrator.generate_agent_commands(weeks)
        print(commands)

    elif args.command == "show":
        progress = orchestrator._load_progress()
        print("\nCurrent Progress:")
        print("=" * 40)
        if not progress:
            print("No progress tracked yet")
        else:
            for week_num in sorted(progress.keys()):
                prog = progress[week_num]
                status_icon = {
                    WeekStatus.PENDING: "⏳",
                    WeekStatus.PLANNING: "🔄",
                    WeekStatus.SLIDES: "🎨",
                    WeekStatus.COMPLETED: "✅",
                    WeekStatus.FAILED: "❌"
                }.get(prog.status, "❓")

                print(f"Week {week_num:02d}: {status_icon} {prog.status.value}")
                if prog.research_completed:
                    print(f"  Research: {prog.research_sections} sections")
                if prog.slides_completed:
                    print(f"  Slides: {prog.slide_pages} pages")
                if prog.errors:
                    print(f"  Errors: {len(prog.errors)}")


if __name__ == "__main__":
    main()
