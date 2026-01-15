# Generated migration to enable pgvector extension

from django.db import migrations


def enable_pgvector(apps, schema_editor):
    """
    Enable pgvector extension in PostgreSQL.

    SQLite (used in many test environments) does not support extensions; this is a no-op there.
    """
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("CREATE EXTENSION IF NOT EXISTS vector;")


def disable_pgvector(apps, schema_editor):
    """Reverse of enable_pgvector (PostgreSQL only)."""
    if schema_editor.connection.vendor != "postgresql":
        return
    schema_editor.execute("DROP EXTENSION IF EXISTS vector;")


class Migration(migrations.Migration):
    """
    Enable pgvector extension in PostgreSQL.
    This must be run before creating tables with VectorField.
    
    This migration has no dependencies so it runs as early as possible.
    The extension needs to be enabled before any VectorField columns are created.
    """
    dependencies = [
        # No dependencies - this should run first to enable the extension
        # before any models with VectorField are created
    ]

    operations = [
        migrations.RunPython(enable_pgvector, reverse_code=disable_pgvector),
    ]

