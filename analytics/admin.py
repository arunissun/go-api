from django.contrib import admin

from dref.admin import ReadOnlyMixin

from .models import DocumentDownloadLog


@admin.register(DocumentDownloadLog)
class DocumentDownloadLogAdmin(ReadOnlyMixin, admin.ModelAdmin):
    list_display = ("downloaded_at", "document_type", "source", "object_id", "user", "ip_address")
    list_filter = ("document_type", "source")
    date_hierarchy = "downloaded_at"
    search_fields = ("url", "user__username", "user__email")
    readonly_fields = (
        "document_type",
        "object_id",
        "url",
        "source",
        "user",
        "downloaded_at",
        "ip_address",
    )
    ordering = ("-downloaded_at",)
