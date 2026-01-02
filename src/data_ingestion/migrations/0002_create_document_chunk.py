# Generated migration for DocumentChunk model

import uuid
from django.db import migrations, models
import django.db.models.deletion
import pgvector.django


class Migration(migrations.Migration):

    dependencies = [
        ('data_ingestion', '0001_enable_pgvector_extension'),
    ]

    operations = [
        migrations.CreateModel(
            name='DocumentChunk',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, db_index=True)),
                ('chunk_text', models.TextField(help_text='Text content of this chunk')),
                ('chunk_index', models.IntegerField(default=0, help_text='Index of this chunk within the document (0-based)')),
                ('embedding', pgvector.django.VectorField(dimensions=1536, blank=True, null=True, help_text='Vector embedding for semantic search')),
                ('metadata', models.JSONField(blank=True, default=dict, help_text='Additional metadata (visa_code, effective_date, jurisdiction, etc.)')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('document_version', models.ForeignKey(db_index=True, help_text='Document version this chunk belongs to', on_delete=django.db.models.deletion.CASCADE, related_name='chunks', to='data_ingestion.documentversion')),
            ],
            options={
                'db_table': 'document_chunks',
                'ordering': ['document_version', 'chunk_index'],
                'verbose_name_plural': 'Document Chunks',
            },
        ),
        migrations.AddIndex(
            model_name='documentchunk',
            index=models.Index(fields=['document_version', 'chunk_index'], name='document_ch_documen_idx'),
        ),
    ]

