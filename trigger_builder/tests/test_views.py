from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

from django.test import SimpleTestCase, override_settings
from httpx import ReadTimeout
from rest_framework.test import APIClient


REVIEW_OUTPUT = {
    "preActivation": "Prepared wording",
    "activation": "Activation wording",
    "stop": "",
    "combined": "Prepared wording then activation wording",
    "warnings": [],
}

PAYLOAD = {
    "documentContext": {
        "countryOrOperationName": "Pakistan",
        "countryId": 153,
        "countryIso": "PK",
        "countryIso3": "PAK",
        "countryName": "Pakistan",
        "operationTitle": "Flood EAP",
        "hazardTypes": ["Flood"],
        "eapName": "Flood EAP",
        "eapVariant": "Single stage",
        "versionLabel": "Phase 1",
    },
    "statements": [
        {
            "id": "statement-1",
            "phase": "activation",
            "canonicalVariable": "Precipitation",
            "operator": ">=",
            "thresholdValue": "100",
            "thresholdUnit": "mm",
            "timeframeUnit": "days",
            "geographyType": "national",
            "geographyLabel": "Pakistan",
            "geographyConfirmed": True,
        }
    ],
}


class PublicEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_schema_and_examples_are_public(self):
        schema = self.client.get("/api/trigger-builder/schema")
        examples = self.client.get("/api/trigger-builder/examples")
        self.assertEqual(schema.status_code, 200)
        self.assertEqual(examples.status_code, 200)
        self.assertGreater(examples.json()["count"], 0)

    def test_validate_accepts_confirmed_structured_country_payload(self):
        response = self.client.post("/api/trigger-builder/validate", PAYLOAD, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["valid"])

    def test_validate_rejects_unconfirmed_non_national_geography(self):
        payload = {
            **PAYLOAD,
            "statements": [
                {
                    **PAYLOAD["statements"][0],
                    "geographyType": "regional",
                    "geographyLabel": "Punjab",
                    "geographyConfirmed": False,
                }
            ],
        }
        response = self.client.post("/api/trigger-builder/validate", payload, format="json")
        self.assertEqual(response.status_code, 200)
        self.assertFalse(response.json()["valid"])


@override_settings(PROTOTYPE_ACCESS_REQUIRED=True, PROTOTYPE_ACCESS_CODE="test-access-code")
class BillableEndpointTests(SimpleTestCase):
    def setUp(self):
        self.client = APIClient()

    def test_missing_and_incorrect_access_codes_are_rejected(self):
        missing = self.client.post("/api/trigger-builder/generate", PAYLOAD, format="json")
        wrong = self.client.post(
            "/api/trigger-builder/generate",
            PAYLOAD,
            format="json",
            HTTP_X_PROTOTYPE_ACCESS_CODE="wrong",
        )
        self.assertEqual(missing.status_code, 401)
        self.assertEqual(missing.json()["code"], "PROTOTYPE_ACCESS_REQUIRED")
        self.assertEqual(wrong.status_code, 403)
        self.assertEqual(wrong.json()["code"], "PROTOTYPE_ACCESS_DENIED")

    @patch(
        "trigger_builder.views.gemini.call_gemini",
        side_effect=lambda *_args, **_kwargs: REVIEW_OUTPUT.copy(),
    )
    def test_generate_and_regenerate_succeed_with_mocked_gemini(self, mocked_call):
        headers = {"HTTP_X_PROTOTYPE_ACCESS_CODE": "test-access-code"}
        generated = self.client.post(
            "/api/trigger-builder/generate", PAYLOAD, format="json", **headers
        )
        regenerated = self.client.post(
            "/api/trigger-builder/regenerate",
            {**PAYLOAD, "reviewerNotes": "Keep it concise."},
            format="json",
            **headers,
        )
        self.assertEqual(generated.status_code, 200)
        self.assertEqual(regenerated.status_code, 200)
        self.assertEqual(generated.json()["modelId"], "gemini-3.5-flash")
        self.assertEqual(mocked_call.call_count, 2)

    def test_provider_timeout_malformed_and_provider_errors_are_safe(self):
        headers = {"HTTP_X_PROTOTYPE_ACCESS_CODE": "test-access-code"}
        cases = [
            (TimeoutError("deadline"), 504, "GEMINI_TIMEOUT"),
            (ReadTimeout("provider deadline"), 504, "GEMINI_TIMEOUT"),
            (ValueError("malformed JSON or missing fields"), 502, "GEMINI_INVALID_RESPONSE"),
            (RuntimeError("provider failure"), 502, "GEMINI_PROVIDER_ERROR"),
        ]
        for exception, expected_status, expected_code in cases:
            with self.subTest(expected_code=expected_code):
                with patch("trigger_builder.views.gemini.call_gemini", side_effect=exception):
                    response = self.client.post(
                        "/api/trigger-builder/generate", PAYLOAD, format="json", **headers
                    )
                self.assertEqual(response.status_code, expected_status)
                self.assertEqual(response.json()["code"], expected_code)
                self.assertNotIn(str(exception), response.content.decode("utf-8"))


@override_settings(PROTOTYPE_ACCESS_REQUIRED=False)
class CapacityAndCorsTests(SimpleTestCase):
    @patch(
        "trigger_builder.views.gemini.call_gemini",
        side_effect=lambda *_args, **_kwargs: REVIEW_OUTPUT.copy(),
    )
    def test_eight_parallel_mocked_generation_requests(self, mocked_call):
        def issue_request(_index):
            return APIClient().post(
                "/api/trigger-builder/generate", PAYLOAD, format="json"
            ).status_code

        with ThreadPoolExecutor(max_workers=8) as executor:
            statuses = list(executor.map(issue_request, range(8)))
        self.assertEqual(statuses, [200] * 8)
        self.assertEqual(mocked_call.call_count, 8)

    def test_cors_allows_documented_origin_and_rejects_unknown_origin(self):
        client = APIClient()
        allowed = client.options(
            "/api/trigger-builder/generate",
            HTTP_ORIGIN="http://localhost:5173",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
            HTTP_ACCESS_CONTROL_REQUEST_HEADERS=(
                "content-type,x-prototype-access-code"
            ),
        )
        denied = client.options(
            "/api/trigger-builder/generate",
            HTTP_ORIGIN="https://example.invalid",
            HTTP_ACCESS_CONTROL_REQUEST_METHOD="POST",
        )
        self.assertEqual(
            allowed.headers.get("Access-Control-Allow-Origin"),
            "http://localhost:5173",
        )
        self.assertIn(
            "x-prototype-access-code",
            allowed.headers.get("Access-Control-Allow-Headers", ""),
        )
        self.assertIsNone(denied.headers.get("Access-Control-Allow-Origin"))
