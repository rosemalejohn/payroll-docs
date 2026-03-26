#!/usr/bin/env python3
"""Create a Google Slides presentation for PayHRIS Payroll epics overview."""

import os
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = [
    "https://www.googleapis.com/auth/presentations",
    "https://www.googleapis.com/auth/drive.file",
]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(SCRIPT_DIR, "credentials.json")
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")

# -- Color palette --
WHITE = {"red": 1.0, "green": 1.0, "blue": 1.0}
DARK_BG = {"red": 0.11, "green": 0.11, "blue": 0.14}
ACCENT_BLUE = {"red": 0.24, "green": 0.47, "blue": 0.96}
LIGHT_GRAY = {"red": 0.85, "green": 0.85, "blue": 0.85}
MEDIUM_GRAY = {"red": 0.6, "green": 0.6, "blue": 0.6}
ACCENT_GREEN = {"red": 0.18, "green": 0.74, "blue": 0.49}
ACCENT_ORANGE = {"red": 0.96, "green": 0.62, "blue": 0.14}
ACCENT_PURPLE = {"red": 0.56, "green": 0.34, "blue": 0.87}
ACCENT_RED = {"red": 0.91, "green": 0.30, "blue": 0.24}
ACCENT_TEAL = {"red": 0.14, "green": 0.70, "blue": 0.76}

# Slide dimensions (default 10x5.625 inches, in EMU: 1 inch = 914400 EMU)
SLIDE_W = 9144000
SLIDE_H = 5143500

EMU_PT = 12700  # 1 pt in EMU


def auth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def emu(inches):
    return int(inches * 914400)


def pt(points):
    return {"magnitude": points, "unit": "PT"}


def text_style(font_size, color, bold=False, italic=False, font_family="Inter"):
    style = {
        "fontSize": pt(font_size),
        "foregroundColor": {"opaqueColor": {"rgbColor": color}},
        "bold": bold,
        "italic": italic,
        "fontFamily": font_family,
    }
    return style


def create_shape_request(page_id, shape_id, x, y, w, h):
    return {
        "createShape": {
            "objectId": shape_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": page_id,
                "size": {
                    "width": {"magnitude": w, "unit": "EMU"},
                    "height": {"magnitude": h, "unit": "EMU"},
                },
                "transform": {
                    "scaleX": 1,
                    "scaleY": 1,
                    "translateX": x,
                    "translateY": y,
                    "unit": "EMU",
                },
            },
        }
    }


def insert_text_request(shape_id, text, index=0):
    return {"insertText": {"objectId": shape_id, "text": text, "insertionIndex": index}}


def style_text_request(shape_id, style, start=0, end=None, text=""):
    end_index = end if end is not None else len(text)
    return {
        "updateTextStyle": {
            "objectId": shape_id,
            "style": style,
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end_index},
            "fields": "fontSize,foregroundColor,bold,italic,fontFamily",
        }
    }


def set_bg(page_id, color):
    return {
        "updatePageProperties": {
            "objectId": page_id,
            "pageProperties": {
                "pageBackgroundFill": {
                    "solidFill": {"color": {"rgbColor": color}}
                }
            },
            "fields": "pageBackgroundFill.solidFill.color",
        }
    }


def para_style_request(shape_id, alignment, start=0, end=None, text=""):
    end_index = end if end is not None else len(text)
    return {
        "updateParagraphStyle": {
            "objectId": shape_id,
            "style": {"alignment": alignment},
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end_index},
            "fields": "alignment",
        }
    }


# -- Epic data --
EPICS = [
    {
        "id": "EP-01",
        "title": "Project Setup & Infrastructure",
        "tickets": 6,
        "color": ACCENT_BLUE,
        "bullets": [
            "Laravel 12 + Inertia.js + React 19 + TypeScript",
            "Tailwind CSS v4, Shadcn/ui component library",
            "Domain-driven folder structure",
            "Database seeders & shared props middleware",
            "Comprehensive Pest test suite",
        ],
    },
    {
        "id": "EP-02",
        "title": "Authentication & User Management",
        "tickets": 5,
        "color": ACCENT_GREEN,
        "bullets": [
            "Login/logout/session management",
            "4 roles: Owner, Payroll Officer, Finance, Employee",
            "Spatie roles & permissions integration",
            "Owner-only user management page",
            "Role-based access control enforcement",
        ],
    },
    {
        "id": "EP-03",
        "title": "Database Schema & Models",
        "tickets": 15,
        "color": ACCENT_ORANGE,
        "bullets": [
            "15 core migrations with Eloquent models & factories",
            "Companies, Users, Employees, Currencies",
            "Payroll Runs with state machine (draft > finalized)",
            "Payslips, Line Items, Bonus Types",
            "Cash Advances & Currency Snapshots",
        ],
    },
    {
        "id": "EP-04",
        "title": "UI Foundation & Reusable Components",
        "tickets": 3,
        "color": ACCENT_PURPLE,
        "bullets": [
            "Authenticated layout shell (sidebar + header)",
            "Reusable data table with sort/filter/pagination",
            "Reusable form components for consistency",
        ],
    },
    {
        "id": "EP-05",
        "title": "Employee Management & HRIS Sync",
        "tickets": 6,
        "color": ACCENT_TEAL,
        "bullets": [
            "Employee CRUD with filters & pagination",
            "Compensation management UI",
            "External salary flags & payroll-specific settings",
            "Employee deactivation with confirmation",
            "Daily HRIS sync job (API-based)",
        ],
    },
    {
        "id": "EP-06",
        "title": "Currency Management",
        "tickets": 7,
        "color": ACCENT_RED,
        "bullets": [
            "Currency CRUD with exchange rates",
            "Deactivation with safety checks",
            "Snapshot rates for historical integrity",
            "Mid-run rate update warnings",
            "Missing currency rate detection",
        ],
    },
    {
        "id": "EP-07",
        "title": "Payroll Run Lifecycle",
        "tickets": 11,
        "color": ACCENT_BLUE,
        "bullets": [
            "Period CRUD & run creation with employee roster",
            "State machine: Draft > Submitted > Under Review > Finalized",
            "Add/remove employees from draft runs",
            "Absent days entry per employee",
            "Submit for review, return to draft, duplicate prevention",
        ],
    },
    {
        "id": "EP-08",
        "title": "Payroll Computation Engine",
        "tickets": 9,
        "color": ACCENT_GREEN,
        "bullets": [
            "10-step gross-to-net pipeline (ComputePayslipAction)",
            "Gross pay, bonuses, absent deductions",
            "SSS, PhilHealth, Pag-IBIG, HMO, voluntary deductions",
            "BIR withholding tax (TRAIN Law brackets)",
            "External salary path, batch recompute, BIR overrides",
        ],
    },
    {
        "id": "EP-09",
        "title": "Bonus Management",
        "tickets": 4,
        "color": ACCENT_ORANGE,
        "bullets": [
            "Bonus type CRUD in settings",
            "Auto-attach bonuses to new payroll runs",
            "Per-run bonus configuration UI",
            "Per-employee bonus exclusions",
        ],
    },
    {
        "id": "EP-10",
        "title": "Cash Advance Management",
        "tickets": 2,
        "color": ACCENT_PURPLE,
        "bullets": [
            "Cash advance CRUD for recording & tracking",
            "Automatic recovery/deduction upon finalization",
        ],
    },
    {
        "id": "EP-11",
        "title": "Finance Review & Finalization",
        "tickets": 4,
        "color": ACCENT_TEAL,
        "bullets": [
            "Finance review page for submitted runs",
            "Approval action (Finance role)",
            "Finalization action (Owner only)",
            "Employer contribution summary display",
        ],
    },
    {
        "id": "EP-12",
        "title": "Payslip Generation & Viewing",
        "tickets": 5,
        "color": ACCENT_RED,
        "bullets": [
            "PDF generation via barryvdh/laravel-dompdf",
            "Draft watermark on preview payslips",
            "Employee payslip list & detail views",
            "Full deduction/bonus breakdown",
            "Dual currency display for foreign salary employees",
        ],
    },
    {
        "id": "EP-13",
        "title": "Reporting & Export",
        "tickets": 3,
        "color": ACCENT_BLUE,
        "bullets": [
            "Payroll summary report page",
            "CSV & PDF export for finalized runs",
            "Government remittance reports (SSS, PhilHealth, Pag-IBIG, BIR)",
        ],
    },
    {
        "id": "EP-14",
        "title": "Audit Trail",
        "tickets": 3,
        "color": ACCENT_GREEN,
        "bullets": [
            "owen-it/laravel-auditing integration",
            "Filterable audit trail page (user, model, date, action)",
            "Payroll run audit history tab",
        ],
    },
    {
        "id": "EP-15",
        "title": "Notifications",
        "tickets": 2,
        "color": ACCENT_ORANGE,
        "bullets": [
            "In-app notification system (bell icon + panel)",
            "Payroll workflow notifications (state transitions)",
        ],
    },
    {
        "id": "EP-16",
        "title": "Edge Cases & Business Rules",
        "tickets": 2,
        "color": ACCENT_PURPLE,
        "bullets": [
            "Mid-month termination with prorated salary",
            "New employee HMO proration for mid-period joins",
        ],
    },
    {
        "id": "EP-17",
        "title": "Dashboard",
        "tickets": 1,
        "color": ACCENT_TEAL,
        "bullets": [
            "Payroll overview with key metrics",
            "Recent/active payroll runs display",
            "Quick action shortcuts, role-specific views",
        ],
    },
]


def build_requests(presentation_id):
    requests = []
    page_ids = []

    # ─── Helper to add a slide ───
    def add_slide(page_id):
        page_ids.append(page_id)
        requests.append(
            {"createSlide": {"objectId": page_id, "slideLayoutReference": {"predefinedLayout": "BLANK"}}}
        )
        requests.append(set_bg(page_id, DARK_BG))

    # ═══════════════════════════════════════
    # SLIDE 0 — TITLE
    # ═══════════════════════════════════════
    slide_id = "slide_title"
    add_slide(slide_id)

    # Accent bar at top
    bar_id = f"{slide_id}_bar"
    requests.append(
        {
            "createShape": {
                "objectId": bar_id,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": SLIDE_W, "unit": "EMU"}, "height": {"magnitude": emu(0.06), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"},
                },
            }
        }
    )
    requests.append(
        {
            "updateShapeProperties": {
                "objectId": bar_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": ACCENT_BLUE}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        }
    )

    # Title text
    title_id = f"{slide_id}_title"
    title_text = "PayHRIS Payroll"
    requests.append(create_shape_request(slide_id, title_id, emu(0.8), emu(1.4), emu(8.4), emu(1.0)))
    requests.append(insert_text_request(title_id, title_text))
    requests.append(style_text_request(title_id, text_style(44, WHITE, bold=True), 0, len(title_text), title_text))
    requests.append(para_style_request(title_id, "CENTER", 0, len(title_text), title_text))

    # Subtitle
    sub_id = f"{slide_id}_sub"
    sub_text = "Project Epics Overview"
    requests.append(create_shape_request(slide_id, sub_id, emu(0.8), emu(2.3), emu(8.4), emu(0.6)))
    requests.append(insert_text_request(sub_id, sub_text))
    requests.append(style_text_request(sub_id, text_style(24, LIGHT_GRAY, italic=True), 0, len(sub_text), sub_text))
    requests.append(para_style_request(sub_id, "CENTER", 0, len(sub_text), sub_text))

    # Meta line
    meta_id = f"{slide_id}_meta"
    meta_text = "17 Epics  \u2022  88 Tickets  \u2022  Laravel 12 + React 19 + TypeScript"
    requests.append(create_shape_request(slide_id, meta_id, emu(0.8), emu(3.2), emu(8.4), emu(0.5)))
    requests.append(insert_text_request(meta_id, meta_text))
    requests.append(style_text_request(meta_id, text_style(14, MEDIUM_GRAY), 0, len(meta_text), meta_text))
    requests.append(para_style_request(meta_id, "CENTER", 0, len(meta_text), meta_text))

    # ═══════════════════════════════════════
    # SLIDE 1 — TECH STACK
    # ═══════════════════════════════════════
    slide_id = "slide_techstack"
    add_slide(slide_id)

    # Section header
    hdr_id = f"{slide_id}_hdr"
    hdr_text = "Technology Stack"
    requests.append(create_shape_request(slide_id, hdr_id, emu(0.8), emu(0.35), emu(8.4), emu(0.6)))
    requests.append(insert_text_request(hdr_id, hdr_text))
    requests.append(style_text_request(hdr_id, text_style(28, ACCENT_BLUE, bold=True), 0, len(hdr_text), hdr_text))

    # Two-column layout
    left_items = [
        ("Backend", "Laravel 12, PHP 8.4+"),
        ("Frontend", "React 19, TypeScript, Inertia.js v2"),
        ("Styling", "Tailwind CSS v4, Shadcn/ui"),
        ("State", "Zustand"),
    ]
    right_items = [
        ("Database", "MySQL (ULIDs, app-layer integrity)"),
        ("Cache/Queue", "Redis"),
        ("Testing", "Pest PHP"),
        ("PDF/Excel", "DomPDF, Laravel Excel"),
    ]

    for col_idx, items in enumerate([left_items, right_items]):
        x = emu(0.8) if col_idx == 0 else emu(5.2)
        for i, (label, value) in enumerate(items):
            box_id = f"{slide_id}_col{col_idx}_item{i}"
            full_text = f"{label}\n{value}"
            requests.append(create_shape_request(slide_id, box_id, x, emu(1.2 + i * 1.0), emu(4.0), emu(0.9)))
            requests.append(insert_text_request(box_id, full_text))
            requests.append(style_text_request(box_id, text_style(11, MEDIUM_GRAY, bold=True), 0, len(label), full_text))
            requests.append(style_text_request(box_id, text_style(16, WHITE), len(label) + 1, len(full_text), full_text))

    # ═══════════════════════════════════════
    # SLIDE 2 — ARCHITECTURE
    # ═══════════════════════════════════════
    slide_id = "slide_arch"
    add_slide(slide_id)

    hdr_id = f"{slide_id}_hdr"
    hdr_text = "Architecture Highlights"
    requests.append(create_shape_request(slide_id, hdr_id, emu(0.8), emu(0.35), emu(8.4), emu(0.6)))
    requests.append(insert_text_request(hdr_id, hdr_text))
    requests.append(style_text_request(hdr_id, text_style(28, ACCENT_BLUE, bold=True), 0, len(hdr_text), hdr_text))

    arch_points = [
        "Domain-Driven Structure — Actions, Models, DTOs, Events per domain",
        "Thin Controllers — business logic in single-responsibility Actions",
        "State Machine — payroll runs: draft \u2192 submitted \u2192 under_review \u2192 finalized",
        "10-Step Computation Pipeline — gross-to-net with Philippine tax compliance",
        "HRIS API Sync — daily employee mirror from external HRIS system",
        "Currency Snapshots — exchange rates frozen at payroll run creation",
        "4-Role RBAC — Owner, Payroll Officer, Finance, Employee",
    ]
    body_text = "\n".join(f"\u2022  {p}" for p in arch_points)
    body_id = f"{slide_id}_body"
    requests.append(create_shape_request(slide_id, body_id, emu(0.8), emu(1.1), emu(8.4), emu(4.0)))
    requests.append(insert_text_request(body_id, body_text))
    requests.append(style_text_request(body_id, text_style(15, LIGHT_GRAY), 0, len(body_text), body_text))
    requests.append(
        {
            "updateParagraphStyle": {
                "objectId": body_id,
                "style": {"lineSpacing": 180},
                "textRange": {"type": "ALL"},
                "fields": "lineSpacing",
            }
        }
    )

    # ═══════════════════════════════════════
    # SLIDE 3 — EPICS OVERVIEW (summary grid)
    # ═══════════════════════════════════════
    slide_id = "slide_overview"
    add_slide(slide_id)

    hdr_id = f"{slide_id}_hdr"
    hdr_text = "Epics at a Glance"
    requests.append(create_shape_request(slide_id, hdr_id, emu(0.8), emu(0.25), emu(8.4), emu(0.5)))
    requests.append(insert_text_request(hdr_id, hdr_text))
    requests.append(style_text_request(hdr_id, text_style(28, ACCENT_BLUE, bold=True), 0, len(hdr_text), hdr_text))

    # Grid: 3 columns x 6 rows
    cols = 3
    for i, epic in enumerate(EPICS):
        col = i % cols
        row = i // cols
        x = emu(0.5 + col * 3.1)
        y = emu(0.85 + row * 0.7)
        box_id = f"{slide_id}_epic{i}"
        label = f"{epic['id']}  {epic['title']}  ({epic['tickets']})"
        requests.append(create_shape_request(slide_id, box_id, x, y, emu(2.95), emu(0.6)))
        requests.append(insert_text_request(box_id, label))
        # Style epic ID
        id_end = len(epic["id"])
        requests.append(style_text_request(box_id, text_style(10, epic["color"], bold=True), 0, id_end, label))
        # Style rest
        requests.append(style_text_request(box_id, text_style(10, LIGHT_GRAY), id_end, len(label), label))

    # ═══════════════════════════════════════
    # SLIDES 4-20 — Individual epic slides
    # ═══════════════════════════════════════
    for idx, epic in enumerate(EPICS):
        slide_id = f"slide_ep{idx:02d}"
        add_slide(slide_id)

        # Colored accent bar left
        bar_id = f"{slide_id}_lbar"
        requests.append(
            {
                "createShape": {
                    "objectId": bar_id,
                    "shapeType": "RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {"width": {"magnitude": emu(0.06), "unit": "EMU"}, "height": {"magnitude": SLIDE_H, "unit": "EMU"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": 0, "unit": "EMU"},
                    },
                }
            }
        )
        requests.append(
            {
                "updateShapeProperties": {
                    "objectId": bar_id,
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": epic["color"]}}},
                        "outline": {"propertyState": "NOT_RENDERED"},
                    },
                    "fields": "shapeBackgroundFill,outline",
                }
            }
        )

        # Epic ID badge
        badge_id = f"{slide_id}_badge"
        requests.append(create_shape_request(slide_id, badge_id, emu(0.8), emu(0.4), emu(1.2), emu(0.45)))
        requests.append(insert_text_request(badge_id, epic["id"]))
        requests.append(style_text_request(badge_id, text_style(14, epic["color"], bold=True), 0, len(epic["id"]), epic["id"]))

        # Ticket count
        count_id = f"{slide_id}_count"
        count_text = f"{epic['tickets']} ticket{'s' if epic['tickets'] != 1 else ''}"
        requests.append(create_shape_request(slide_id, count_id, emu(7.5), emu(0.4), emu(2.0), emu(0.45)))
        requests.append(insert_text_request(count_id, count_text))
        requests.append(style_text_request(count_id, text_style(12, MEDIUM_GRAY), 0, len(count_text), count_text))
        requests.append(para_style_request(count_id, "END", 0, len(count_text), count_text))

        # Title
        title_id = f"{slide_id}_title"
        requests.append(create_shape_request(slide_id, title_id, emu(0.8), emu(0.9), emu(8.4), emu(0.7)))
        requests.append(insert_text_request(title_id, epic["title"]))
        requests.append(style_text_request(title_id, text_style(28, WHITE, bold=True), 0, len(epic["title"]), epic["title"]))

        # Divider line
        line_id = f"{slide_id}_line"
        requests.append(
            {
                "createLine": {
                    "objectId": line_id,
                    "lineCategory": "STRAIGHT",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {"width": {"magnitude": emu(8.4), "unit": "EMU"}, "height": {"magnitude": 0, "unit": "EMU"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(0.8), "translateY": emu(1.7), "unit": "EMU"},
                    },
                }
            }
        )
        requests.append(
            {
                "updateLineProperties": {
                    "objectId": line_id,
                    "lineProperties": {
                        "lineFill": {"solidFill": {"color": {"rgbColor": epic["color"]}, "alpha": 0.4}},
                        "weight": pt(1),
                    },
                    "fields": "lineFill,weight",
                }
            }
        )

        # Bullet points
        bullet_text = "\n".join(f"\u2022  {b}" for b in epic["bullets"])
        bullet_id = f"{slide_id}_bullets"
        requests.append(create_shape_request(slide_id, bullet_id, emu(0.8), emu(1.95), emu(8.4), emu(3.2)))
        requests.append(insert_text_request(bullet_id, bullet_text))
        requests.append(style_text_request(bullet_id, text_style(16, LIGHT_GRAY), 0, len(bullet_text), bullet_text))
        requests.append(
            {
                "updateParagraphStyle": {
                    "objectId": bullet_id,
                    "style": {"lineSpacing": 200},
                    "textRange": {"type": "ALL"},
                    "fields": "lineSpacing",
                }
            }
        )

    # ═══════════════════════════════════════
    # SLIDE — PAYROLL COMPUTATION PIPELINE
    # ═══════════════════════════════════════
    slide_id = "slide_pipeline"
    add_slide(slide_id)

    hdr_id = f"{slide_id}_hdr"
    hdr_text = "10-Step Computation Pipeline"
    requests.append(create_shape_request(slide_id, hdr_id, emu(0.8), emu(0.25), emu(8.4), emu(0.55)))
    requests.append(insert_text_request(hdr_id, hdr_text))
    requests.append(style_text_request(hdr_id, text_style(24, ACCENT_BLUE, bold=True), 0, len(hdr_text), hdr_text))

    steps = [
        ("1", "Gross Pay", ACCENT_GREEN),
        ("2", "Add Bonuses", ACCENT_GREEN),
        ("3", "Absent Deduction", ACCENT_ORANGE),
        ("4", "SSS", ACCENT_ORANGE),
        ("5", "PhilHealth", ACCENT_ORANGE),
        ("6", "Pag-IBIG", ACCENT_ORANGE),
        ("7", "HMO", ACCENT_PURPLE),
        ("8", "Voluntary Deductions", ACCENT_PURPLE),
        ("9", "BIR Withholding Tax", ACCENT_RED),
        ("10", "Net Pay", ACCENT_BLUE),
    ]

    for i, (num, label, color) in enumerate(steps):
        col = i % 5
        row = i // 5
        x = emu(0.4 + col * 1.9)
        y = emu(1.0 + row * 2.0)
        box_id = f"{slide_id}_step{i}"

        # Step box background
        bg_id = f"{slide_id}_stepbg{i}"
        requests.append(
            {
                "createShape": {
                    "objectId": bg_id,
                    "shapeType": "ROUND_RECTANGLE",
                    "elementProperties": {
                        "pageObjectId": slide_id,
                        "size": {"width": {"magnitude": emu(1.7), "unit": "EMU"}, "height": {"magnitude": emu(1.5), "unit": "EMU"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "EMU"},
                    },
                }
            }
        )
        bg_color = {"red": color["red"] * 0.2 + DARK_BG["red"] * 0.8, "green": color["green"] * 0.2 + DARK_BG["green"] * 0.8, "blue": color["blue"] * 0.2 + DARK_BG["blue"] * 0.8}
        requests.append(
            {
                "updateShapeProperties": {
                    "objectId": bg_id,
                    "shapeProperties": {
                        "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": bg_color}}},
                        "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.3}}, "weight": pt(1)},
                    },
                    "fields": "shapeBackgroundFill,outline",
                }
            }
        )

        full = f"{num}\n{label}"
        requests.append(create_shape_request(slide_id, box_id, x + emu(0.1), y + emu(0.2), emu(1.5), emu(1.1)))
        requests.append(insert_text_request(box_id, full))
        requests.append(style_text_request(box_id, text_style(22, color, bold=True), 0, len(num), full))
        requests.append(style_text_request(box_id, text_style(11, LIGHT_GRAY), len(num) + 1, len(full), full))
        requests.append(para_style_request(box_id, "CENTER", 0, len(full), full))

    # ═══════════════════════════════════════
    # SLIDE — SUMMARY / THANK YOU
    # ═══════════════════════════════════════
    slide_id = "slide_end"
    add_slide(slide_id)

    bar_id = f"{slide_id}_bar"
    requests.append(
        {
            "createShape": {
                "objectId": bar_id,
                "shapeType": "RECTANGLE",
                "elementProperties": {
                    "pageObjectId": slide_id,
                    "size": {"width": {"magnitude": SLIDE_W, "unit": "EMU"}, "height": {"magnitude": emu(0.06), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": 0, "translateY": SLIDE_H - emu(0.06), "unit": "EMU"},
                },
            }
        }
    )
    requests.append(
        {
            "updateShapeProperties": {
                "objectId": bar_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": ACCENT_BLUE}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        }
    )

    title_id = f"{slide_id}_title"
    title_text = "Thank You"
    requests.append(create_shape_request(slide_id, title_id, emu(0.8), emu(1.6), emu(8.4), emu(1.0)))
    requests.append(insert_text_request(title_id, title_text))
    requests.append(style_text_request(title_id, text_style(44, WHITE, bold=True), 0, len(title_text), title_text))
    requests.append(para_style_request(title_id, "CENTER", 0, len(title_text), title_text))

    summary_id = f"{slide_id}_summary"
    summary_text = "17 Epics  \u2022  88 Tickets  \u2022  Ready for Implementation"
    requests.append(create_shape_request(slide_id, summary_id, emu(0.8), emu(2.6), emu(8.4), emu(0.5)))
    requests.append(insert_text_request(summary_id, summary_text))
    requests.append(style_text_request(summary_id, text_style(16, MEDIUM_GRAY), 0, len(summary_text), summary_text))
    requests.append(para_style_request(summary_id, "CENTER", 0, len(summary_text), summary_text))

    return requests


def main():
    creds = auth()
    slides_service = build("slides", "v1", credentials=creds)

    # Create presentation
    presentation = slides_service.presentations().create(body={"title": "PayHRIS Payroll — Epics Overview"}).execute()
    presentation_id = presentation["presentationId"]
    print(f"Created presentation: {presentation_id}")

    # Delete the default blank slide
    default_slides = presentation.get("slides", [])
    delete_requests = [{"deleteObject": {"objectId": s["objectId"]}} for s in default_slides]

    # Build all slide requests
    all_requests = delete_requests + build_requests(presentation_id)

    # Execute batch update
    slides_service.presentations().batchUpdate(
        presentationId=presentation_id, body={"requests": all_requests}
    ).execute()

    url = f"https://docs.google.com/presentation/d/{presentation_id}/edit"
    print(f"\nPresentation created successfully!")
    print(f"URL: {url}")


if __name__ == "__main__":
    main()
