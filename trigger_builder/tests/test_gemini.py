import json
from types import SimpleNamespace
from unittest.mock import patch

from django.test import SimpleTestCase

from trigger_builder.services import gemini


class FakeModels:
    def __init__(self, text):
        self.text = text

    def generate_content(self, **_kwargs):
        return SimpleNamespace(text=self.text)


class GeminiParsingTests(SimpleTestCase):
    valid_response = {
        "preActivation": "Pre-activation statement",
        "activation": "Activation statement",
        "stop": "Stop statement",
        "combined": "Combined statement",
        "warnings": [],
    }

    def test_json_with_trailing_model_commentary_is_accepted(self):
        response_text = f"{json.dumps(self.valid_response)}\nI hope this helps."
        fake_client = SimpleNamespace(models=FakeModels(response_text))
        with patch("trigger_builder.services.gemini._get_client", return_value=fake_client):
            result = gemini.call_gemini({}, {"countryName": "Pakistan"})
        self.assertEqual(result, self.valid_response)

    def test_fenced_json_with_surrounding_text_is_accepted(self):
        response_text = (
            "Generated output:\n```json\n"
            f"{json.dumps(self.valid_response)}\n"
            "```\nReview the trigger facts before approval."
        )
        fake_client = SimpleNamespace(models=FakeModels(response_text))
        with patch("trigger_builder.services.gemini._get_client", return_value=fake_client):
            result = gemini.call_gemini({}, {"countryName": "Pakistan"})
        self.assertEqual(result, self.valid_response)

    def test_missing_fields_never_reach_the_frontend(self):
        fake_client = SimpleNamespace(models=FakeModels('{"combined": "only one field"}'))
        with patch("trigger_builder.services.gemini._get_client", return_value=fake_client):
            with self.assertRaisesRegex(ValueError, "missing required fields"):
                gemini.call_gemini({}, {"countryName": "Pakistan"})

    def test_malformed_json_is_rejected(self):
        fake_client = SimpleNamespace(models=FakeModels("not-json"))
        with patch("trigger_builder.services.gemini._get_client", return_value=fake_client):
            with self.assertRaisesRegex(ValueError, "could not be parsed"):
                gemini.call_gemini({}, {"countryName": "Pakistan"})
