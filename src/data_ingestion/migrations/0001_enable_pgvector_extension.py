# Generated migration to enable pgvector extension

from django.db import migrations


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
        migrations.RunSQL(
            sql="CREATE EXTENSION IF NOT EXISTS vector;",
            reverse_sql="DROP EXTENSION IF EXISTS vector;"
        ),
    ]

