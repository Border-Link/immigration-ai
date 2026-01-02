# Generated migration to create HNSW index for vector similarity search

from django.db import migrations


class Migration(migrations.Migration):
    """
    Create HNSW index for fast approximate vector similarity search.
    This index enables efficient cosine similarity queries on embeddings.
    """
    dependencies = [
        ('data_ingestion', '0002_create_document_chunk'),
    ]

    operations = [
        migrations.RunSQL(
            sql="""
            CREATE INDEX IF NOT EXISTS document_chunks_embedding_idx 
            ON document_chunks 
            USING hnsw (embedding vector_cosine_ops);
            """,
            reverse_sql="DROP INDEX IF EXISTS document_chunks_embedding_idx;"
        ),
    ]

