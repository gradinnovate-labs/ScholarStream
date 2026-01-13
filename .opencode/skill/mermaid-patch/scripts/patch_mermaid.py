#!/usr/bin/env python3
"""
Mermaid Auto-Patcher - MVP v1.0
"""

import re
import sys
import os
import shutil
import subprocess
import datetime
from pathlib import Path


class MermaidPatcher:
    def __init__(self, file_path, auto_approve=False, verbose=False):
        self.file_path = Path(file_path)
        self.auto_approve = auto_approve
        self.verbose = verbose
        self.backup_path = None
        self.original_content = None
        self.patches_applied = []

    def log(self, message):
        if self.verbose:
            print(f"[INFO] {message}")

    def error(self, message):
        print(f"[ERROR] {message}", file=sys.stderr)

    def create_backup(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_name = f"{self.file_path.name}.backup_{timestamp}"
        self.backup_path = self.file_path.parent / backup_name

        if self.backup_path.exists():
            i = 1
            while self.backup_path.exists():
                backup_name = f"{self.file_path.name}.backup_{timestamp}_{i}"
                self.backup_path = self.file_path.parent / backup_name
                i += 1

        shutil.copy2(self.file_path, self.backup_path)
        self.log(f"Created backup: {self.backup_path}")
        return self.backup_path

    def restore_backup(self):
        if self.backup_path and self.backup_path.exists():
            shutil.copy2(self.backup_path, self.file_path)
            self.log(f"Restored from backup: {self.backup_path}")
            return True
        return False

    def read_file(self):
        try:
            with open(self.file_path, 'r', encoding='utf-8') as f:
                self.original_content = f.read()
            return self.original_content
        except Exception as e:
            self.error(f"Failed to read file: {e}")
            return None

    def write_file(self, content):
        try:
            with open(self.file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            self.error(f"Failed to write file: {e}")
            return False

    def extract_mermaid_blocks(self, content):
        pattern = r'```mermaid\n(.*?)\n```'
        blocks = re.findall(pattern, content, re.DOTALL)
        self.log(f"Found {len(blocks)} mermaid blocks")
        return blocks

    def validate_block(self, block_content, block_num):
        import tempfile
        import uuid

        temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False, encoding='utf-8')
        temp_path = temp_file.name
        temp_file.write(f"```mermaid\n{block_content}\n```")
        temp_file.close()

        try:
            result = subprocess.run(
                ['mmdc', '-i', temp_path, '-o', '/tmp/mermaid-validation-test.svg'],
                capture_output=True,
                text=True,
                timeout=15
            )
            is_valid = result.returncode == 0
            output = result.stdout + result.stderr
            os.unlink(temp_path)

            return {'valid': is_valid, 'output': output, 'block_num': block_num}
        except subprocess.TimeoutExpired:
            self.error(f"Validation timeout for block {block_num}")
            try:
                os.unlink(temp_path)
            except:
                pass
            return {'valid': False, 'output': 'Timeout', 'block_num': block_num}
        except Exception as e:
            self.error(f"Validation error for block {block_num}: {e}")
            try:
                os.unlink(temp_path)
            except:
                pass
            return {'valid': False, 'output': str(e), 'block_num': block_num}

    def detect_errors(self, validation_results):
        errors = []

        for result in validation_results:
            if not result['valid']:
                output = result['output']

                if "Parse error on line" in output:
                    errors.append({
                        'type': 'parse_error',
                        'block_num': result['block_num'],
                        'message': self._extract_parse_error(output),
                        'output': output
                    })
                elif "Expecting" in output and "got" in output:
                    errors.append({
                        'type': 'expecting_error',
                        'block_num': result['block_num'],
                        'message': self._extract_expect_error(output),
                        'output': output
                    })
                else:
                    errors.append({
                        'type': 'unknown_error',
                        'block_num': result['block_num'],
                        'message': output[:200],
                        'output': output
                    })

        return errors

    def _extract_parse_error(self, output):
        match = re.search(r'Parse error on line (\d+):.*?(?=\n|$)', output, re.DOTALL)
        if match:
            return match.group(0).strip()
        return "Unknown parse error"

    def _extract_expect_error(self, output):
        match = re.search(r"Expecting '[^']*', got '[^']*\"", output)
        if match:
            return f"Expecting {match.group(1)}, got {match.group(2)}"
        return "Syntax error"

    def apply_fixes(self, errors, blocks):
        content = self.original_content
        fixed_count = 0

        for error in errors:
            block_num = error['block_num']
            if block_num > len(blocks):
                continue

            original_block = blocks[block_num - 1]
            fixed_block = self._fix_block(original_block, error)

            if fixed_block != original_block:
                old_code = f"```mermaid\n{original_block}\n```"
                new_code = f"```mermaid\n{fixed_block}\n```"
                content = content.replace(old_code, new_code)
                fixed_count += 1
                self.patches_applied.append({
                    'block_num': block_num,
                    'error_type': error['type'],
                    'original': original_block[:100],
                    'fixed': fixed_block[:100]
                })
                self.log(f"Applied fix to block {block_num}: {error['type']}")

        self.log(f"Applied {fixed_count} fixes")
        return content, fixed_count

    def _fix_block(self, block_content, error):
        if '<br/>' in block_content or '<br>' in block_content:
            self.log("Applying Rule #1: Flowchart <br/> replacement")
            return self._fix_flowchart_br_tags(block_content)

        if re.search(r'noteA\[.*?\]', block_content):
            self.log("Applying Rule #2: Invalid note syntax")
            return self._fix_invalid_note_syntax(block_content)

        if self._has_unquoted_special_chars(block_content):
            self.log("Applying Rule #3: Unquoted special characters")
            return self._fix_unquoted_special_chars(block_content)

        return block_content

    def _fix_flowchart_br_tags(self, content):
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            if '<br/>' in line or '<br>' in line:
                fixed_line = line.replace('<br/>', '\n').replace('<br>', '\n')
                if '[' in fixed_line and ']' in fixed_line:
                    parts = fixed_line.split(']')
                    for i, part in enumerate(parts):
                        if '[' in part and '\n' in part:
                            subparts = part.split('\n')
                            for j, subpart in enumerate(subparts):
                                if j == 0 and subpart.startswith('[') and not subpart.startswith('['):
                                    subparts[j] = f'["{subpart[1:]}'
                            fixed_line = ']'.join(subparts)
                fixed_lines.append(fixed_line)
            else:
                fixed_lines.append(line)
        else:
            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def _fix_invalid_note_syntax(self, content):
        pattern = r'noteA\[([^\]]*)\]'

        def replacer(match):
            note_content = match.group(1)
            note_content = note_content.replace(':', ' ')
            return f'noteA["{note_content}"]'

        return re.sub(pattern, replacer, content)

    def _has_unquoted_special_chars(self, content):
        special_chars = set(':-|[]<>/')

        for char in special_chars:
            if char in content:
                return True
        return False

    def _fix_unquoted_special_chars(self, content):
        lines = content.split('\n')
        fixed_lines = []

        for line in lines:
            fixed_line = line
            if '[' in line and ']' in line:
                parts = line.split(']')
                for i, part in enumerate(parts):
                    if '[' in part:
                        for char in ':-|[]<>/':
                            if char in part:
                                fixed_line = fixed_line.replace(f'{part}]', f'["{part[1:]}"]')
                                break
                        if fixed_line != line:
                            break
            fixed_lines.append(fixed_line)
        else:
            fixed_lines.append(line)

        return '\n'.join(fixed_lines)

    def generate_report(self, validation_before, validation_after):
        report = []
        report.append("=" * 70)
        report.append("MERMAID PATCH REPORT")
        report.append("=" * 70)
        report.append("")
        report.append(f"**File**: {self.file_path}")
        report.append(f"**Timestamp**: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"**Patcher**: mermaid-patch skill v1.0 (MVP)")
        report.append("")

        report.append("## Summary")
        report.append("-" * 70)
        report.append(f"- **Total Mermaid Blocks**: {len(self.patches_applied)}")
        report.append(f"- **Fixes Applied**: {len(self.patches_applied)}")
        report.append("")

        if self.patches_applied:
            report.append("## Applied Fixes")
            report.append("-" * 70)
            for i, patch in enumerate(self.patches_applied, 1):
                report.append(f"\n### Fix #{i}")
                report.append(f"- **Block**: {patch['block_num']}")
                report.append(f"- **Error Type**: {patch['error_type']}")
                report.append(f"- **Original (first 100 chars)**:")
                report.append("  ```")
                report.append(f"  {patch['original']}")
                report.append("  ```")
                report.append(f"- **Fixed (first 100 chars)**:")
                report.append("  ```")
                report.append(f"  {patch['fixed']}")
                report.append("  ```")
            report.append("")

        if validation_after:
            valid_count = sum(1 for r in validation_after if r['valid'])
            report.append("## Validation Result")
            report.append("-" * 70)
            report.append(f"- **Valid Blocks**: {valid_count}/{len(validation_after)}")
            report.append("")

            for result in validation_after:
                status = "✅ VALID" if result['valid'] else "❌ INVALID"
                report.append(f"Block {result['block_num']}: {status}")
                if not result['valid']:
                    report.append(f"  Error: {result['output'][:200]}")

        report.append("")
        report.append("## Backup Information")
        report.append("-" * 70)
        report.append(f"- **Backup Location**: {self.backup_path}")
        report.append(f"- **Status**: Kept until manual confirmation")

        report.append("")
        report.append("=" * 70)

        return "\n".join(report)

    def save_report(self, report):
        report_path = self.file_path.parent / f"{self.file_path.stem}_patch_report.md"
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write(report)
        self.log(f"Saved report: {report_path}")
        return report_path

    def run(self):
        print(f"\nMermaid Patcher v1.0 (MVP)")
        print(f"Processing: {self.file_path}")
        print("=" * 70)

        self.log("Step 1: Reading file...")
        content = self.read_file()
        if content is None:
            return False

        self.log("Step 2: Creating backup...")
        self.create_backup()

        self.log("Step 3: Extracting mermaid blocks...")
        blocks = self.extract_mermaid_blocks(content)

        if not blocks:
            print("✅ No mermaid blocks found. Nothing to validate.")
            return True

        self.log("Step 4: Validating each block...")
        validation_results = []
        for i, block in enumerate(blocks, 1):
            self.log(f"  Validating block {i}/{len(blocks)}...")
            result = self.validate_block(block, i)
            validation_results.append(result)

        self.log("Step 5: Detecting errors...")
        errors = self.detect_errors(validation_results)

        if not errors:
            print("✅ All mermaid blocks are valid. No fixes needed.")
            report = self.generate_report(validation_results, None)
            report_path = self.save_report(report)
            print(f"\n📊 Report saved: {report_path}")
            return True

        print(f"\n⚠️  Found {len(errors)} error(s) requiring fixes:")
        for i, error in enumerate(errors, 1):
            print(f"  {i}. Block {error['block_num']}: {error['type']}")

        self.log("Step 6: Applying fixes...")
        modified_content, fixed_count = self.apply_fixes(errors, blocks)

        if not self.write_file(modified_content):
            self.error("Failed to write modified content")
            self.restore_backup()
            return False

        print(f"\n✅ Applied {fixed_count} fix(es)")

        self.log("Step 7: Re-validating...")
        with open(self.file_path, 'r', encoding='utf-8') as f:
            final_content = f.read()

        final_blocks = self.extract_mermaid_blocks(final_content)
        validation_after = []
        for i, block in enumerate(final_blocks, 1):
            self.log(f"  Re-validating block {i}/{len(final_blocks)}...")
            result = self.validate_block(block, i)
            validation_after.append(result)

        still_invalid = [r for r in validation_after if not r['valid']]

        if still_invalid:
            print(f"\n❌ {len(still_invalid)} block(s) still invalid after fixes")
            for r in still_invalid:
                print(f"  Block {r['block_num']}: {r['output'][:200]}")

            if not self.auto_approve:
                print("\n" + "=" * 70)
                print("VALIDATION FAILED")
                print("=" * 70)
                response = input("\nRestore backup? (y/n): ").strip().lower()
                if response == 'y':
                    self.restore_backup()
                    print("✅ Restored from backup")
                    return False

            report = self.generate_report(validation_results, validation_after)
            report_path = self.save_report(report)
            print(f"\n📊 Report saved: {report_path}")
            return False

        self.log("Step 8: Generating report...")
        print("\n✅ All blocks validated successfully after fixes!")
        report = self.generate_report(validation_results, validation_after)
        report_path = self.save_report(report)
        print(f"\n📊 Report saved: {report_path}")

        return True


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description='Mermaid Auto-Patcher - Detect and fix common Mermaid syntax errors',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --file ./week01/plan/section_02_research.md
  %(prog)s --directory ./week01/plan/ --pattern "section_*.md"
  %(prog)s --file ./week01/plan/section_02_research.md --auto-approve --verbose
        """
    )

    parser.add_argument('--file', '-f', type=str, help='Path to markdown file to patch')
    parser.add_argument('--directory', '-d', type=str, help='Directory containing markdown files to patch')
    parser.add_argument('--pattern', '-p', type=str, default='section_*.md', help='File pattern to match (default: section_*.md)')
    parser.add_argument('--auto-approve', action='store_true', help='Auto-approve fixes without confirmation')
    parser.add_argument('--verbose', '-v', action='store_true', help='Enable verbose logging')

    args = parser.parse_args()

    if args.file and args.directory:
        print("Error: Cannot specify both --file and --directory", file=sys.stderr)
        sys.exit(1)

    if not args.file and not args.directory:
        print("Error: Must specify either --file or --directory", file=sys.stderr)
        sys.exit(1)

    files_to_patch = []

    if args.file:
        file_path = Path(args.file)
        if not file_path.exists():
            print(f"Error: File not found: {args.file}", file=sys.stderr)
            sys.exit(1)
        files_to_patch.append(file_path)

    if args.directory:
        dir_path = Path(args.directory)
        if not dir_path.exists():
            print(f"Error: Directory not found: {args.directory}", file=sys.stderr)
            sys.exit(1)

        files_to_patch = list(dir_path.glob(args.pattern))
        if not files_to_patch:
            print(f"Error: No files matching pattern '{args.pattern}' in {args.directory}", file=sys.stderr)
            sys.exit(1)

    print(f"\nFound {len(files_to_patch)} file(s) to process\n")

    results = []
    for file_path in files_to_patch:
        patcher = MermaidPatcher(file_path, auto_approve=args.auto_approve, verbose=args.verbose)
        success = patcher.run()
        results.append({'file': file_path, 'success': success})

    print("\n" + "=" * 70)
    print("PATCH SUMMARY")
    print("=" * 70)

    successful = sum(1 for r in results if r['success'])
    total = len(results)

    print(f"Total files processed: {total}")
    print(f"Successfully patched: {successful}")
    print(f"Failed: {total - successful}")

    if successful == total:
        print("\n✅ All files processed successfully!")
        sys.exit(0)
    else:
        print(f"\n⚠️  {total - successful} file(s) failed")
        sys.exit(1)


if __name__ == '__main__':
    main()
