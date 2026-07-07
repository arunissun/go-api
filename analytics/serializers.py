from rest_framework import serializers

from .models import DocumentDownloadLog


class DocumentDownloadLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentDownloadLog
        fields = ("id", "document_type", "object_id", "url", "source")
        read_only_fields = ("id",)

    def validate_document_type(self, value):
        if value not in DocumentDownloadLog.DocumentType.values:
            raise serializers.ValidationError(
                f"Invalid document_type. Choose from: {', '.join(DocumentDownloadLog.DocumentType.values)}"
            )
        return value

    def validate_source(self, value):
        if value not in DocumentDownloadLog.DocumentSource.values:
            raise serializers.ValidationError(
                f"Invalid source. Choose from: {', '.join(DocumentDownloadLog.DocumentSource.values)}"
            )
        return value
