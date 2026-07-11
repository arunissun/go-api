import ipaddress

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _


def mask_ip_address(ip: str) -> str | None:
    """
    Return the IP address with its first segment zeroed out for privacy.
    IPv4: 192.168.1.5  -> 0.168.1.5
    IPv6: 2001:db8::1  -> 0:db8::1
    """
    if not ip:
        return None
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return None
    if addr.version == 4:
        parts = ip.split(".")
        parts[0] = "0"
        return ".".join(parts)
    # IPv6 – zero the first group
    # Expand so we always have 8 groups before masking
    expanded = ipaddress.ip_address(ip).exploded
    parts = expanded.split(":")
    parts[0] = "0000"
    return ":".join(parts)


class DocumentDownloadLog(models.Model):
    class DocumentSource(models.TextChoices):
        # External Source
        AZURE_BLOB = "azure_blob", _("Azure Blob")
        # Internal Source
        ADORE = "adore", _("Adore")
        GOAPI = "goapi", _("GOAPI")
        SHAREPOINT = "sharepoint", _("SharePoint")
        OTHER = "other", _("Other")

    class DocumentType(models.TextChoices):
        SITUATION_REPORT = "situation_report", _("Situation Report")
        APPEAL_DOCUMENT = "appeal_document", _("Appeal Document")
        GENERAL_DOCUMENT = "general_document", _("General Document")
        COUNTRY_DOCUMENT = "country_document", _("Country Key Document")
        FEATURED_DOCUMENT = "featured_document", _("Event Featured Document")
        DREF_FILE = "dref_file", _("DREF File")
        PER_DOCUMENT = "per_document", _("PER Document")
        OTHER = "other", _("Other")

    document_type = models.CharField(
        verbose_name=_("document type"),
        max_length=50,
        choices=DocumentType.choices,
    )
    # PK of the source record – nullable for purely external documents
    object_id = models.PositiveIntegerField(
        verbose_name=_("object id"),
        null=True,
        blank=True,
        db_index=True,
    )
    url = models.URLField(
        verbose_name=_("url"),
        max_length=2000,
    )
    source = models.CharField(
        verbose_name=_("source"),
        max_length=20,
        choices=DocumentSource.choices,
        default=DocumentSource.OTHER,
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        verbose_name=_("user"),
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="document_download_logs",
    )
    downloaded_at = models.DateTimeField(
        verbose_name=_("downloaded at"),
        auto_now_add=True,
        db_index=True,
    )
    # First segment zeroed; e.g. 0.168.1.5 for IPv4
    ip_address = models.GenericIPAddressField(
        verbose_name=_("ip address"),
        null=True,
        blank=True,
        unpack_ipv4=True,
    )

    class Meta:
        verbose_name = _("document download log")
        verbose_name_plural = _("document download logs")
        ordering = ("-downloaded_at",)

    def __str__(self):
        return f"{self.document_type} / {self.object_id} @ {self.downloaded_at}"


def detect_source(url: str) -> str:
    """Classify a download URL into a DocumentSource choice."""
    azure_account = getattr(settings, "AZURE_STORAGE_ACCOUNT", None)
    if azure_account and azure_account in url:
        return DocumentDownloadLog.DocumentSource.AZURE_BLOB
    if "blob.core.windows.net" in url:
        return DocumentDownloadLog.DocumentSource.AZURE_BLOB
    if "go-api.ifrc.org" in url:
        return DocumentDownloadLog.DocumentSource.GOAPI
    if "adore.ifrc.org" in url:
        return DocumentDownloadLog.DocumentSource.ADORE
    if "sharepoint.com" in url:
        return DocumentDownloadLog.DocumentSource.SHAREPOINT
    return DocumentDownloadLog.DocumentSource.OTHER
