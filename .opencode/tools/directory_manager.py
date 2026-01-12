#!/usr/bin/env python3
"""ScholarStream Directory Manager - Automates week directory structure creation and management"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, List


class ScholarStreamDirectoryManager:
    """Manages ScholarStream project directory structure"""

    def __init__(self, base_path: str = "."):
        self.base_path = Path(base_path).resolve()
        self.template_dir = self.base_path / ".opencode" / "templates"

    def create_week_structure(self, week_num: int) -> Dict:
        """Create standard week directory structure"""
        week_dir = self.base_path / f"week{week_num:02d}"

        if week_dir.exists():
            return {
                "status": "exists",
                "message": f"Week {week_num} directory already exists",
                "path": str(week_dir)
            }

        directories = [
            week_dir / "plan",
            week_dir / "slides",
            week_dir / "assignments",
            week_dir / "assets"
        ]

        created_dirs = []
        for dir_path in directories:
            dir_path.mkdir(parents=True, exist_ok=True)
            (dir_path / ".gitkeep").touch()
            created_dirs.append(str(dir_path))

        readme_content = self._generate_readme(week_num)
        (week_dir / "README.md").write_text(readme_content, encoding="utf-8")

        self._create_plan_templates(week_dir / "plan", week_num)

        return {
            "status": "created",
            "message": f"Successfully created week {week_num} structure",
            "week_dir": str(week_dir),
            "created_dirs": created_dirs
        }

    def _generate_readme(self, week_num: int) -> str:
        now = datetime.now()
        return f"""# Week {week_num:02d} Course Materials

**Created:** {now.strftime("%Y-%m-%d")}

## Directory Structure

```
week{week_num:02d}/
├── plan/              # Research and planning documents
├── slides/            # Generated presentation slides (Marp Markdown + PDF)
├── assignments/       # Assignment materials
├── assets/            # Images, diagrams, and other assets
└── README.md          # This file
```

## Workflow

1. **Planning Phase**
   - Use `@planner` to generate research documents in `plan/`
   - Planner creates: research_summary.md, section_XX_research.md, references.md

2. **Slide Generation**
   - Use `@slide-generator` to create presentations
   - Slide-generator reads from `plan/` and outputs to `slides/`

3. **Assignment Creation**
   - (Future) Use assignment agent to generate exercises

## Notes

- All content in this directory is gitignored (see .gitignore)
- Use markdown for all documentation
- Follow the established file naming conventions
"""

    def _create_plan_templates(self, plan_dir: Path, week_num: int):
        """Create template files in plan directory"""
        research_summary = f"""# Research Summary - Week {week_num:02d}

## Overview
[3-5 sentence summary of the week's content]

## Key Findings
- [Finding 1]
- [Finding 2]
- [Finding 3]

## Learning Objectives
By the end of this week, students should be able to:
1. [Objective 1]
2. [Objective 2]
3. [Objective 3]

## References
See `references.md` for the detailed reference list.
"""
        (plan_dir / "research_summary.md").write_text(research_summary, encoding="utf-8")

        references = f"""# References - Week {week_num:02d}

> **URL Validation Status:** All URLs have been validated on {datetime.now().strftime("%Y-%m-%d")}

## Official Documentation
1. [Example Official Doc](https://example.com) ✅

## Academic Papers
1. [Example Paper](https://arxiv.org/abs/xxxx.xxxxx) ✅

## Educational Resources
1. [Example Course](https://example.com) ✅

## Notes
- Update this file as you discover new resources
- Validate URLs before including in final materials
- Use consistent citation format (APA/IEEE)
"""
        (plan_dir / "references.md").write_text(references, encoding="utf-8")

        section_template = "# Section XX: [Section Name]\n\n" \
                          "## Key Concepts\n\n" \
                          "### Concept 1: [Name]\n" \
                          "- **Definition:** ...\n" \
                          "- **Key Formula:** $formula$\n" \
                          "- **Intuitive Explanation:** ...\n" \
                          "- **References:** [URL](url)\n\n" \
                          "## Academic Theory\n\n" \
                          "### Theoretical Foundation\n" \
                          "- **Origin and Development:** [Brief history]\n" \
                          "- **Key Academic Literature:**\n" \
                          "  - [Paper 1](url) - [Contribution]\n" \
                          "  - [Paper 2](url) - [Contribution]\n\n" \
                          "### Formal Definition\n" \
                          "$definition$\n\n" \
                          "### Theoretical Boundaries and Conditions\n" \
                          "- **Assumptions:** [List assumptions]\n" \
                          "- **Applicability:** [When does this apply?]\n" \
                          "- **Limitations:** [When does this NOT apply?]\n\n" \
                          "### Theory to Practice Connection\n" \
                          "- **Implementation:** [How to apply]\n" \
                          "- **Approximations:** [Practical simplifications]\n" \
                          "- **Validation:** [How to verify]\n\n" \
                          "## Teaching Strategies\n\n" \
                          "### Intuitive Analogies\n" \
                          "- [Analogy 1]\n" \
                          "- [Analogy 2]\n\n" \
                          "### Common Misconceptions\n" \
                          "- [Misconception 1] → [Correct Understanding]\n" \
                          "- [Misconception 2] → [Correct Understanding]\n"
        (plan_dir / "section_template.md").write_text(section_template, encoding="utf-8")

    def list_weeks(self) -> List[Dict]:
        """List all existing week directories"""
        weeks = []
        for item in self.base_path.glob("week*"):
            if item.is_dir() and item.name.startswith("week"):
                try:
                    week_num = int(item.name.replace("week", ""))
                    weeks.append({
                        "week": week_num,
                        "path": str(item),
                        "has_plan": (item / "plan").exists(),
                        "has_slides": (item / "slides").exists(),
                        "has_assignments": (item / "assignments").exists()
                    })
                except ValueError:
                    continue

        return sorted(weeks, key=lambda x: x["week"])

    def validate_week_structure(self, week_num: int) -> Dict:
        """Validate week directory structure"""
        week_dir = self.base_path / f"week{week_num:02d}"

        if not week_dir.exists():
            return {
                "valid": False,
                "message": f"Week {week_num} does not exist",
                "issues": [f"Directory {week_dir} not found"]
            }

        issues = []
        warnings = []

        required_dirs = ["plan", "slides"]
        for dir_name in required_dirs:
            if not (week_dir / dir_name).exists():
                issues.append(f"Missing required directory: {dir_name}")

        optional_dirs = ["assignments", "assets"]
        for dir_name in optional_dirs:
            if not (week_dir / dir_name).exists():
                warnings.append(f"Missing optional directory: {dir_name}")

        required_files = [
            "README.md",
            "plan/research_summary.md",
            "plan/references.md"
        ]
        for file_path in required_files:
            if not (week_dir / file_path).exists():
                issues.append(f"Missing required file: {file_path}")

        section_files = list((week_dir / "plan").glob("section_*_research.md"))
        if len(section_files) == 0:
            warnings.append("No section research files found")

        return {
            "valid": len(issues) == 0,
            "week": week_num,
            "path": str(week_dir),
            "issues": issues,
            "warnings": warnings,
            "section_count": len(section_files)
        }

    def get_week_summary(self, week_num: int) -> Optional[Dict]:
        """Get summary of a week's content"""
        week_dir = self.base_path / f"week{week_num:02d}"

        if not week_dir.exists():
            return None

        summary = {
            "week": week_num,
            "path": str(week_dir),
            "sections": [],
            "total_files": 0
        }

        for subdir in ["plan", "slides", "assignments", "assets"]:
            subdir_path = week_dir / subdir
            if subdir_path.exists():
                file_count = sum(1 for f in subdir_path.glob("*") if f.is_file())
                summary[subdir] = file_count
                summary["total_files"] += file_count

        plan_dir = week_dir / "plan"
        if plan_dir.exists():
            for section_file in sorted(plan_dir.glob("section_*_research.md")):
                section_name = section_file.stem.replace("_research", "")
                summary["sections"].append(section_name)

        return summary


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ScholarStream Directory Management Tool"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    create_parser = subparsers.add_parser("create", help="Create a new week structure")
    create_parser.add_argument(
        "week",
        type=int,
        help="Week number (e.g., 1, 2, 3)"
    )

    list_parser = subparsers.add_parser("list", help="List all weeks")

    validate_parser = subparsers.add_parser("validate", help="Validate week structure")
    validate_parser.add_argument(
        "week",
        type=int,
        help="Week number to validate"
    )

    summary_parser = subparsers.add_parser("summary", help="Get week summary")
    summary_parser.add_argument(
        "week",
        type=int,
        help="Week number"
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    manager = ScholarStreamDirectoryManager()

    if args.command == "create":
        result = manager.create_week_structure(args.week)
        print(f"✓ {result['message']}")
        if result['status'] == 'created':
            print(f"  Created: {result['week_dir']}")
            for dir_path in result['created_dirs']:
                print(f"    - {dir_path}")

    elif args.command == "list":
        weeks = manager.list_weeks()
        print("\nExisting Weeks:")
        print("-" * 60)
        for week in weeks:
            print(f"Week {week['week']:02d}: {week['path']}")
            print(f"  Plan: {week['has_plan']} | Slides: {week['has_slides']} | Assignments: {week['has_assignments']}")

    elif args.command == "validate":
        result = manager.validate_week_structure(args.week)
        if result['valid']:
            print(f"✓ Week {args.week} structure is valid")
        else:
            print(f"✗ Week {args.week} has issues:")
            for issue in result['issues']:
                print(f"  - {issue}")
        if result['warnings']:
            print("\nWarnings:")
            for warning in result['warnings']:
                print(f"  ! {warning}")

    elif args.command == "summary":
        summary = manager.get_week_summary(args.week)
        if summary:
            print(f"\nWeek {args.week:02d} Summary")
            print("-" * 40)
            print(f"Total Files: {summary['total_files']}")
            for key in ['plan', 'slides', 'assignments', 'assets']:
                if key in summary:
                    print(f"  {key}: {summary[key]} files")
            if summary['sections']:
                print(f"\nSections: {len(summary['sections'])}")
                for section in summary['sections']:
                    print(f"  - {section}")
        else:
            print(f"Week {args.week} does not exist")


if __name__ == "__main__":
    main()
