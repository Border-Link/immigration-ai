from django.db import transaction
from django.db.models import F
from django.utils import timezone
from django.core.exceptions import ValidationError
from data_ingestion.models.data_source import DataSource


class DataSourceRepository:
    """Repository for DataSource write operations."""

    @staticmethod
    def create_data_source(name: str, base_url: str, jurisdiction: str, 
                          crawl_frequency: str = 'daily', is_active: bool = True):
        """Create a new data source."""
        with transaction.atomic():
            data_source = DataSource.objects.create(
                name=name,
                base_url=base_url,
                jurisdiction=jurisdiction,
                crawl_frequency=crawl_frequency,
                is_active=is_active,
                version=1,
                is_deleted=False,
            )
            data_source.full_clean()
            data_source.save()
            return data_source

    @staticmethod
    def update_data_source(data_source: DataSource, version: int = None, **fields) -> DataSource:
        """
        Update data source fields with optimistic locking.

        Uses a single conditional UPDATE (WHERE id AND version) to prevent last-write-wins overwrites.
        """
        with transaction.atomic():
            expected_version = version if version is not None else getattr(data_source, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            allowed_fields = {f.name for f in DataSource._meta.fields}
            protected_fields = {"id", "version", "created_at"}
            update_fields = {
                k: v for k, v in fields.items()
                if k in allowed_fields and k not in protected_fields
            }

            # QuerySet.update bypasses auto_now; set updated_at explicitly.
            if "updated_at" in allowed_fields:
                update_fields["updated_at"] = timezone.now()

            updated_count = DataSource.objects.filter(
                id=data_source.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                **update_fields,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DataSource.objects.filter(id=data_source.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Data source not found.")
                raise ValidationError(
                    f"Data source was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DataSource.objects.get(id=data_source.id)

    @staticmethod
    def update_last_fetched(data_source):
        """Update last_fetched_at timestamp."""
        with transaction.atomic():
            expected_version = getattr(data_source, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DataSource.objects.filter(
                id=data_source.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                last_fetched_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )
            if updated_count != 1:
                current_version = DataSource.objects.filter(id=data_source.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Data source not found.")
                raise ValidationError(
                    f"Data source was modified by another user. Expected version {expected_version}, got {current_version}."
                )
            return DataSource.objects.get(id=data_source.id)

    @staticmethod
    def activate_data_source(data_source, is_active: bool):
        """Activate or deactivate data source."""
        return DataSourceRepository.update_data_source(
            data_source,
            version=getattr(data_source, "version", None),
            is_active=is_active,
        )

    @staticmethod
    def soft_delete_data_source(data_source: DataSource, version: int = None) -> DataSource:
        """Soft delete a data source with optimistic locking."""
        with transaction.atomic():
            expected_version = version if version is not None else getattr(data_source, "version", None)
            if expected_version is None:
                raise ValidationError("Missing version for optimistic locking.")

            now_ts = timezone.now()
            updated_count = DataSource.objects.filter(
                id=data_source.id,
                version=expected_version,
                is_deleted=False,
            ).update(
                is_deleted=True,
                deleted_at=now_ts,
                updated_at=now_ts,
                version=F("version") + 1,
            )

            if updated_count != 1:
                current_version = DataSource.objects.filter(id=data_source.id).values_list("version", flat=True).first()
                if current_version is None:
                    raise ValidationError("Data source not found.")
                raise ValidationError(
                    f"Data source was modified by another user. Expected version {expected_version}, got {current_version}."
                )

            return DataSource.objects.get(id=data_source.id)

    @staticmethod
    def delete_data_source(data_source: DataSource, version: int = None):
        """
        Delete a data source.

        CRITICAL: Deletion must be soft-delete to preserve auditability.
        """
        DataSourceRepository.soft_delete_data_source(data_source, version=version)
        return True
