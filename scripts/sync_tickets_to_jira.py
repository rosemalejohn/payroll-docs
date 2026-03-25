#!/usr/bin/env python3
"""
Sync markdown ticket files from tickets/ directory to Jira.

Usage:
  python scripts/sync_tickets_to_jira.py

Environment variables:
  JIRA_BASE_URL    - Jira instance URL (e.g. https://yourcompany.atlassian.net)
  JIRA_EMAIL       - Jira account email
  JIRA_API_TOKEN   - Jira API token (create at https://id.atlassian.com/manage-profile/security/api-tokens)
  JIRA_PROJECT_KEY - Jira project key (e.g. PAY)
  DRY_RUN          - Set to "true" to preview without creating tickets

Field Mapping:
  The script maps markdown sections to Jira fields as follows:
  - Description section → Jira "Description" field (standard)
  - Technical Implementation section → Custom field (if available)
  - Acceptance Criteria section → Custom field (if available)
  
  The script automatically discovers custom fields from your Jira instance.
  Update the build_issue_payload() function to map custom field IDs if needed.
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
JIRA_BASE_URL = os.environ.get("JIRA_BASE_URL", "https://geekee.atlassian.net")
JIRA_EMAIL = os.environ.get("JIRA_EMAIL", "harley@creativextechlabsinc.com")
JIRA_API_TOKEN = os.environ.get("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.environ.get("JIRA_PROJECT_KEY", "GEEK")
DRY_RUN = os.environ.get("DRY_RUN", "false").lower() == "true"

TICKETS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "tickets")

# Map ticket number ranges to epic names (adjust as needed)
EPIC_MAP = {
    range(1, 6):   "Foundation",
    range(6, 21):  "Database Schema",
    range(21, 26): "Seeders & Frontend Shell",
    range(26, 31): "Employee Management",
    range(31, 37): "HRIS & Users & Currency",
    range(37, 41): "Payroll Periods & Runs",
    range(41, 44): "State Machine & Run Management",
    range(44, 51): "Computation Engine",
    range(51, 55): "Bonus Manager",
    range(55, 57): "Cash Advances",
    range(57, 61): "Review Workflow",
    range(61, 63): "Finalization & Approval",
    range(63, 67): "Payslips & PDF",
    range(67, 71): "Reports & Exports",
    range(71, 76): "Audit & Notifications",
    range(76, 81): "Edge Cases",
    range(81, 89): "Access Control & Polish",
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


def get_custom_fields() -> dict[str, str]:
    """Fetch all custom fields in the Jira instance, return {field_name: field_id} map."""
    result = jira_request("GET", "field")
    custom_fields = {}
    for field in result:
        if field["id"].startswith("customfield_"):
            custom_fields[field["name"]] = field["id"]
    return custom_fields


def get_existing_tickets() -> dict[str, str]:
    """Fetch existing tickets in the project, return {summary: issue_key} map."""
    jql = f'project = "{JIRA_PROJECT_KEY}" ORDER BY created ASC'
    start = 0
    existing = {}

    while True:
        params = urllib.parse.urlencode({
            "jql": jql,
            "startAt": start,
            "maxResults": 100,
            "fields": "summary",
        })
        result = jira_request("GET", f"search/jql?{params}")
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


def markdown_to_plain(markdown_text: str) -> str:
    """
    Convert markdown to clean, readable plain text for Jira textarea fields.
    Strips markdown syntax while preserving structure and readability.
    """
    lines = markdown_text.split("\n")
    result = []
    i = 0

    while i < len(lines):
        line = lines[i]

        # Code block — preserve content, strip fences
        if line.strip().startswith("```"):
            i += 1
            result.append("---")
            while i < len(lines) and not lines[i].strip().startswith("```"):
                result.append("  " + lines[i])
                i += 1
            result.append("---")
            i += 1
            continue

        # Headings → UPPERCASE with underline
        heading_match = re.match(r"^(#{1,6})\s+(.+)$", line)
        if heading_match:
            text = heading_match.group(2).strip()
            result.append("")
            result.append(text.upper())
            result.append("─" * len(text))
            i += 1
            continue

        # Checkboxes → ☐ / ☑
        checkbox_match = re.match(r"^\s*[-*]\s+\[( |x)\]\s*(.+)$", line)
        if checkbox_match:
            checked = checkbox_match.group(1) == "x"
            text = _strip_inline_markdown(checkbox_match.group(2))
            marker = "☑" if checked else "☐"
            result.append(f"  {marker} {text}")
            i += 1
            continue

        # Bullet list items → •
        bullet_match = re.match(r"^(\s*)[-*]\s+(.+)$", line)
        if bullet_match:
            indent = "  " * (len(bullet_match.group(1)) // 2 + 1)
            text = _strip_inline_markdown(bullet_match.group(2))
            result.append(f"{indent}• {text}")
            i += 1
            continue

        # Regular text — strip inline markdown
        result.append(_strip_inline_markdown(line))
        i += 1

    # Clean up extra blank lines
    text = "\n".join(result).strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text


def _strip_inline_markdown(text: str) -> str:
    """Remove inline markdown syntax (bold, code, links) leaving clean text."""
    # Links [text](url) → text
    text = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", text)
    # Bold **text** → text
    text = re.sub(r"\*\*([^*]+)\*\*", r"\1", text)
    # Inline code `text` → text
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


def _plain_text_adf(markdown_text: str) -> dict:
    """Convert markdown to a plain-text ADF document (single paragraph with newlines)."""
    plain = markdown_to_plain(markdown_text)
    doc = {"version": 1, "type": "doc", "content": []}
    for paragraph in plain.split("\n\n"):
        if paragraph.strip():
            doc["content"].append({
                "type": "paragraph",
                "content": [{"type": "text", "text": paragraph.strip()}],
            })
    return doc


def _parse_section_lines(section_lines: list[str]) -> list[dict]:
    """Parse markdown lines into ADF content nodes (bullets, code, paragraphs)."""
    nodes = []
    j = 0
    while j < len(section_lines):
        line = section_lines[j]

        if not line.strip():
            j += 1
            continue

        # Code block
        if line.strip().startswith("```"):
            lang = line.strip().lstrip("`").strip() or None
            code_lines = []
            j += 1
            while j < len(section_lines) and not section_lines[j].strip().startswith("```"):
                code_lines.append(section_lines[j])
                j += 1
            j += 1
            code_block = {
                "type": "codeBlock",
                "content": [{"type": "text", "text": "\n".join(code_lines)}],
            }
            if lang:
                code_block["attrs"] = {"language": lang}
            nodes.append(code_block)
            continue

        # Bullet list
        if re.match(r"^\s*[-*]\s", line):
            list_items = []
            while j < len(section_lines) and re.match(r"^\s*[-*]\s", section_lines[j]):
                item_text = re.sub(r"^\s*[-*]\s+", "", section_lines[j])
                item_text = re.sub(r"^\[[ x]\]\s*", "", item_text)
                list_items.append({
                    "type": "listItem",
                    "content": [{
                        "type": "paragraph",
                        "content": _inline_marks(item_text),
                    }],
                })
                j += 1
            nodes.append({"type": "bulletList", "content": list_items})
            continue

        # Regular paragraph
        nodes.append({"type": "paragraph", "content": _inline_marks(line)})
        j += 1

    return nodes


def _build_tech_impl_adf(markdown_text: str) -> dict:
    """
    Build a beautiful ADF document for Technical Implementation.
    Each ### section gets a bold heading + divider + content in a colored panel.
    """
    doc = {"version": 1, "type": "doc", "content": []}
    lines = markdown_text.split("\n")

    panel_types = ["info", "note", "success", "warning"]
    panel_idx = 0

    i = 0
    current_section_title = None
    current_section_content = []

    def flush_section():
        nonlocal panel_idx
        if current_section_title is None and not current_section_content:
            return

        panel_content = []

        # Section title as bold paragraph
        if current_section_title:
            panel_content.append({
                "type": "paragraph",
                "content": [
                    {"type": "text", "text": "── "},
                    {"type": "text", "text": current_section_title.upper(), "marks": [{"type": "strong"}]},
                    {"type": "text", "text": " ──"},
                ],
            })

        # Parse content
        panel_content.extend(_parse_section_lines(current_section_content))

        if panel_content:
            panel_type = panel_types[panel_idx % len(panel_types)]
            doc["content"].append({
                "type": "panel",
                "attrs": {"panelType": panel_type},
                "content": panel_content,
            })
            panel_idx += 1

    while i < len(lines):
        line = lines[i]

        h3_match = re.match(r"^###\s+(.+)$", line)
        if h3_match:
            flush_section()
            current_section_title = h3_match.group(1).strip()
            current_section_content = []
            i += 1
            continue

        current_section_content.append(line)
        i += 1

    flush_section()

    return doc


def _build_acceptance_criteria_adf(markdown_text: str) -> dict:
    """
    Build a beautiful ADF document for Acceptance Criteria.
    Uses a numbered ordered list inside a success panel for clean checklist look.
    """
    doc = {"version": 1, "type": "doc", "content": []}
    lines = markdown_text.split("\n")

    list_items = []
    other_content = []

    for line in lines:
        if not line.strip():
            continue

        # Checkbox items
        checkbox_match = re.match(r"^\s*[-*]\s+\[( |x)\]\s*(.+)$", line)
        if checkbox_match:
            item_text = checkbox_match.group(2).strip()
            list_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": _inline_marks(item_text),
                }],
            })
            continue

        # Regular bullet
        bullet_match = re.match(r"^\s*[-*]\s+(.+)$", line)
        if bullet_match:
            item_text = bullet_match.group(1).strip()
            list_items.append({
                "type": "listItem",
                "content": [{
                    "type": "paragraph",
                    "content": _inline_marks(item_text),
                }],
            })
            continue

        other_content.append(line)

    panel_content = []

    # Title
    panel_content.append({
        "type": "paragraph",
        "content": [
            {"type": "text", "text": "── "},
            {"type": "text", "text": "ACCEPTANCE CHECKLIST", "marks": [{"type": "strong"}]},
            {"type": "text", "text": " ──"},
        ],
    })

    # Ordered list for criteria
    if list_items:
        panel_content.append({
            "type": "orderedList",
            "attrs": {"order": 1},
            "content": list_items,
        })

    # Any other content
    for line in other_content:
        if line.strip():
            panel_content.append({
                "type": "paragraph",
                "content": _inline_marks(line),
            })

    doc["content"].append({
        "type": "panel",
        "attrs": {"panelType": "success"},
        "content": panel_content,
    })

    return doc


def build_issue_payload(ticket: dict) -> dict:
    """Build the Jira issue creation payload from a parsed ticket."""
    # Map sections to separate Jira fields
    description_adf = markdown_to_adf(ticket["description"]) if ticket["description"] else {"version": 1, "type": "doc", "content": []}
    technical_adf = markdown_to_adf(ticket["technical"]) if ticket["technical"] else {"version": 1, "type": "doc", "content": []}
    acceptance_adf = markdown_to_adf(ticket["acceptance_criteria"]) if ticket["acceptance_criteria"] else {"version": 1, "type": "doc", "content": []}

    payload = {
        "fields": {
            "project": {"key": JIRA_PROJECT_KEY},
            "summary": ticket["title"],
            "description": description_adf,
            "issuetype": {"name": "Story"},
            "labels": ["auto-synced", f"epic-{ticket['epic_name'].lower().replace(' ', '-').replace('&', 'and')}"],
        }
    }

    # Add custom fields if they exist (customize field IDs based on your Jira instance)
    # You can find field IDs by calling: GET /rest/api/3/field
    # Common custom field naming: customfield_XXXXX
    # Uncomment and adjust these based on your Jira setup:
    
    # if technical_adf["content"]:  # Only add if not empty
    #     payload["fields"]["customfield_10000"] = technical_adf  # Replace with your Technical Implementation field ID
    
    # if acceptance_adf["content"]:  # Only add if not empty
    #     payload["fields"]["customfield_10001"] = acceptance_adf  # Replace with your Acceptance Criteria field ID

    return payload


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    if not JIRA_BASE_URL or not JIRA_EMAIL or not JIRA_API_TOKEN:
        if not DRY_RUN:
            print("ERROR: JIRA_BASE_URL, JIRA_EMAIL, and JIRA_API_TOKEN must be set.", file=sys.stderr)
            print("  Create an API token at https://id.atlassian.com/manage-profile/security/api-tokens", file=sys.stderr)
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

    # Get custom fields and existing tickets (skip in dry run without creds)
    custom_fields = {}
    existing = {}
    if not DRY_RUN and JIRA_BASE_URL:
        print("Discovering custom fields...")
        try:
            custom_fields = get_custom_fields()
            if custom_fields:
                print(f"  Found custom fields:")
                for name, field_id in custom_fields.items():
                    print(f"    - {name}: {field_id}")
            print()
        except Exception as e:
            print(f"  WARNING: Could not fetch custom fields: {e}", file=sys.stderr)
            print()

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
            print(f"  Fields: {list(payload['fields'].keys())}")
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
