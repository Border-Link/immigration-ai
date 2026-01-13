"""
Prometheus Metrics for Document Handling Module

Custom metrics for monitoring document handling operations including:
- Document uploads
- OCR operations
- Document classification
- Document validation
- Document checks and matching
"""
import time
from functools import wraps

# Import prometheus_client for custom metrics
try:
    from prometheus_client import Counter, Histogram, Gauge
except ImportError:
    Counter = None
    Histogram = None
    Gauge = None


# Document Upload Metrics
if Counter and Histogram:
    document_uploads_total = Counter(
        'document_handling_document_uploads_total',
        'Total number of document uploads',
        ['status', 'document_type']  # status: success, failure; document_type: passport, visa, etc.
    )
    
    document_upload_duration_seconds = Histogram(
        'document_handling_document_upload_duration_seconds',
        'Duration of document upload operations in seconds',
        ['document_type'],
        buckets=(0.5, 1.0, 2.0, 5.0, 10.0, 30.0)
    )
    
    document_upload_size_bytes = Histogram(
        'document_handling_document_upload_size_bytes',
        'Size of uploaded documents in bytes',
        ['document_type'],
        buckets=(1024, 10240, 102400, 1048576, 10485760, 52428800)  # 1KB to 50MB
    )
    
    # OCR Metrics
    ocr_operations_total = Counter(
        'document_handling_ocr_operations_total',
        'Total number of OCR operations',
        ['backend', 'status']  # backend: tesseract, aws_textract, google_vision; status: success, failure
    )
    
    ocr_duration_seconds = Histogram(
        'document_handling_ocr_duration_seconds',
        'Duration of OCR operations in seconds',
        ['backend'],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0, 120.0)
    )
    
    ocr_confidence_score = Histogram(
        'document_handling_ocr_confidence_score',
        'OCR confidence scores',
        ['backend'],
        buckets=(0.0, 0.5, 0.7, 0.8, 0.9, 0.95, 1.0)
    )
    
    ocr_text_length = Histogram(
        'document_handling_ocr_text_length',
        'Length of extracted OCR text',
        ['backend'],
        buckets=(100, 500, 1000, 5000, 10000, 50000, 100000)
    )
    
    # Document Classification Metrics
    document_classifications_total = Counter(
        'document_handling_document_classifications_total',
        'Total number of document classifications',
        ['classification_type', 'status']  # classification_type: automated, manual; status: success, failure
    )
    
    document_classification_duration_seconds = Histogram(
        'document_handling_document_classification_duration_seconds',
        'Duration of document classification in seconds',
        ['classification_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Document Validation Metrics
    document_validations_total = Counter(
        'document_handling_document_validations_total',
        'Total number of document validations',
        ['validation_type', 'status']  # validation_type: content, expiry, format; status: valid, invalid
    )
    
    document_validation_duration_seconds = Histogram(
        'document_handling_document_validation_duration_seconds',
        'Duration of document validation in seconds',
        ['validation_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Document Check Metrics
    document_checks_total = Counter(
        'document_handling_document_checks_total',
        'Total number of document checks',
        ['check_type', 'status']  # check_type: requirement_match, expiry_check, etc.; status: pass, fail
    )
    
    document_check_duration_seconds = Histogram(
        'document_handling_document_check_duration_seconds',
        'Duration of document checks in seconds',
        ['check_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0)
    )
    
    # Document Requirement Matching Metrics
    document_requirement_matches_total = Counter(
        'document_handling_document_requirement_matches_total',
        'Total number of document requirement matches',
        ['match_status']  # match_status: matched, unmatched, partial
    )
    
    # Document Expiry Extraction Metrics
    document_expiry_extractions_total = Counter(
        'document_handling_document_expiry_extractions_total',
        'Total number of document expiry extractions',
        ['status']  # status: success, failure, not_found
    )
    
    # Document Reprocessing Metrics
    document_reprocessing_operations_total = Counter(
        'document_handling_document_reprocessing_operations_total',
        'Total number of document reprocessing operations',
        ['reason', 'status']  # reason: ocr_failed, validation_failed, etc.; status: success, failure
    )
    
    document_reprocessing_duration_seconds = Histogram(
        'document_handling_document_reprocessing_duration_seconds',
        'Duration of document reprocessing in seconds',
        [],
        buckets=(1.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    # File Storage Metrics
    file_storage_operations_total = Counter(
        'document_handling_file_storage_operations_total',
        'Total number of file storage operations',
        ['operation', 'storage_type']  # operation: upload, download, delete; storage_type: s3, local
    )
    
    file_storage_duration_seconds = Histogram(
        'document_handling_file_storage_duration_seconds',
        'Duration of file storage operations in seconds',
        ['operation', 'storage_type'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0)
    )
    
    # Virus Scanning Metrics
    virus_scans_total = Counter(
        'document_handling_virus_scans_total',
        'Total number of virus scans',
        ['backend', 'status']  # backend: clamav, aws_macie, none; status: clean, threat_detected, failed, skipped
    )
    
    virus_scan_duration_seconds = Histogram(
        'document_handling_virus_scan_duration_seconds',
        'Duration of virus scans in seconds',
        ['backend'],
        buckets=(0.1, 0.5, 1.0, 2.0, 5.0, 10.0, 30.0, 60.0)
    )
    
    virus_threats_detected_total = Counter(
        'document_handling_virus_threats_detected_total',
        'Total number of threats detected',
        ['backend', 'threat_type']  # threat_type: virus, malware, trojan, etc.
    )
    
else:
    # Dummy metrics
    document_uploads_total = None
    document_upload_duration_seconds = None
    document_upload_size_bytes = None
    ocr_operations_total = None
    ocr_duration_seconds = None
    ocr_confidence_score = None
    ocr_text_length = None
    document_classifications_total = None
    document_classification_duration_seconds = None
    document_validations_total = None
    document_validation_duration_seconds = None
    document_checks_total = None
    document_check_duration_seconds = None
    document_requirement_matches_total = None
    document_expiry_extractions_total = None
    document_reprocessing_operations_total = None
    document_reprocessing_duration_seconds = None
    file_storage_operations_total = None
    file_storage_duration_seconds = None
    virus_scans_total = None
    virus_scan_duration_seconds = None
    virus_threats_detected_total = None


def track_document_upload(status: str, document_type: str, duration: float, size_bytes: int = None):
    """Track document upload metrics."""
    if document_uploads_total:
        document_uploads_total.labels(status=status, document_type=document_type).inc()
    if document_upload_duration_seconds:
        document_upload_duration_seconds.labels(document_type=document_type).observe(duration)
    if document_upload_size_bytes and size_bytes:
        document_upload_size_bytes.labels(document_type=document_type).observe(size_bytes)


def track_ocr_operation(backend: str, status: str, duration: float, confidence: float = None, text_length: int = None):
    """Track OCR operation metrics."""
    if ocr_operations_total:
        ocr_operations_total.labels(backend=backend, status=status).inc()
    if ocr_duration_seconds:
        ocr_duration_seconds.labels(backend=backend).observe(duration)
    if ocr_confidence_score and confidence:
        ocr_confidence_score.labels(backend=backend).observe(confidence)
    if ocr_text_length and text_length:
        ocr_text_length.labels(backend=backend).observe(text_length)


def track_document_classification(classification_type: str, status: str, duration: float):
    """Track document classification metrics."""
    if document_classifications_total:
        document_classifications_total.labels(classification_type=classification_type, status=status).inc()
    if document_classification_duration_seconds:
        document_classification_duration_seconds.labels(classification_type=classification_type).observe(duration)


def track_document_validation(validation_type: str, status: str, duration: float):
    """Track document validation metrics."""
    if document_validations_total:
        document_validations_total.labels(validation_type=validation_type, status=status).inc()
    if document_validation_duration_seconds:
        document_validation_duration_seconds.labels(validation_type=validation_type).observe(duration)


def track_document_check(check_type: str, status: str, duration: float):
    """Track document check metrics."""
    if document_checks_total:
        document_checks_total.labels(check_type=check_type, status=status).inc()
    if document_check_duration_seconds:
        document_check_duration_seconds.labels(check_type=check_type).observe(duration)


def track_document_requirement_match(match_status: str):
    """Track document requirement matching."""
    if document_requirement_matches_total:
        document_requirement_matches_total.labels(match_status=match_status).inc()


def track_document_expiry_extraction(status: str):
    """Track document expiry extraction."""
    if document_expiry_extractions_total:
        document_expiry_extractions_total.labels(status=status).inc()


def track_document_reprocessing(reason: str, status: str, duration: float):
    """Track document reprocessing metrics."""
    if document_reprocessing_operations_total:
        document_reprocessing_operations_total.labels(reason=reason, status=status).inc()
    if document_reprocessing_duration_seconds:
        document_reprocessing_duration_seconds.observe(duration)


def track_file_storage_operation(operation: str, storage_type: str, duration: float):
    """Track file storage operation metrics."""
    if file_storage_operations_total:
        file_storage_operations_total.labels(operation=operation, storage_type=storage_type).inc()
    if file_storage_duration_seconds:
        file_storage_duration_seconds.labels(operation=operation, storage_type=storage_type).observe(duration)


def track_virus_scan(backend: str, status: str, duration: float, threat_detected: bool = False, threat_type: str = None):
    """
    Track virus scan metrics.
    
    Args:
        backend: Scanning backend (clamav, aws_macie, none)
        status: Scan status (clean, threat_detected, failed, skipped)
        duration: Scan duration in seconds
        threat_detected: Whether a threat was detected
        threat_type: Type of threat detected (if any)
    """
    if virus_scans_total:
        virus_scans_total.labels(backend=backend, status=status).inc()
    if virus_scan_duration_seconds:
        virus_scan_duration_seconds.labels(backend=backend).observe(duration)
    if virus_threats_detected_total and threat_detected:
        threat_type_label = threat_type or 'unknown'
        virus_threats_detected_total.labels(backend=backend, threat_type=threat_type_label).inc()
