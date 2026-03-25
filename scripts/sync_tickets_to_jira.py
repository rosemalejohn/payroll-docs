#!/usr/bin/env python3
"""
Sync markdown ticket files from tickets/ directory to Jira.

Usage:
  python scripts/sync_tickets_to_jira.py

Environment variables:
  JIRA_BASE_URL   - Jira instance URL (e.g. https://yourcompany.atlassian.net)
  JIRA_EMAIL       - Jira account email
  JIRA_API_TOKEN   - Jira API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)
  JIRA_PROJECT_KEY - Jira project key (e.g. PAY)
  DRY_RUN          - Set to "true" to preview without creating tickets
"""

from __future__ import annotations

import os
import re
import sys
import json
import glob
import base64
import urllib.request
import urllib.error
import urllib.parse


# ---------------------------------------------------------------------------
# Configuration (from environment)
# ---------------------------------------------------------------------------
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "")       # e.g. https://yourcompany.atlassian.net
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "")              # e.g. you@company.com
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")      # API token
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "PAY")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

TICKETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tickets")

# Map ticket number ranges to epic names (adjust as needed)
EPIC_MAP = {
    range(1, 15):  "Project Setup & Infrastructure",
    range(21, 29): "Database & Seeders",
    range(41, 58): "Payroll Processing Engine",
    range(61, 87): "UI & Workflows",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def jira_auth_header() -> str:
    """Return base64-encoded Basic auth header value."""
    credentials = f"{JIRA_EMAIL}:{JIRA_API_TOKEN}"
    return "Basic " + base64.b64encode(credentials.encode()).decode()


def jira_request(method: str, path: str, data: dict | None = None) -> dict:
    """Make an authenticated request to the Jira REST API."""
    url = f"{JIRA_BASE_URL}/rest/api/3/{path.lstrip('/')}"
    body = json.dumps(data).encode() if data else None

    req = urllib.request.Request(
        url,
        data=body,
        method=method,
        headers={
            "Authorization": jira_auth_header(),
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )

    try:
        with urllib.request.urlopen(req) as resp:
            resp_body = resp.read().decode()
            return json.loads(resp_body) if resp_body else {}
    except urllib.error.HTTPError as e:
        error_body = e.read().decode() if e.fp else ""
        print(f"  ERROR {e.code}: {error_body}", file=sys.stderr)
        raise


def get_existing_tickets() -> dict[str, str]:
    """Fetch existing tickets in the project, return {summary: issue_key} map."""
    jql = f'project = "{JIRA_PROJECT_KEY}" ORDER BY created ASC'
    start = 0
    existing = {}

    while True:
        result = jira_request("GET", f"search?jql={urllib.parse.quote(jql)}&startAt={start}&maxResults=100&fields=summary")
        for issue in result.get("issues", []):
            existing[issue["fields"]["summary"]] = issue["key"]
        total = result.get("total", 0)
        start += len(result.get("issues", []))
        if start >= total:
            break

    return existing


def parse_ticket_file(filepath: str) -> dict:
    """Parse a ticket markdown file into title, description, and acceptance criteria."""
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Extract title from first H1
    title_match = re.match(r"^#\s+(.+)$", content, re.MULTILINE)
    title = title_match.group(1).strip() if title_match else os.path.basename(filepath)

    # Extract ticket key from filename (e.g. PAY-001)
    ticket_key = re.search(r"(PAY-\d+)", os.path.basename(filepath))
    ticket_id = ticket_key.group(1) if ticket_key else ""

    # Extract number for epic mapping
    num_match = re.search(r"PAY-(\d+)", ticket_id)
    ticket_num = int(num_match.group(1)) if num_match else 0

    # Split into sections
    description_section = ""
    tech_section = ""
    acceptance_section = ""

    # Get Description section
    desc_match = re.search(r"## Description\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if desc_match:
        description_section = desc_match.group(1).strip()

    # Get Technical Implementation section
    tech_match = re.search(r"## Technical Implementation\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if tech_match:
        tech_section = tech_match.group(1).strip()

    # Get Acceptance Criteria section
    ac_match = re.search(r"## Acceptance Criteria\s*\n(.*?)(?=\n## |\Z)", content, re.DOTALL)
    if ac_match:
        acceptance_section = ac_match.group(1).strip()

    # Determine epic
    epic_name = "Uncategorized"
    for num_range, name in EPIC_MAP.items():
        if ticket_num in num_range:
            epic_name = name
            break

    return {
        "ticket_id": ticket_id,
        "ticket_num": ticket_num,
        "title": title,
        "description": description_section,
        "technical": tech_section,
        "acceptance_criteria": acceptance_section,
        "epic_name": epic_name,
    }


def markdown_to_adf(markdown_text: str) -> dict:
    """
    Convert markdown text to Atlassian Document Format (ADF).
    Handles headings, bullet lists, checkboxes, code blocks, and paragraphs.
    """
    doc = {"version": 1, "type": "doc", "content": []}

    lines = markdown_text.split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]

        # Skip empty lines
        if not line.strip():
            i += 1
            continue

        # Code block
        if line.strip().startswith("```"):
            lang = line.strip().lstrip("`").strip() or None
            code_lines = []
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                code_lines.append(lines[i])
                i += 1
            i += 1  # skip closing ```

            code_block = {
                "type": "codeBlock",
                "content": [{"type": "text", "text": "\n".join(code_lines)}],
            }
            if lang:
                code_block["attrs"] = {"language": lang}
            doc["content"].append(code_block)
            continue

        # Headings (### -> h3, #### -> h4, etc.)
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            level = len(heading_match.group(1))
            doc["content"].append({
                "type": "heading",
                "attrs": {"level": level},
                "content": [{"type": "text", "text": heading_match.group(2).strip()}],
            })
            i += 1
            continue

        # Bullet list / checkbox items
        if re.match(r"^\s*[-*]\s", line):
            list_items = []
            while i < len(lines) and re.match(r"^\s*[-*]\s", lines[i]):
                item_text = re.sub(r"^\s*[-*]\s+", "", lines[i])
                # Convert checkbox syntax
                item_text = re.sub(r"^\[[ x]\]\s*", "", item_text)
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": _inline_marks(item_text),
                    }],
                })
                i += 1

            doc["content"].append({
                "type": "bulletList",
                "content": list_items,
            })
            continue

        # Regular paragraph
        doc["content"].append({
            "type": "paragraph",
            "content": _inline_marks(line),
        })
        i += 1

    return doc


def _inline_marks(text: str) -> list[dict]:
    """Parse inline markdown (bold, code, links) into ADF inline nodes."""
    nodes = []
    # Split on inline code, bold, and regular text
    parts = re.split(r"(`[^`]+`|\*\*[^*]+\*\*|\[[^\]]+\]\([^)]+\))", text)

    for part in parts:
        if not part:
            continue

        # Inline code
        if part.startswith("`") and part.endswith("`"):
            nodes.append({
                "type": "text",
                "text": part[1:-1],
                "marks": [{"type": "code"}],
            })
        # Bold
        elif part.startswith("**") and part.endswith("**"):
            nodes.append({
                "type": "text",
                "text": part[2:-2],
                "marks": [{"type": "strong"}],
            })
        # Link
        elif re.match(r"\[([^\]]+)\]\(([^)]+)\)", part):
            m = re.match(r"\[([^\]]+)\]\(([^)]+)\)", part)
            nodes.append({
                "type": "text",
                "text": m.group(1),
                "marks": [{"type": "link", "attrs": {"href": m.group(2)}}],
            })
        else:
            nodes.append({"type": "text", "text": part})

    return nodes if nodes else [{"type": "text", "text": text}]


def build_issue_payload(ticket: dict) -> dict:
    """Build the Jira issue creation payload from a parsed ticket."""
    # Combine description + technical + acceptance criteria into one ADF body
    full_markdown = ticket["description"]
    if ticket["technical"]:
        full_markdown += f"\n\n## Technical Implementation\n\n{ticket['technical']}"
    if ticket["acceptance_criteria"]:
        full_markdown += f"\n\n## Acceptance Criteria\n\n{ticket['acceptance_criteria']}"

    description_adf = markdown_to_adf(full_markdown)

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": ticket["title"],
            "description": description_adf,
            "issuetype": {"name": "Story"},
            "labels": ["auto-synced", f"epic-{ticket['epic_name'].lower().replace(' ', '-')}"],
        }
    }

    return payload


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not JIRA_BASE_URL or not JIRA_EMAIL or not JIRA_API_TOKEN:
        if not DRY_RUN:
            print("ERROR: JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set.", file=sys.stderr)
            print("Set DRY_RUN=true to preview without Jira credentials.", file=sys.stderr)
            sys.exit(1)

    # Discover ticket files
    ticket_files = sorted(glob.glob(os.path.join(TICKETS_DIR, "PAY-*.md")))
    if not ticket_files:
        print("No ticket files found in tickets/ directory.")
        sys.exit(0)

    print(f"Found {len(ticket_files)} ticket file(s) in {TICKETS_DIR}")
    print(f"Project key: {JIRA_PROJECT_KEY}")
    print(f"Dry run: {DRY_RUN}")
    print()

    # Get existing tickets to avoid duplicates (skip in dry run without creds)
    existing = {}
    if not DRY_RUN and JIRA_BASE_URL:
        print("Fetching existing Jira tickets...")
        existing = get_existing_tickets()
        print(f"  Found {len(existing)} existing ticket(s)")
        print()

    created = 0
    skipped = 0
    errors = 0

    for filepath in ticket_files:
        filename = os.path.basename(filepath)
        ticket = parse_ticket_file(filepath)

        print(f"[{ticket['ticket_id']}] {ticket['title']}")
        print(f"  Epic: {ticket['epic_name']}")

        # Check if already exists (by summary match)
        if ticket["title"] in existing:
            print(f"  SKIP: Already exists as {existing[ticket['title']]}")
            skipped += 1
            print()
            continue

        if DRY_RUN:
            payload = build_issue_payload(ticket)
            print(f"  DRY RUN: Would create issue with {len(json.dumps(payload))} bytes")
            print(f"  Labels: {payload['fields']['labels']}")
            created += 1
            print()
            continue

        # Create the issue
        try:
            payload = build_issue_payload(ticket)
            result = jira_request("POST", "issue", payload)
            issue_key = result.get("key", "???")
            print(f"  CREATED: {issue_key}")
            print(f"  URL: {JIRA_BASE_URL}/browse/{issue_key}")
            created += 1
        except Exception as e:
            print(f"  FAILED: {e}", file=sys.stderr)
            errors += 1

        print()

    # Summary
    print("=" * 60)
    print(f"Done! Created: {created}, Skipped: {skipped}, Errors: {errors}")

    if errors > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
