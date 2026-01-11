"""
OCR Service

Service for extracting text from documents using OCR.
Supports multiple OCR backends: Tesseract, AWS Textract, Google Vision API.
"""
import logging
import time
from typing import Tuple, Optional, Dict
from django.conf import settings
from pathlib import Path
from document_handling.helpers.metrics import track_ocr_operation

logger = logging.getLogger('django')


class OCRService:
    """
    Service for OCR text extraction from documents.
    Supports multiple backends with fallback options.
    """

    @staticmethod
    def extract_text(file_path: str, mime_type: str = None) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extract text from document using OCR.
        
        Args:
            file_path: Path to the document file (local or S3 key)
            mime_type: MIME type of the file (optional, for optimization)
            
        Returns:
            Tuple of (extracted_text, metadata, error_message)
            - extracted_text: Extracted text or None if failed
            - metadata: Dict with confidence scores, page count, etc.
            - error_message: Error message if extraction failed
        """
        start_time = time.time()
        try:
            # Determine OCR backend from settings
            ocr_backend = getattr(settings, 'OCR_BACKEND', 'tesseract')
            
            if ocr_backend == 'aws_textract':
                result = OCRService._extract_with_textract(file_path, mime_type)
            elif ocr_backend == 'google_vision':
                result = OCRService._extract_with_google_vision(file_path, mime_type)
            elif ocr_backend == 'tesseract':
                result = OCRService._extract_with_tesseract(file_path, mime_type)
            else:
                logger.error(f"Unknown OCR backend: {ocr_backend}")
                result = (None, None, f"Unknown OCR backend: {ocr_backend}")
            
            # Track metrics
            duration = time.time() - start_time
            extracted_text, metadata, error_message = result
            status = 'success' if extracted_text else 'failure'
            confidence = metadata.get('confidence', 0.0) if metadata else None
            text_length = len(extracted_text) if extracted_text else None
            
            track_ocr_operation(
                backend=ocr_backend,
                status=status,
                duration=duration,
                confidence=confidence,
                text_length=text_length
            )
            
            return result
                
        except Exception as e:
            duration = time.time() - start_time
            track_ocr_operation(backend=getattr(settings, 'OCR_BACKEND', 'tesseract'), status='failure', duration=duration)
            logger.error(f"Error in OCR extraction: {e}", exc_info=True)
            return None, None, str(e)

    @staticmethod
    def _extract_with_tesseract(file_path: str, mime_type: str = None) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extract text using Tesseract OCR.
        
        Args:
            file_path: Path to the document file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (extracted_text, metadata, error_message)
        """
        try:
            import pytesseract
            from PIL import Image
            import pdf2image
            
            # Check if file exists (local storage)
            use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
            
            if use_s3:
                # Download file from S3 first
                file_content = OCRService._download_from_s3(file_path)
                if not file_content:
                    return None, None, "Failed to download file from S3"
            else:
                # Local file
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if not media_root:
                    base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
                    media_root = base_dir / 'media'
                
                full_path = Path(media_root) / file_path
                if not full_path.exists():
                    return None, None, f"File not found: {full_path}"
            
            # Extract text based on file type
            if mime_type == 'application/pdf' or file_path.lower().endswith('.pdf'):
                # Convert PDF to images
                if use_s3:
                    images = pdf2image.convert_from_bytes(file_content)
                else:
                    images = pdf2image.convert_from_path(str(full_path))
                
                # Extract text from each page
                extracted_texts = []
                for image in images:
                    text = pytesseract.image_to_string(image, lang='eng')
                    extracted_texts.append(text)
                
                full_text = '\n\n'.join(extracted_texts)
                metadata = {
                    'pages': len(images),
                    'backend': 'tesseract',
                    'language': 'eng'
                }
                
            else:
                # Image file
                if use_s3:
                    from io import BytesIO
                    image = Image.open(BytesIO(file_content))
                else:
                    image = Image.open(full_path)
                
                # Extract text
                full_text = pytesseract.image_to_string(image, lang='eng')
                
                # Get confidence data
                data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)
                avg_confidence = sum([int(conf) for conf in data['conf'] if int(conf) > 0]) / max(len([c for c in data['conf'] if int(c) > 0]), 1)
                
                metadata = {
                    'pages': 1,
                    'backend': 'tesseract',
                    'language': 'eng',
                    'average_confidence': avg_confidence
                }
            
            # Validate extraction
            if not full_text or len(full_text.strip()) < 10:
                return None, metadata, "OCR extracted insufficient text (may be image-only document)"
            
            logger.info(f"OCR extraction successful: {len(full_text)} characters extracted")
            return full_text, metadata, None
            
        except ImportError:
            logger.error("Tesseract dependencies not installed. Install with: pip install pytesseract pdf2image pillow")
            return None, None, "Tesseract OCR not available. Install pytesseract, pdf2image, and pillow packages."
        except Exception as e:
            logger.error(f"Error in Tesseract OCR: {e}", exc_info=True)
            return None, None, str(e)

    @staticmethod
    def _extract_with_textract(file_path: str, mime_type: str = None) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extract text using AWS Textract.
        
        Args:
            file_path: S3 key or local file path
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (extracted_text, metadata, error_message)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get S3 settings
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_storage_bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            
            if not all([aws_access_key_id, aws_secret_access_key, aws_storage_bucket_name]):
                return None, None, "AWS credentials not configured for Textract"
            
            # Create Textract client
            textract_client = boto3.client(
                'textract',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                region_name=getattr(settings, 'AWS_REGION', 'us-east-1')
            )
            
            # Call Textract
            # If file is in S3, use S3 reference
            use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
            
            if use_s3:
                response = textract_client.detect_document_text(
                    Document={
                        'S3Object': {
                            'Bucket': aws_storage_bucket_name,
                            'Name': file_path
                        }
                    }
                )
            else:
                # Read local file and send bytes
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if not media_root:
                    base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
                    media_root = base_dir / 'media'
                
                full_path = Path(media_root) / file_path
                with open(full_path, 'rb') as f:
                    document_bytes = f.read()
                
                response = textract_client.detect_document_text(
                    Document={'Bytes': document_bytes}
                )
            
            # Extract text from response
            blocks = response.get('Blocks', [])
            text_blocks = [block['Text'] for block in blocks if block['BlockType'] == 'LINE']
            full_text = '\n'.join(text_blocks)
            
            metadata = {
                'pages': len([b for b in blocks if b.get('BlockType') == 'PAGE']),
                'backend': 'aws_textract',
                'blocks_count': len(blocks)
            }
            
            if not full_text or len(full_text.strip()) < 10:
                return None, metadata, "Textract extracted insufficient text"
            
            logger.info(f"Textract extraction successful: {len(full_text)} characters extracted")
            return full_text, metadata, None
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return None, None, "AWS Textract not available. Install boto3 package."
        except Exception as e:
            logger.error(f"Error in AWS Textract: {e}", exc_info=True)
            return None, None, str(e)

    @staticmethod
    def _extract_with_google_vision(file_path: str, mime_type: str = None) -> Tuple[Optional[str], Optional[Dict], Optional[str]]:
        """
        Extract text using Google Vision API.
        
        Args:
            file_path: Path to the document file
            mime_type: MIME type of the file
            
        Returns:
            Tuple of (extracted_text, metadata, error_message)
        """
        try:
            from google.cloud import vision
            
            # Get credentials
            google_credentials_path = getattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS', None)
            if not google_credentials_path:
                return None, None, "Google Vision credentials not configured"
            
            # Create client
            client = vision.ImageAnnotatorClient()
            
            # Read file
            use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
            
            if use_s3:
                file_content = OCRService._download_from_s3(file_path)
                if not file_content:
                    return None, None, "Failed to download file from S3"
                image = vision.Image(content=file_content)
            else:
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if not media_root:
                    base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
                    media_root = base_dir / 'media'
                
                full_path = Path(media_root) / file_path
                with open(full_path, 'rb') as f:
                    content = f.read()
                image = vision.Image(content=content)
            
            # Extract text
            response = client.document_text_detection(image=image)
            full_text = response.full_text_annotation.text if response.full_text_annotation else ""
            
            metadata = {
                'backend': 'google_vision',
                'pages': 1  # Google Vision processes single images
            }
            
            if not full_text or len(full_text.strip()) < 10:
                return None, metadata, "Google Vision extracted insufficient text"
            
            logger.info(f"Google Vision extraction successful: {len(full_text)} characters extracted")
            return full_text, metadata, None
            
        except ImportError:
            logger.error("Google Cloud Vision not installed. Install with: pip install google-cloud-vision")
            return None, None, "Google Vision not available. Install google-cloud-vision package."
        except Exception as e:
            logger.error(f"Error in Google Vision: {e}", exc_info=True)
            return None, None, str(e)

    @staticmethod
    def _download_from_s3(file_path: str) -> Optional[bytes]:
        """Download file from S3 and return as bytes."""
        try:
            import boto3
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_storage_bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            aws_s3_endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
            
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                endpoint_url=aws_s3_endpoint_url
            )
            
            from io import BytesIO
            file_obj = BytesIO()
            s3_client.download_fileobj(aws_storage_bucket_name, file_path, file_obj)
            file_obj.seek(0)
            return file_obj.read()
        except Exception as e:
            logger.error(f"Error downloading from S3: {e}")
            return None

