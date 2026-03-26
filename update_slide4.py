#!/usr/bin/env python3
"""Update slide 4 (Epics at a Glance) to a timeline-based layout across 2 slides."""
import os
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/presentations", "https://www.googleapis.com/auth/drive.file"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")

PRES_ID = "1QESDUSwoXH-qWdYkmIadTuFnuaqMUu9wiBOIW2UVu54"

# Colors
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

PHASE_COLORS = [ACCENT_BLUE, ACCENT_GREEN, ACCENT_ORANGE, ACCENT_PURPLE, ACCENT_RED, ACCENT_TEAL]

SLIDE_W = 9144000
SLIDE_H = 5143500

def emu(inches):
    return int(inches * 914400)

def pt(points):
    return {"magnitude": points, "unit": "PT"}

EPICS = [
    ("EP-01", "Project Setup & Infrastructure", 6),
    ("EP-02", "Auth & User Management", 5),
    ("EP-03", "Database Schema & Models", 15),
    ("EP-04", "UI Foundation", 3),
    ("EP-05", "Employee Management & HRIS Sync", 6),
    ("EP-06", "Currency Management", 7),
    ("EP-07", "Payroll Run Lifecycle", 11),
    ("EP-08", "Computation Engine", 9),
    ("EP-09", "Bonus Management", 4),
    ("EP-10", "Cash Advance Management", 2),
    ("EP-11", "Finance Review & Finalization", 4),
    ("EP-12", "Payslip Generation & Viewing", 5),
    ("EP-13", "Reporting & Export", 3),
    ("EP-14", "Audit Trail", 3),
    ("EP-15", "Notifications", 2),
    ("EP-16", "Edge Cases & Business Rules", 2),
    ("EP-17", "Dashboard", 1),
]

# Group into phases for the timeline
PHASES = [
    ("Foundation", [0, 1, 2, 3]),        # EP-01 to EP-04
    ("Core Features", [4, 5, 6, 7]),     # EP-05 to EP-08
    ("Extensions", [8, 9, 10, 11]),      # EP-09 to EP-12
    ("Polish & Launch", [12, 13, 14, 15, 16]),  # EP-13 to EP-17
]


def auth():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                os.path.join(SCRIPT_DIR, "credentials.json"), SCOPES
            )
            creds = flow.run_local_server(port=0)
        with open(TOKEN_FILE, "w") as f:
            f.write(creds.to_json())
    return creds


def build_timeline_requests():
    requests = []

    # Step 1: Delete the old slide_overview
    requests.append({"deleteObject": {"objectId": "slide_overview"}})

    # Step 2: Create two new timeline slides inserted at index 3
    slide1_id = "slide_timeline1"
    slide2_id = "slide_timeline2"

    # Create slide 2 first (it will be at index 3), then slide 1 (pushes slide 2 to index 4)
    for sid in [slide2_id, slide1_id]:
        requests.append({
            "createSlide": {
                "objectId": sid,
                "insertionIndex": 3,
                "slideLayoutReference": {"predefinedLayout": "BLANK"},
            }
        })
        requests.append({
            "updatePageProperties": {
                "objectId": sid,
                "pageProperties": {
                    "pageBackgroundFill": {
                        "solidFill": {"color": {"rgbColor": DARK_BG}}
                    }
                },
                "fields": "pageBackgroundFill.solidFill.color",
            }
        })

    # ═══════════════════════════════════════════
    # SLIDE 1: Timeline — Foundation & Core Features (EP-01 to EP-08)
    # ═══════════════════════════════════════════
    sid = slide1_id
    obj_idx = 0

    def make_id(prefix):
        nonlocal obj_idx
        obj_idx += 1
        return f"tl1_{prefix}_{obj_idx}"

    # Header
    hdr_id = make_id("hdr")
    hdr_text = "Project Timeline"
    requests.append(_shape(sid, hdr_id, emu(0.5), emu(0.2), emu(7.0), emu(0.5)))
    requests.append(_text(hdr_id, hdr_text))
    requests.append(_style(hdr_id, 28, ACCENT_BLUE, True, 0, len(hdr_text)))

    # Subtitle
    sub_id = make_id("sub")
    sub_text = "Part 1 of 2 — Foundation & Core Features"
    requests.append(_shape(sid, sub_id, emu(0.5), emu(0.65), emu(7.0), emu(0.35)))
    requests.append(_text(sub_id, sub_text))
    requests.append(_style(sub_id, 13, MEDIUM_GRAY, False, 0, len(sub_text)))

    # Vertical timeline line
    line_id = make_id("vline")
    requests.append({
        "createLine": {
            "objectId": line_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": sid,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": emu(4.1), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3), "translateY": emu(1.05), "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": line_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": MEDIUM_GRAY}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    # Timeline entries for first 8 epics (EP-01 to EP-08)
    first_half = EPICS[:9]
    y_start = 1.05
    y_spacing = 0.5
    for i, (ep_id, ep_title, tickets) in enumerate(first_half):
        color = PHASE_COLORS[i % len(PHASE_COLORS)]
        y = emu(y_start + i * y_spacing)

        # Dot/circle on timeline
        dot_id = make_id(f"dot{i}")
        dot_size = emu(0.18)
        requests.append({
            "createShape": {
                "objectId": dot_id,
                "shapeType": "ELLIPSE",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": dot_size, "unit": "EMU"}, "height": {"magnitude": dot_size, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3) - dot_size // 2, "translateY": y - dot_size // 2 + emu(0.08), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": dot_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

        # Horizontal connector line from dot to content
        conn_id = make_id(f"conn{i}")
        requests.append({
            "createLine": {
                "objectId": conn_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": emu(0.4), "unit": "EMU"}, "height": {"magnitude": 0, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3) + dot_size // 2, "translateY": y + emu(0.08), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateLineProperties": {
                "objectId": conn_id,
                "lineProperties": {
                    "lineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.5}},
                    "weight": pt(1),
                },
                "fields": "lineFill,weight",
            }
        })

        # Epic ID label
        eid_id = make_id(f"eid{i}")
        requests.append(_shape(sid, eid_id, emu(1.85), y - emu(0.05), emu(0.75), emu(0.35)))
        requests.append(_text(eid_id, ep_id))
        requests.append(_style(eid_id, 13, color, True, 0, len(ep_id)))

        # Epic title
        title_id = make_id(f"etitle{i}")
        requests.append(_shape(sid, title_id, emu(2.65), y - emu(0.05), emu(5.0), emu(0.35)))
        requests.append(_text(title_id, ep_title))
        requests.append(_style(title_id, 14, WHITE, False, 0, len(ep_title)))

        # Ticket count badge
        badge_id = make_id(f"badge{i}")
        badge_text = f"{tickets}"
        requests.append(_shape(sid, badge_id, emu(8.2), y - emu(0.03), emu(0.6), emu(0.3)))
        requests.append(_text(badge_id, badge_text))
        requests.append(_style(badge_id, 12, color, True, 0, len(badge_text)))
        requests.append(_align(badge_id, "CENTER", 0, len(badge_text)))

        # Badge background
        bbg_id = make_id(f"bbg{i}")
        bg_color = {
            "red": color["red"] * 0.2 + DARK_BG["red"] * 0.8,
            "green": color["green"] * 0.2 + DARK_BG["green"] * 0.8,
            "blue": color["blue"] * 0.2 + DARK_BG["blue"] * 0.8,
        }
        requests.append({
            "createShape": {
                "objectId": bbg_id,
                "shapeType": "ROUND_RECTANGLE",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": emu(0.45), "unit": "EMU"}, "height": {"magnitude": emu(0.28), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(8.25), "translateY": y - emu(0.01), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": bbg_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": bg_color}}},
                    "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.3}}, "weight": pt(1)},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

    # Phase labels on the right
    phase1_id = make_id("phase1")
    requests.append(_shape(sid, phase1_id, emu(8.9), emu(1.5), emu(1.0), emu(0.8)))
    p1text = "Phase 1\nFoundation"
    requests.append(_text(phase1_id, p1text))
    requests.append(_style(phase1_id, 9, ACCENT_BLUE, True, 0, 7))
    requests.append(_style(phase1_id, 9, MEDIUM_GRAY, False, 8, len(p1text)))
    requests.append(_align(phase1_id, "END", 0, len(p1text)))

    phase2_id = make_id("phase2")
    requests.append(_shape(sid, phase2_id, emu(8.9), emu(3.3), emu(1.0), emu(0.8)))
    p2text = "Phase 2\nCore"
    requests.append(_text(phase2_id, p2text))
    requests.append(_style(phase2_id, 9, ACCENT_GREEN, True, 0, 7))
    requests.append(_style(phase2_id, 9, MEDIUM_GRAY, False, 8, len(p2text)))
    requests.append(_align(phase2_id, "END", 0, len(p2text)))

    # ═══════════════════════════════════════════
    # SLIDE 2: Timeline — Extensions & Polish (EP-10 to EP-17)
    # ═══════════════════════════════════════════
    sid = slide2_id
    obj_idx = 0

    def make_id2(prefix):
        nonlocal obj_idx
        obj_idx += 1
        return f"tl2_{prefix}_{obj_idx}"

    # Header
    hdr_id = make_id2("hdr")
    hdr_text = "Project Timeline"
    requests.append(_shape(sid, hdr_id, emu(0.5), emu(0.2), emu(7.0), emu(0.5)))
    requests.append(_text(hdr_id, hdr_text))
    requests.append(_style(hdr_id, 28, ACCENT_BLUE, True, 0, len(hdr_text)))

    sub_id = make_id2("sub")
    sub_text = "Part 2 of 2 — Extensions & Polish"
    requests.append(_shape(sid, sub_id, emu(0.5), emu(0.65), emu(7.0), emu(0.35)))
    requests.append(_text(sub_id, sub_text))
    requests.append(_style(sub_id, 13, MEDIUM_GRAY, False, 0, len(sub_text)))

    # Vertical timeline line
    line_id = make_id2("vline")
    requests.append({
        "createLine": {
            "objectId": line_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": sid,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": emu(3.6), "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3), "translateY": emu(1.05), "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": line_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": MEDIUM_GRAY}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    second_half = EPICS[9:]
    y_spacing = 0.5
    for i, (ep_id, ep_title, tickets) in enumerate(second_half):
        color = PHASE_COLORS[(i + 3) % len(PHASE_COLORS)]
        y = emu(y_start + i * y_spacing)

        dot_id = make_id2(f"dot{i}")
        dot_size = emu(0.18)
        requests.append({
            "createShape": {
                "objectId": dot_id,
                "shapeType": "ELLIPSE",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": dot_size, "unit": "EMU"}, "height": {"magnitude": dot_size, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3) - dot_size // 2, "translateY": y - dot_size // 2 + emu(0.08), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": dot_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

        conn_id = make_id2(f"conn{i}")
        requests.append({
            "createLine": {
                "objectId": conn_id,
                "lineCategory": "STRAIGHT",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": emu(0.4), "unit": "EMU"}, "height": {"magnitude": 0, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(1.3) + dot_size // 2, "translateY": y + emu(0.08), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateLineProperties": {
                "objectId": conn_id,
                "lineProperties": {
                    "lineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.5}},
                    "weight": pt(1),
                },
                "fields": "lineFill,weight",
            }
        })

        eid_id = make_id2(f"eid{i}")
        requests.append(_shape(sid, eid_id, emu(1.85), y - emu(0.05), emu(0.75), emu(0.35)))
        requests.append(_text(eid_id, ep_id))
        requests.append(_style(eid_id, 13, color, True, 0, len(ep_id)))

        title_id = make_id2(f"etitle{i}")
        requests.append(_shape(sid, title_id, emu(2.65), y - emu(0.05), emu(5.0), emu(0.35)))
        requests.append(_text(title_id, ep_title))
        requests.append(_style(title_id, 14, WHITE, False, 0, len(ep_title)))

        badge_id = make_id2(f"badge{i}")
        badge_text = f"{tickets}"
        requests.append(_shape(sid, badge_id, emu(8.2), y - emu(0.03), emu(0.6), emu(0.3)))
        requests.append(_text(badge_id, badge_text))
        requests.append(_style(badge_id, 12, color, True, 0, len(badge_text)))
        requests.append(_align(badge_id, "CENTER", 0, len(badge_text)))

        bbg_id = make_id2(f"bbg{i}")
        bg_color = {
            "red": color["red"] * 0.2 + DARK_BG["red"] * 0.8,
            "green": color["green"] * 0.2 + DARK_BG["green"] * 0.8,
            "blue": color["blue"] * 0.2 + DARK_BG["blue"] * 0.8,
        }
        requests.append({
            "createShape": {
                "objectId": bbg_id,
                "shapeType": "ROUND_RECTANGLE",
                "elementProperties": {
                    "pageObjectId": sid,
                    "size": {"width": {"magnitude": emu(0.45), "unit": "EMU"}, "height": {"magnitude": emu(0.28), "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(8.25), "translateY": y - emu(0.01), "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": bbg_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": bg_color}}},
                    "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.3}}, "weight": pt(1)},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

    # Phase labels
    phase3_id = make_id2("phase3")
    requests.append(_shape(sid, phase3_id, emu(8.9), emu(1.5), emu(1.0), emu(0.8)))
    p3text = "Phase 3\nExtensions"
    requests.append(_text(phase3_id, p3text))
    requests.append(_style(phase3_id, 9, ACCENT_ORANGE, True, 0, 7))
    requests.append(_style(phase3_id, 9, MEDIUM_GRAY, False, 8, len(p3text)))
    requests.append(_align(phase3_id, "END", 0, len(p3text)))

    phase4_id = make_id2("phase4")
    requests.append(_shape(sid, phase4_id, emu(8.9), emu(3.0), emu(1.0), emu(0.8)))
    p4text = "Phase 4\nPolish"
    requests.append(_text(phase4_id, p4text))
    requests.append(_style(phase4_id, 9, ACCENT_PURPLE, True, 0, 7))
    requests.append(_style(phase4_id, 9, MEDIUM_GRAY, False, 8, len(p4text)))
    requests.append(_align(phase4_id, "END", 0, len(p4text)))

    # Total summary at bottom of slide 2
    total_id = make_id2("total")
    total_text = "Total: 88 Tickets across 17 Epics"
    requests.append(_shape(sid, total_id, emu(1.85), emu(5.0), emu(6.0), emu(0.35)))
    requests.append(_text(total_id, total_text))
    requests.append(_style(total_id, 12, MEDIUM_GRAY, True, 0, len(total_text)))

    return requests


# ─── Helper functions ───

def _shape(page_id, shape_id, x, y, w, h):
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
                    "scaleX": 1, "scaleY": 1,
                    "translateX": x, "translateY": y,
                    "unit": "EMU",
                },
            },
        }
    }

def _text(shape_id, text):
    return {"insertText": {"objectId": shape_id, "text": text, "insertionIndex": 0}}

def _style(shape_id, font_size, color, bold, start, end):
    return {
        "updateTextStyle": {
            "objectId": shape_id,
            "style": {
                "fontSize": pt(font_size),
                "foregroundColor": {"opaqueColor": {"rgbColor": color}},
                "bold": bold,
                "fontFamily": "Inter",
            },
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            "fields": "fontSize,foregroundColor,bold,fontFamily",
        }
    }

def _align(shape_id, alignment, start, end):
    return {
        "updateParagraphStyle": {
            "objectId": shape_id,
            "style": {"alignment": alignment},
            "textRange": {"type": "FIXED_RANGE", "startIndex": start, "endIndex": end},
            "fields": "alignment",
        }
    }


def main():
    creds = auth()
    service = build("slides", "v1", credentials=creds)

    reqs = build_timeline_requests()
    service.presentations().batchUpdate(
        presentationId=PRES_ID, body={"requests": reqs}
    ).execute()

    print("Slide 4 updated to timeline layout (now split across 2 slides).")
    print(f"URL: https://docs.google.com/presentation/d/{PRES_ID}/edit")


if __name__ == "__main__":
    main()
