from rest_framework import mixins, viewsets
from rest_framework.authentication import TokenAuthentication

from .models import DocumentDownloadLog, detect_source, mask_ip_address
from .serializers import DocumentDownloadLogSerializer


def _get_client_ip(request) -> str | None:
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if forwarded_for:
        return forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR")


class DocumentDownloadLogViewSet(mixins.CreateModelMixin, viewsets.GenericViewSet):
    """
    Log a document download event.

    The frontend calls this endpoint (fire-and-forget) each time a user
    initiates a download.  Authentication is optional: anonymous downloads
    are recorded with a null user.
    """

    authentication_classes = (TokenAuthentication,)
    # No permission_classes – allow unauthenticated requests
    permission_classes = []
    serializer_class = DocumentDownloadLogSerializer

    def perform_create(self, serializer):
        url = serializer.validated_data.get("url", "")
        # Auto-detect source from URL when not explicitly provided or defaulted
        source = serializer.validated_data.get("source") or detect_source(url)
        if source == DocumentDownloadLog.DocumentSource.OTHER:
            source = detect_source(url)

        raw_ip = _get_client_ip(self.request)
        masked_ip = mask_ip_address(raw_ip) if raw_ip else None

        user = self.request.user if self.request.user.is_authenticated else None

        serializer.save(
            user=user,
            ip_address=masked_ip,
            source=source,
        )
