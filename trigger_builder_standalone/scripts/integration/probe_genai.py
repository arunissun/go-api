"""Billable Vertex/Gemini probe. Run explicitly; never part of the normal test suite."""

import os

import google.auth
from google import genai
from google.genai import types


PROJECT = os.environ.get("GCP_PROJECT_ID", "eap-form-prototype")
LOCATION = os.environ.get("GCP_LOCATION", "global")
MODEL = os.environ.get("GEMINI_MODEL_ID", "gemini-3.5-flash")

credentials, _ = google.auth.default(
    scopes=["https://www.googleapis.com/auth/cloud-platform"]
)
client = genai.Client(
    vertexai=True,
    credentials=credentials,
    project=PROJECT,
    location=LOCATION,
)
response = client.models.generate_content(
    model=MODEL,
    contents='Reply with exactly this JSON: {"ok": true}',
    config=types.GenerateContentConfig(response_mime_type="application/json"),
)
print(response.text)
