import secrets

from django.conf import settings
from rest_framework import status
from rest_framework.request import Request
from rest_framework.response import Response


def check_prototype_access(request: Request) -> Response | None:
    """Protect only billable Phase 1 endpoints with a temporary session code."""
    if not settings.PROTOTYPE_ACCESS_REQUIRED:
        return None

    supplied = request.headers.get("X-Prototype-Access-Code", "")
    if not supplied:
        return Response(
            {
                "error": "A prototype access code is required.",
                "code": "PROTOTYPE_ACCESS_REQUIRED",
            },
            status=status.HTTP_401_UNAUTHORIZED,
        )

    expected = settings.PROTOTYPE_ACCESS_CODE
    if not secrets.compare_digest(supplied.encode("utf-8"), expected.encode("utf-8")):
        return Response(
            {
                "error": "The prototype access code was rejected.",
                "code": "PROTOTYPE_ACCESS_DENIED",
            },
            status=status.HTTP_403_FORBIDDEN,
        )
    return None
