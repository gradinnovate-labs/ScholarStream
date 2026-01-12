#!/usr/bin/env python3
"""URL Validator for ScholarStream - Validates reference URLs in research documents"""
import asyncio
import aiohttp
import argparse
import re
import sys
from typing import List, Tuple, Dict, Optional
from urllib.parse import urlparse
from pathlib import Path


class URLValidator:
    """Validates URLs in research documents and provides status reports"""

    def __init__(self, timeout: int = 10, max_concurrent: int = 10):
        self.timeout = aiohttp.ClientTimeout(total=timeout)
        self.max_concurrent = max_concurrent

    async def validate_single_url(self, session: aiohttp.ClientSession, url: str) -> Tuple[str, str, Optional[str]]:
        """
        Validate a single URL with HEAD request

        Returns:
            Tuple of (url, status, details)
            status: 'valid', 'redirect', 'warning', 'invalid'
        """
        try:
            async with session.head(url, timeout=self.timeout, allow_redirects=False) as response:
                if response.status == 200:
                    return (url, "valid", None)

                elif 300 <= response.status < 400:
                    location = response.headers.get('Location', 'Unknown')
                    return (url, "redirect", f"Redirects to {location}")

                elif 400 <= response.status < 500:
                    return (url, "invalid", f"Client error: {response.status}")

                elif 500 <= response.status < 600:
                    return (url, "warning", f"Server error: {response.status}")

                else:
                    return (url, "warning", f"Unexpected status: {response.status}")

        except asyncio.TimeoutError:
            return (url, "invalid", "Request timeout")

        except aiohttp.ClientError as e:
            return (url, "invalid", f"Connection error: {type(e).__name__}")

        except Exception as e:
            return (url, "invalid", f"Unexpected error: {type(e).__name__}")

    async def validate_urls_batch(self, urls: List[str]) -> List[Tuple[str, str, Optional[str]]]:
        """
        Validate multiple URLs concurrently

        Args:
            urls: List of URLs to validate

        Returns:
            List of (url, status, details) tuples
        """
        connector = aiohttp.TCPConnector(limit=self.max_concurrent)

        async with aiohttp.ClientSession(connector=connector, timeout=self.timeout) as session:
            tasks = [self.validate_single_url(session, url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)

            validated_results: List[Tuple[str, str, Optional[str]]] = []
            for result in results:
                if isinstance(result, Exception):
                    validated_results.append(("", "invalid", f"Validation error: {type(result).__name__}"))
                else:
                    validated_results.append(result)

            return validated_results

    def extract_urls_from_markdown(self, content: str) -> List[str]:
        """
        Extract URLs from markdown content

        Args:
            content: Markdown text

        Returns:
            List of unique URLs found in the content
        """
        url_pattern = r'https?://[^\s\)\]\}]+'
        urls = re.findall(url_pattern, content)

        urls = [url.rstrip('.,;:') for url in urls]

        return list(set(urls))

    def validate_markdown_file(self, file_path: str) -> Dict:
        """
        Validate all URLs in a markdown file

        Args:
            file_path: Path to markdown file

        Returns:
            Dictionary with validation results
        """
        path = Path(file_path)

        if not path.exists():
            return {
                "error": f"File not found: {file_path}",
                "valid": False
            }

        content = path.read_text(encoding="utf-8")
        urls = self.extract_urls_from_markdown(content)

        if not urls:
            return {
                "file": str(path),
                "total": 0,
                "valid": 0,
                "invalid": 0,
                "warning": 0,
                "redirect": 0,
                "urls": []
            }

        results = asyncio.run(self.validate_urls_batch(urls))

        summary = {
            "file": str(path),
            "total": len(results),
            "valid": 0,
            "invalid": 0,
            "warning": 0,
            "redirect": 0,
            "urls": []
        }

        for url, status, details in results:
            if isinstance(url, str):
                summary[status] = summary.get(status, 0) + 1
                summary["urls"].append({
                    "url": url,
                    "status": status,
                    "details": details
                })

        return summary

    def validate_directory(self, dir_path: str) -> Dict:
        """
        Validate all markdown files in a directory

        Args:
            dir_path: Path to directory containing markdown files

        Returns:
            Dictionary with aggregated results
        """
        path = Path(dir_path)

        if not path.exists() or not path.is_dir():
            return {
                "error": f"Directory not found: {dir_path}",
                "valid": False
            }

        md_files = list(path.glob("*.md"))

        if not md_files:
            return {
                "directory": str(path),
                "total_files": 0,
                "total_urls": 0,
                "files": []
            }

        aggregated = {
            "directory": str(path),
            "total_files": len(md_files),
            "total_urls": 0,
            "total_valid": 0,
            "total_invalid": 0,
            "total_warning": 0,
            "total_redirect": 0,
            "files": []
        }

        for md_file in md_files:
            result = self.validate_markdown_file(str(md_file))
            aggregated["files"].append(result)
            aggregated["total_urls"] += result.get("total", 0)
            aggregated["total_valid"] += result.get("valid", 0)
            aggregated["total_invalid"] += result.get("invalid", 0)
            aggregated["total_warning"] += result.get("warning", 0)
            aggregated["total_redirect"] += result.get("redirect", 0)

        return aggregated

    def generate_validation_report(self, results: Dict, output_format: str = "text") -> str:
        """
        Generate human-readable validation report

        Args:
            results: Validation results from validate_file or validate_directory
            output_format: 'text' or 'markdown'

        Returns:
            Formatted report string
        """
        if output_format == "markdown":
            return self._generate_markdown_report(results)
        else:
            return self._generate_text_report(results)

    def _generate_text_report(self, results: Dict) -> str:
        """Generate plain text report"""
        lines = []

        if "error" in results:
            lines.append(f"Error: {results['error']}")
            return "\n".join(lines)

        if "directory" in results:
            lines.append(f"\nURL Validation Report")
            lines.append(f"=" * 50)
            lines.append(f"Directory: {results['directory']}")
            lines.append(f"Total Files: {results['total_files']}")
            lines.append(f"Total URLs: {results['total_urls']}")
            lines.append("")
            lines.append(f"Summary:")
            lines.append(f"  ✓ Valid: {results['total_valid']}")
            lines.append(f"  ✗ Invalid: {results['total_invalid']}")
            lines.append(f"  ⚠ Warning: {results['total_warning']}")
            lines.append(f"  → Redirect: {results['total_redirect']}")
            lines.append("")

            for file_result in results["files"]:
                if file_result.get("total", 0) > 0:
                    lines.append(f"\n{Path(file_result['file']).name}:")
                    for url_info in file_result["urls"]:
                        status_icon = {
                            "valid": "✓",
                            "invalid": "✗",
                            "warning": "⚠",
                            "redirect": "→"
                        }.get(url_info["status"], "?")

                        lines.append(f"  {status_icon} {url_info['url']}")
                        if url_info["details"]:
                            lines.append(f"      {url_info['details']}")

        elif "file" in results:
            lines.append(f"\nURL Validation Report")
            lines.append(f"=" * 50)
            lines.append(f"File: {results['file']}")
            lines.append(f"Total URLs: {results['total']}")
            lines.append("")
            lines.append(f"Summary:")
            lines.append(f"  ✓ Valid: {results['valid']}")
            lines.append(f"  ✗ Invalid: {results['invalid']}")
            lines.append(f"  ⚠ Warning: {results['warning']}")
            lines.append(f"  → Redirect: {results['redirect']}")
            lines.append("")

            for url_info in results["urls"]:
                status_icon = {
                    "valid": "✓",
                    "invalid": "✗",
                    "warning": "⚠",
                    "redirect": "→"
                }.get(url_info["status"], "?")

                lines.append(f"  {status_icon} {url_info['url']}")
                if url_info["details"]:
                    lines.append(f"      {url_info['details']}")

        return "\n".join(lines)

    def _generate_markdown_report(self, results: Dict) -> str:
        """Generate markdown report"""
        lines = []

        if "error" in results:
            lines.append(f"# URL Validation Error\n\n**Error:** {results['error']}")
            return "\n".join(lines)

        if "directory" in results:
            lines.append(f"# URL Validation Report")
            lines.append(f"\n**Directory:** `{results['directory']}`")
            lines.append(f"**Total Files:** {results['total_files']}")
            lines.append(f"**Total URLs:** {results['total_urls']}")
            lines.append("\n## Summary\n")
            lines.append(f"- ✅ **Valid:** {results['total_valid']}")
            lines.append(f"- ❌ **Invalid:** {results['total_invalid']}")
            lines.append(f"- ⚠️ **Warning:** {results['total_warning']}")
            lines.append(f"- 🔄 **Redirect:** {results['total_redirect']}")
            lines.append("\n## Details\n")

            for file_result in results["files"]:
                if file_result.get("total", 0) > 0:
                    lines.append(f"\n### `{Path(file_result['file']).name}`\n")
                    for url_info in file_result["urls"]:
                        status_emoji = {
                            "valid": "✅",
                            "invalid": "❌",
                            "warning": "⚠️",
                            "redirect": "🔄"
                        }.get(url_info["status"], "❓")

                        lines.append(f"- {status_emoji} `{url_info['url']}`")
                        if url_info["details"]:
                            lines.append(f"  - *{url_info['details']}*")

        elif "file" in results:
            lines.append(f"# URL Validation Report")
            lines.append(f"\n**File:** `{results['file']}`")
            lines.append(f"**Total URLs:** {results['total']}")
            lines.append("\n## Summary\n")
            lines.append(f"- ✅ **Valid:** {results['valid']}")
            lines.append(f"- ❌ **Invalid:** {results['invalid']}")
            lines.append(f"- ⚠️ **Warning:** {results['warning']}")
            lines.append(f"- 🔄 **Redirect:** {results['redirect']}")
            lines.append("\n## URLs\n")

            for url_info in results["urls"]:
                status_emoji = {
                    "valid": "✅",
                    "invalid": "❌",
                    "warning": "⚠️",
                    "redirect": "🔄"
                }.get(url_info["status"], "❓")

                lines.append(f"- {status_emoji} `{url_info['url']}`")
                if url_info["details"]:
                    lines.append(f"  - *{url_info['details']}*")

        return "\n".join(lines)


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="ScholarStream URL Validator"
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    file_parser = subparsers.add_parser("file", help="Validate URLs in a file")
    file_parser.add_argument("file", help="Path to markdown file")
    file_parser.add_argument("--format", choices=["text", "markdown"],
                           default="text", help="Output format")

    dir_parser = subparsers.add_parser("dir", help="Validate URLs in a directory")
    dir_parser.add_argument("dir", help="Path to directory")
    dir_parser.add_argument("--format", choices=["text", "markdown"],
                          default="text", help="Output format")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(1)

    validator = URLValidator()

    if args.command == "file":
        results = validator.validate_markdown_file(args.file)
        print(validator.generate_validation_report(results, args.format))

    elif args.command == "dir":
        results = validator.validate_directory(args.dir)
        print(validator.generate_validation_report(results, args.format))


if __name__ == "__main__":
    main()
