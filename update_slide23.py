#!/usr/bin/env python3
"""Redesign slide 23 (10-Step Computation Pipeline) with an appealing flowing pipeline layout."""
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
DARK_GRAY = {"red": 0.25, "green": 0.25, "blue": 0.28}
ACCENT_GREEN = {"red": 0.18, "green": 0.74, "blue": 0.49}
ACCENT_ORANGE = {"red": 0.96, "green": 0.62, "blue": 0.14}
ACCENT_PURPLE = {"red": 0.56, "green": 0.34, "blue": 0.87}
ACCENT_RED = {"red": 0.91, "green": 0.30, "blue": 0.24}
ACCENT_TEAL = {"red": 0.14, "green": 0.70, "blue": 0.76}
ACCENT_CYAN = {"red": 0.20, "green": 0.78, "blue": 0.89}

SLIDE_ID = "slide_pipeline"

def emu(inches):
    return int(inches * 914400)

def pt(points):
    return {"magnitude": points, "unit": "PT"}

def mix_color(c1, c2, ratio):
    """Mix two colors. ratio=0 gives c1, ratio=1 gives c2."""
    return {
        "red": c1["red"] * (1 - ratio) + c2["red"] * ratio,
        "green": c1["green"] * (1 - ratio) + c2["green"] * ratio,
        "blue": c1["blue"] * (1 - ratio) + c2["blue"] * ratio,
    }

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


def get_existing_elements(service):
    """Get all element IDs on slide 23 to delete them."""
    pres = service.presentations().get(presentationId=PRES_ID).execute()
    for slide in pres.get("slides", []):
        if slide["objectId"] == SLIDE_ID:
            return [el["objectId"] for el in slide.get("pageElements", [])]
    return []


def build_requests(existing_element_ids):
    requests = []
    obj_counter = [0]

    def make_id(prefix):
        obj_counter[0] += 1
        return f"pipe_{prefix}_{obj_counter[0]}"

    # Step 1: Delete all existing elements on this slide
    for eid in existing_element_ids:
        requests.append({"deleteObject": {"objectId": eid}})

    # ── HEADER ──
    hdr_id = make_id("hdr")
    hdr_text = "Gross-to-Net Pipeline"
    requests.append(_shape(hdr_id, emu(0.6), emu(0.15), emu(6.5), emu(0.5)))
    requests.append(_text(hdr_id, hdr_text))
    requests.append(_style(hdr_id, 26, WHITE, True, 0, len(hdr_text)))

    # Subtitle
    sub_id = make_id("sub")
    sub_text = "10-step computation per employee payslip"
    requests.append(_shape(sub_id, emu(0.6), emu(0.55), emu(6.5), emu(0.3)))
    requests.append(_text(sub_id, sub_text))
    requests.append(_style(sub_id, 12, MEDIUM_GRAY, False, 0, len(sub_text)))

    # ── Accent line under header ──
    hline_id = make_id("hline")
    requests.append({
        "createLine": {
            "objectId": hline_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": emu(8.8), "unit": "EMU"}, "height": {"magnitude": 0, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": emu(0.6), "translateY": emu(0.9), "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": hline_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_BLUE}, "alpha": 0.4}},
                "weight": pt(1.5),
            },
            "fields": "lineFill,weight",
        }
    })

    # ── PIPELINE STEPS ──
    # Layout: Two columns, left column (steps 1-5), right column (steps 6-10)
    # Each step is a card with a colored circle number, label, and description

    steps = [
        ("1", "Gross Pay", "Monthly salary or\ndaily rate × working days", ACCENT_GREEN),
        ("2", "Add Bonuses", "Fixed, percentage, or\nformula-based bonuses", ACCENT_GREEN),
        ("3", "Absent Deduction", "Daily rate × absent days\nsubtracted from gross", ACCENT_ORANGE),
        ("4", "SSS", "Bracket-based lookup\nfrom contribution table", ACCENT_ORANGE),
        ("5", "PhilHealth", "2.5% employee share\nwith salary floor/ceiling", ACCENT_ORANGE),
        ("6", "Pag-IBIG", "Fixed ₱100 monthly\nemployee contribution", ACCENT_TEAL),
        ("7", "HMO", "Fixed amount per\nemployee plan", ACCENT_PURPLE),
        ("8", "Voluntary", "MP2, SSS WISP,\ncash advance recovery", ACCENT_PURPLE),
        ("9", "BIR Tax", "TRAIN Law brackets\nannualized computation", ACCENT_RED),
        ("10", "Net Pay", "Gross + bonuses\nminus all deductions", ACCENT_BLUE),
    ]

    # Section labels
    sections = [
        ("EARNINGS", ACCENT_GREEN, 0),       # steps 1-2
        ("DEDUCTIONS", ACCENT_ORANGE, 2),     # steps 3-8
        ("TAX & RESULT", ACCENT_RED, 8),      # steps 9-10
    ]

    left_x = emu(0.6)
    right_x = emu(5.1)
    card_w = emu(4.2)
    card_h = emu(0.7)
    y_start = 1.0
    y_gap = 0.82

    for i, (num, label, desc, color) in enumerate(steps):
        col = 0 if i < 5 else 1
        row = i if i < 5 else i - 5
        x = left_x if col == 0 else right_x
        y = emu(y_start + row * y_gap)

        # Card background
        card_bg_id = make_id(f"cardbg{i}")
        bg_color = mix_color(DARK_BG, color, 0.08)
        requests.append({
            "createShape": {
                "objectId": card_bg_id,
                "shapeType": "ROUND_RECTANGLE",
                "elementProperties": {
                    "pageObjectId": SLIDE_ID,
                    "size": {"width": {"magnitude": card_w, "unit": "EMU"}, "height": {"magnitude": card_h, "unit": "EMU"}},
                    "transform": {"scaleX": 1, "scaleY": 1, "translateX": x, "translateY": y, "unit": "EMU"},
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": card_bg_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": bg_color}}},
                    "outline": {"outlineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.25}}, "weight": pt(1)},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

        # Number circle
        circle_id = make_id(f"circle{i}")
        circle_size = emu(0.42)
        requests.append({
            "createShape": {
                "objectId": circle_id,
                "shapeType": "ELLIPSE",
                "elementProperties": {
                    "pageObjectId": SLIDE_ID,
                    "size": {"width": {"magnitude": circle_size, "unit": "EMU"}, "height": {"magnitude": circle_size, "unit": "EMU"}},
                    "transform": {
                        "scaleX": 1, "scaleY": 1,
                        "translateX": x + emu(0.12),
                        "translateY": y + (card_h - circle_size) // 2,
                        "unit": "EMU",
                    },
                },
            }
        })
        requests.append({
            "updateShapeProperties": {
                "objectId": circle_id,
                "shapeProperties": {
                    "shapeBackgroundFill": {"solidFill": {"color": {"rgbColor": color}}},
                    "outline": {"propertyState": "NOT_RENDERED"},
                },
                "fields": "shapeBackgroundFill,outline",
            }
        })

        # Number text inside circle
        num_id = make_id(f"num{i}")
        requests.append(_shape(num_id, x + emu(0.12), y + (card_h - circle_size) // 2, circle_size, circle_size))
        requests.append(_text(num_id, num))
        requests.append(_style(num_id, 16, WHITE, True, 0, len(num)))
        requests.append(_align(num_id, "CENTER", 0, len(num)))
        # Vertical center the text in the circle
        requests.append({
            "updateShapeProperties": {
                "objectId": num_id,
                "shapeProperties": {
                    "contentAlignment": "MIDDLE",
                },
                "fields": "contentAlignment",
            }
        })

        # Step label (bold)
        lbl_id = make_id(f"lbl{i}")
        requests.append(_shape(lbl_id, x + emu(0.65), y + emu(0.06), emu(1.8), emu(0.3)))
        requests.append(_text(lbl_id, label))
        requests.append(_style(lbl_id, 14, WHITE, True, 0, len(label)))

        # Step description
        desc_id = make_id(f"desc{i}")
        requests.append(_shape(desc_id, x + emu(0.65), y + emu(0.32), emu(3.3), emu(0.38)))
        requests.append(_text(desc_id, desc.replace("\n", " ")))
        desc_flat = desc.replace("\n", " ")
        requests.append(_style(desc_id, 10, MEDIUM_GRAY, False, 0, len(desc_flat)))

        # Downward arrow between steps (except last in each column)
        if (col == 0 and row < 4) or (col == 1 and row < 4):
            arrow_id = make_id(f"arrow{i}")
            arrow_x = x + card_w // 2
            arrow_y_start = y + card_h
            arrow_len = emu(y_gap) - card_h
            requests.append({
                "createLine": {
                    "objectId": arrow_id,
                    "lineCategory": "STRAIGHT",
                    "elementProperties": {
                        "pageObjectId": SLIDE_ID,
                        "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": arrow_len, "unit": "EMU"}},
                        "transform": {"scaleX": 1, "scaleY": 1, "translateX": arrow_x, "translateY": arrow_y_start, "unit": "EMU"},
                    },
                }
            })
            requests.append({
                "updateLineProperties": {
                    "objectId": arrow_id,
                    "lineProperties": {
                        "lineFill": {"solidFill": {"color": {"rgbColor": color}, "alpha": 0.35}},
                        "weight": pt(1.5),
                        "endArrow": "OPEN_ARROW",
                    },
                    "fields": "lineFill,weight,endArrow",
                }
            })

    # ── Connector from col1 bottom to col2 top ──
    # Connect step 5 (bottom of left col) to step 6 (top of right col)
    # Since step 6 is ABOVE step 5, we draw from step 6 top down to step 5 bottom
    # and flip the arrow to point at step 6
    step5_y_bottom = emu(y_start + 4 * y_gap) + card_h
    step6_y_top = emu(y_start)
    conn_start_x = right_x + card_w // 2  # start at step 6 (top-right)
    conn_end_x = left_x + card_w // 2     # end at step 5 (bottom-left)

    conn_h_id = make_id("connh")
    line_height = step5_y_bottom - step6_y_top
    line_width = conn_start_x - conn_end_x
    requests.append({
        "createLine": {
            "objectId": conn_h_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {
                    "width": {"magnitude": line_width, "unit": "EMU"},
                    "height": {"magnitude": line_height, "unit": "EMU"},
                },
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": conn_end_x, "translateY": step6_y_top, "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": conn_h_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_TEAL}, "alpha": 0.4}},
                "weight": pt(1.5),
                "startArrow": "OPEN_ARROW",
                "dashStyle": "DASH",
            },
            "fields": "lineFill,weight,startArrow,dashStyle",
        }
    })

    # ── SECTION LABELS on the right side ──
    # Earnings label
    earn_id = make_id("sec_earn")
    earn_text = "EARNINGS"
    requests.append(_shape(earn_id, left_x + card_w + emu(0.08), emu(y_start + 0.15), emu(0.45), emu(1.2)))
    requests.append(_text(earn_id, earn_text))
    requests.append(_style(earn_id, 8, ACCENT_GREEN, True, 0, len(earn_text)))
    # Rotate text 90 degrees... not supported easily via API, so use vertical bracket instead

    # Section bracket lines
    # Earnings bracket (steps 1-2)
    brk1_id = make_id("brk1")
    brk1_y = emu(y_start + 0.1)
    brk1_h = emu(y_gap * 1 + 0.5)
    requests.append({
        "createLine": {
            "objectId": brk1_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": brk1_h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": left_x + card_w + emu(0.12), "translateY": brk1_y, "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": brk1_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_GREEN}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    # Deductions bracket (steps 3-5 left, 6-8 right)
    brk2_id = make_id("brk2")
    brk2_y = emu(y_start + 2 * y_gap + 0.1)
    brk2_h = emu(y_gap * 2 + 0.5)
    requests.append({
        "createLine": {
            "objectId": brk2_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": brk2_h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": left_x + card_w + emu(0.12), "translateY": brk2_y, "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": brk2_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_ORANGE}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    # Section labels next to brackets
    earn_lbl_id = make_id("earnlbl")
    requests.append(_shape(earn_lbl_id, left_x + card_w + emu(0.2), emu(y_start + 0.4 * y_gap), emu(0.7), emu(0.25)))
    requests.append(_text(earn_lbl_id, "EARN"))
    requests.append(_style(earn_lbl_id, 8, ACCENT_GREEN, True, 0, 4))

    ded_lbl_id = make_id("dedlbl")
    requests.append(_shape(ded_lbl_id, left_x + card_w + emu(0.2), emu(y_start + 3 * y_gap), emu(0.7), emu(0.25)))
    requests.append(_text(ded_lbl_id, "DEDUCT"))
    requests.append(_style(ded_lbl_id, 8, ACCENT_ORANGE, True, 0, 6))

    # Right side labels
    brk3_id = make_id("brk3")
    brk3_y = emu(y_start + 0.1)
    brk3_h = emu(y_gap * 2 + 0.5)
    requests.append({
        "createLine": {
            "objectId": brk3_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": brk3_h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": right_x + card_w + emu(0.12), "translateY": brk3_y, "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": brk3_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_TEAL}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    ded2_lbl_id = make_id("ded2lbl")
    requests.append(_shape(ded2_lbl_id, right_x + card_w + emu(0.2), emu(y_start + 0.8 * y_gap), emu(0.7), emu(0.25)))
    requests.append(_text(ded2_lbl_id, "DEDUCT"))
    requests.append(_style(ded2_lbl_id, 8, ACCENT_TEAL, True, 0, 6))

    # Tax/Result bracket (steps 9-10 right col)
    brk4_id = make_id("brk4")
    brk4_y = emu(y_start + 3 * y_gap + 0.1)
    brk4_h = emu(y_gap * 1 + 0.5)
    requests.append({
        "createLine": {
            "objectId": brk4_id,
            "lineCategory": "STRAIGHT",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
                "size": {"width": {"magnitude": 0, "unit": "EMU"}, "height": {"magnitude": brk4_h, "unit": "EMU"}},
                "transform": {"scaleX": 1, "scaleY": 1, "translateX": right_x + card_w + emu(0.12), "translateY": brk4_y, "unit": "EMU"},
            },
        }
    })
    requests.append({
        "updateLineProperties": {
            "objectId": brk4_id,
            "lineProperties": {
                "lineFill": {"solidFill": {"color": {"rgbColor": ACCENT_RED}, "alpha": 0.3}},
                "weight": pt(2),
            },
            "fields": "lineFill,weight",
        }
    })

    tax_lbl_id = make_id("taxlbl")
    requests.append(_shape(tax_lbl_id, right_x + card_w + emu(0.2), emu(y_start + 3.5 * y_gap), emu(0.7), emu(0.25)))
    requests.append(_text(tax_lbl_id, "TAX"))
    requests.append(_style(tax_lbl_id, 8, ACCENT_RED, True, 0, 3))

    # ── Footer note ──
    note_id = make_id("note")
    note_text = "Steps 4-6 & 9 use Step 1 gross pay as basis  •  External salary employees skip steps 3-9"
    requests.append(_shape(note_id, emu(0.6), emu(5.2), emu(8.8), emu(0.25)))
    requests.append(_text(note_id, note_text))
    requests.append(_style(note_id, 9, MEDIUM_GRAY, False, 0, len(note_text)))
    requests.append(_align(note_id, "CENTER", 0, len(note_text)))

    return requests


# ─── Helper functions ───

def _shape(shape_id, x, y, w, h):
    return {
        "createShape": {
            "objectId": shape_id,
            "shapeType": "TEXT_BOX",
            "elementProperties": {
                "pageObjectId": SLIDE_ID,
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

    # Get existing elements to delete
    existing = get_existing_elements(service)
    print(f"Found {len(existing)} existing elements to replace")

    reqs = build_requests(existing)
    print(f"Sending {len(reqs)} API requests...")

    service.presentations().batchUpdate(
        presentationId=PRES_ID, body={"requests": reqs}
    ).execute()

    print("Slide 23 redesigned successfully!")
    print(f"URL: https://docs.google.com/presentation/d/{PRES_ID}/edit#slide=id.slide_pipeline")


if __name__ == "__main__":
    main()
