#!/usr/bin/env python3
"""Debug: read presentation and show slide count + content."""
import os, json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TOKEN_FILE = os.path.join(SCRIPT_DIR, "token.json")
SCOPES = ["https://www.googleapis.com/auth/presentations", "https://www.googleapis.com/auth/drive.file"]

creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
service = build("slides", "v1", credentials=creds)

pres_id = "1QESDUSwoXH-qWdYkmIadTuFnuaqMUu9wiBOIW2UVu54"
pres = service.presentations().get(presentationId=pres_id).execute()

slides = pres.get("slides", [])
print(f"Total slides: {len(slides)}")
for i, slide in enumerate(slides):
    elements = slide.get("pageElements", [])
    texts = []
    for el in elements:
        shape = el.get("shape", {})
        tf = shape.get("text", {})
        for te in tf.get("textElements", []):
            tr = te.get("textRun", {})
            if tr.get("content", "").strip():
                texts.append(tr["content"].strip())
    preview = " | ".join(texts[:3]) if texts else "(empty)"
    print(f"  Slide {i}: {len(elements)} elements — {preview}")
