import json
import logging

from django.conf import settings
from httpx import TimeoutException
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.views import APIView

from trigger_builder.serializers import (
    GenerateRequestSerializer,
    RegenerateRequestSerializer,
    ValidateRequestSerializer,
)
from trigger_builder.access import check_prototype_access
from trigger_builder.services import builder, gemini
from trigger_builder.services.data import load_compact_schema, load_pilot_examples, load_pilot_statements
from trigger_builder.services.validate import validate_document_context, validate_statement

logger = logging.getLogger(__name__)


def generation_error_response(exc: Exception) -> Response:
    if isinstance(exc, (TimeoutError, TimeoutException)):
        return Response(
            {"error": "AI generation timed out. Please try again.", "code": "GEMINI_TIMEOUT"},
            status=status.HTTP_504_GATEWAY_TIMEOUT,
        )
    if isinstance(exc, (ValueError, json.JSONDecodeError)):
        return Response(
            {"error": "The AI provider returned an invalid response.", "code": "GEMINI_INVALID_RESPONSE"},
            status=status.HTTP_502_BAD_GATEWAY,
        )
    return Response(
        {"error": "AI generation failed. Please try again.", "code": "GEMINI_PROVIDER_ERROR"},
        status=status.HTTP_502_BAD_GATEWAY,
    )


class SchemaView(APIView):
    """GET /api/trigger-builder/schema — return processed schema lookups."""

    def get(self, request: Request) -> Response:
        try:
            data = load_compact_schema()
        except FileNotFoundError as exc:
            logger.error("Schema file not found: %s", exc)
            return Response({"error": "Schema data not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        except json.JSONDecodeError as exc:
            logger.error("Schema file is malformed: %s", exc)
            return Response({"error": "Schema data is malformed."}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        return Response(data)


class ExamplesView(APIView):
    """GET /api/trigger-builder/examples — return pilot EAP summaries."""

    def get(self, request: Request) -> Response:
        try:
            raw = load_pilot_examples()
            statements_by_id = load_pilot_statements()
        except FileNotFoundError as exc:
            logger.error("Pilot data file not found: %s", exc)
            return Response({"error": "Pilot examples not available."}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        selected = (raw or {}).get("selected", [])
        examples = [
            {
                "document_id": ex.get("document_id"),
                "document_name": ex.get("document_name"),
                "file": ex.get("file"),
                "activation_type": ex.get("activation_type"),
                "trigger_count_openai": ex.get("trigger_count_openai"),
                "hard_case_score": ex.get("hard_case_score"),
                "hard_case_flags": ex.get("hard_case_flags"),
                "stop_mechanism_present": ex.get("stop_mechanism_present"),
                "inter_phase_connector": ex.get("inter_phase_connector"),
                "connector_method": ex.get("connector_method"),
                "selection_bucket": ex.get("selection_bucket"),
                "pilot_order": ex.get("pilot_order"),
                "statements": statements_by_id.get(str(ex.get("document_id")), []),
            }
            for ex in selected
        ]
        return Response({"count": len(examples), "examples": examples})


class ValidateView(APIView):
    """POST /api/trigger-builder/validate — structural validation without generation."""

    def post(self, request: Request) -> Response:
        serializer = ValidateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        doc = data["documentContext"]
        statements = data["statements"]

        all_warnings, all_errors = validate_document_context(doc)

        if not statements:
            all_errors.append("statements: at least one statement is required.")
        for s in statements:
            w, e = validate_statement(s)
            all_warnings.extend(w)
            all_errors.extend(e)

        return Response({"valid": len(all_errors) == 0, "warnings": all_warnings, "errors": all_errors})


class GenerateView(APIView):
    """POST /api/trigger-builder/generate — build deterministic draft then call Gemini."""

    def post(self, request: Request) -> Response:
        access_error = check_prototype_access(request)
        if access_error is not None:
            return access_error
        serializer = GenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        doc = data["documentContext"]
        statements = data["statements"]

        deterministic = builder.build_deterministic_draft(doc, statements)

        try:
            review_output = gemini.call_gemini(deterministic, doc)
        except Exception as exc:
            logger.exception("Gemini call failed (%s)", type(exc).__name__)
            return generation_error_response(exc)

        top_warnings = review_output.pop("warnings", [])
        return Response(
            {
                "documentContext": doc,
                "statements": statements,
                "deterministicDraft": deterministic,
                "reviewOutput": review_output,
                "warnings": top_warnings,
                "modelId": settings.GEMINI_MODEL_ID,
                "promptVersion": settings.GEMINI_PROMPT_VERSION,
            }
        )


class RegenerateView(APIView):
    """POST /api/trigger-builder/regenerate — same as generate but with reviewer notes."""

    def post(self, request: Request) -> Response:
        access_error = check_prototype_access(request)
        if access_error is not None:
            return access_error
        serializer = RegenerateRequestSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        data = serializer.validated_data
        doc = data["documentContext"]
        statements = data["statements"]
        reviewer_notes = data.get("reviewerNotes", "")

        deterministic = builder.build_deterministic_draft(doc, statements)

        try:
            review_output = gemini.call_gemini(deterministic, doc, reviewer_notes=reviewer_notes)
        except Exception as exc:
            logger.exception("Gemini regenerate call failed (%s)", type(exc).__name__)
            return generation_error_response(exc)

        top_warnings = review_output.pop("warnings", [])
        return Response(
            {
                "documentContext": doc,
                "statements": statements,
                "deterministicDraft": deterministic,
                "reviewOutput": review_output,
                "warnings": top_warnings,
                "modelId": settings.GEMINI_MODEL_ID,
                "promptVersion": settings.GEMINI_PROMPT_VERSION,
            }
        )
