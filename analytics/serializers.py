from rest_framework import serializers

from .models import DocumentDownloadLog


class DocumentDownloadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDownloadLog
        fields = ("id", "document_type", "object_id", "url", "source")
        read_only_fields = ("id",)
