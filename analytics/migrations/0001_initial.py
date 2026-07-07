import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentDownloadLog",
            fields=[
                ("id", models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name="ID")),
                (
                    "document_type",
                    models.CharField(
                        choices=[
                            ("situation_report", "Situation Report"),
                            ("appeal_document", "Appeal Document"),
                            ("general_document", "General Document"),
                            ("country_document", "Country Key Document"),
                            ("featured_document", "Event Featured Document"),
                            ("dref_file", "DREF File"),
                            ("per_document", "PER Document"),
                            ("other", "Other"),
                        ],
                        max_length=50,
                        verbose_name="document type",
                    ),
                ),
                (
                    "object_id",
                    models.PositiveIntegerField(blank=True, db_index=True, null=True, verbose_name="object id"),
                ),
                ("url", models.URLField(max_length=2000, verbose_name="url")),
                (
                    "source",
                    models.CharField(
                        choices=[
                            ("azure_blob", "Azure Blob"),
                            ("adore", "Adore"),
                            ("sharepoint", "SharePoint"),
                            ("other", "Other"),
                        ],
                        default="other",
                        max_length=20,
                        verbose_name="source",
                    ),
                ),
                (
                    "downloaded_at",
                    models.DateTimeField(auto_now_add=True, db_index=True, verbose_name="downloaded at"),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True, null=True, unpack_ipv4=True, verbose_name="ip address"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="document_download_logs",
                        to=settings.AUTH_USER_MODEL,
                        verbose_name="user",
                    ),
                ),
            ],
            options={
                "verbose_name": "document download log",
                "verbose_name_plural": "document download logs",
                "ordering": ("-downloaded_at",),
            },
        ),
    ]
