"""
File Storage Service

Handles file uploads and storage for case documents.
Supports both local filesystem and S3 storage.
"""
import logging
import os
import uuid
from typing import Optional, Tuple
from django.conf import settings
from django.core.files.uploadedfile import UploadedFile
from pathlib import Path

logger = logging.getLogger('django')


class FileStorageService:
    """
    Service for handling file storage operations.
    Supports local filesystem and S3 (when configured).
    """

    # Maximum file size: 10MB
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB in bytes
    
    # Allowed file extensions
    ALLOWED_EXTENSIONS = ['.pdf', '.jpg', '.jpeg', '.png', '.doc', '.docx']
    
    # Allowed MIME types
    ALLOWED_MIME_TYPES = [
        'application/pdf',
        'image/jpeg',
        'image/png',
        'application/msword',
        'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
    ]

    @staticmethod
    def validate_file(file: UploadedFile) -> Tuple[bool, Optional[str]]:
        """
        Validate uploaded file.
        
        Security: Validates file size, extension, MIME type, and actual file content
        using magic bytes to prevent MIME type spoofing.
        
        Args:
            file: UploadedFile instance
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        # Check file size
        if file.size > FileStorageService.MAX_FILE_SIZE:
            return False, f"File size exceeds maximum allowed size of {FileStorageService.MAX_FILE_SIZE / (1024*1024)}MB"
        
        # Check file extension
        file_name = file.name.lower()
        if not any(file_name.endswith(ext) for ext in FileStorageService.ALLOWED_EXTENSIONS):
            allowed = ', '.join(FileStorageService.ALLOWED_EXTENSIONS)
            return False, f"File type not allowed. Allowed types: {allowed}"
        
        # Check MIME type if available (declared MIME type)
        if hasattr(file, 'content_type') and file.content_type:
            if file.content_type not in FileStorageService.ALLOWED_MIME_TYPES:
                return False, f"File MIME type '{file.content_type}' not allowed"
        
        # Security: Validate actual file content using magic bytes (prevents MIME spoofing)
        try:
            import magic
            file.seek(0)
            file_content = file.read(1024)  # Read first 1KB for magic bytes
            file.seek(0)  # Reset file pointer
            
            if file_content:
                detected_mime = magic.from_buffer(file_content, mime=True)
                if detected_mime not in FileStorageService.ALLOWED_MIME_TYPES:
                    logger.warning(
                        f"File content validation failed: "
                        f"declared MIME type '{file.content_type if hasattr(file, 'content_type') else 'unknown'}' "
                        f"but detected '{detected_mime}'"
                    )
                    return False, f"File content does not match declared type. Detected: {detected_mime}"
        except ImportError:
            # python-magic not installed, log warning but continue
            logger.warning("python-magic not installed. File content validation skipped.")
        except Exception as e:
            # If magic detection fails, log error but don't block (defensive)
            logger.error(f"Error validating file content with magic bytes: {e}", exc_info=True)
            # In production, you might want to fail here, but for now we'll be defensive
        
        return True, None

    @staticmethod
    def generate_file_path(case_id: str, document_type_id: str, original_filename: str) -> str:
        """
        Generate a unique file path for storing the document.
        
        Args:
            case_id: UUID of the case
            document_type_id: UUID of the document type
            original_filename: Original filename
            
        Returns:
            Relative file path string
        """
        # Generate unique filename
        file_extension = Path(original_filename).suffix
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        
        # Create path: case_documents/{case_id}/{document_type_id}/{unique_filename}
        file_path = f"case_documents/{case_id}/{document_type_id}/{unique_filename}"
        
        return file_path

    @staticmethod
    def store_file_local(file: UploadedFile, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Store file on local filesystem.
        
        Args:
            file: UploadedFile instance
            file_path: Relative file path
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            # Get media root from settings
            media_root = getattr(settings, 'MEDIA_ROOT', None)
            if not media_root:
                # Default to BASE_DIR/media
                base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
                media_root = base_dir / 'media'
            
            # Create full path
            full_path = Path(media_root) / file_path
            
            # Create directory if it doesn't exist
            full_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            with open(full_path, 'wb+') as destination:
                for chunk in file.chunks():
                    destination.write(chunk)
            
            logger.info(f"File stored locally at: {full_path}")
            return True, None
            
        except Exception as e:
            logger.error(f"Error storing file locally: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def store_file_s3(file: UploadedFile, file_path: str) -> Tuple[bool, Optional[str]]:
        """
        Store file in S3 (AWS S3 or DigitalOcean Spaces).
        
        Args:
            file: UploadedFile instance
            file_path: Relative file path (will be used as S3 key)
            
        Returns:
            Tuple of (success, error_message)
        """
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # Get S3 settings
            aws_access_key_id = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
            aws_secret_access_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
            aws_storage_bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
            aws_s3_endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)  # For DigitalOcean Spaces
            
            if not all([aws_access_key_id, aws_secret_access_key, aws_storage_bucket_name]):
                logger.error("S3 credentials not configured")
                return False, "S3 storage not configured"
            
            # Create S3 client
            s3_client = boto3.client(
                's3',
                aws_access_key_id=aws_access_key_id,
                aws_secret_access_key=aws_secret_access_key,
                endpoint_url=aws_s3_endpoint_url  # None for AWS, URL for DigitalOcean
            )
            
            # Upload file
            file.seek(0)  # Reset file pointer
            s3_client.upload_fileobj(
                file,
                aws_storage_bucket_name,
                file_path,
                ExtraArgs={
                    'ContentType': file.content_type if hasattr(file, 'content_type') else 'application/octet-stream',
                    'ACL': 'private'  # Private files
                }
            )
            
            logger.info(f"File stored in S3: {file_path}")
            return True, None
            
        except ImportError:
            logger.error("boto3 not installed. Install with: pip install boto3")
            return False, "S3 storage requires boto3 package"
        except Exception as e:
            logger.error(f"Error storing file in S3: {e}", exc_info=True)
            return False, str(e)

    @staticmethod
    def store_file(file: UploadedFile, case_id: str, document_type_id: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Store uploaded file (local or S3 based on configuration).
        
        Security: Validates file, scans for viruses, then stores.
        
        Args:
            file: UploadedFile instance
            case_id: UUID of the case
            document_type_id: UUID of the document type
            
        Returns:
            Tuple of (file_path, error_message)
        """
        # Step 1: Validate file (size, extension, MIME type, content)
        is_valid, error = FileStorageService.validate_file(file)
        if not is_valid:
            return None, error
        
        # Step 2: Security - Scan file for viruses/malware
        try:
            from document_handling.services.virus_scan_service import VirusScanService
            is_clean, threat_name, scan_error = VirusScanService.scan_file(file)
            
            if not is_clean:
                if threat_name:
                    logger.error(f"Virus detected in uploaded file: {threat_name}")
                    return None, f"File rejected: Threat detected ({threat_name})"
                else:
                    logger.error(f"Virus scan failed: {scan_error}")
                    return None, f"File rejected: Virus scan failed. {scan_error}"
            
            logger.info(f"File passed virus scan: {file.name}")
        except ImportError:
            # Virus scanning service not available - log warning but continue
            logger.warning("Virus scanning service not available. File upload proceeding without scan.")
        except Exception as e:
            # If scanning fails, fail secure: reject the file
            logger.error(f"Error during virus scan: {e}", exc_info=True)
            return None, "File rejected: Virus scan error. Please try again or contact support."
        
        # Generate file path
        file_path = FileStorageService.generate_file_path(
            case_id=case_id,
            document_type_id=document_type_id,
            original_filename=file.name
        )
        
        # Determine storage backend
        use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
        
        if use_s3:
            success, error = FileStorageService.store_file_s3(file, file_path)
        else:
            success, error = FileStorageService.store_file_local(file, file_path)
        
        if success:
            return file_path, None
        else:
            return None, error

    @staticmethod
    def get_file_url(file_path: str, case_id: str = None, user_id: str = None) -> str:
        """
        Get URL to access the stored file.
        
        Security: This method should be called with authorization checks in the view/service layer.
        The caller is responsible for verifying the user has access to the case/document.
        
        Args:
            file_path: Relative file path
            case_id: Optional case ID for authorization (not validated here, caller must check)
            user_id: Optional user ID for authorization (not validated here, caller must check)
            
        Returns:
            URL string
        """
        # Security: Log file access for audit trail
        if case_id or user_id:
            logger.info(
                f"File access requested: path={file_path}, case_id={case_id}, user_id={user_id}"
            )
        
        use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
        
        if use_s3:
            # Generate S3 presigned URL (expires in 1 hour)
            try:
                import boto3
                from botocore.exceptions import ClientError
                
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
                
                url = s3_client.generate_presigned_url(
                    'get_object',
                    Params={'Bucket': aws_storage_bucket_name, 'Key': file_path},
                    ExpiresIn=3600  # 1 hour
                )
                return url
            except Exception as e:
                logger.error(f"Error generating S3 presigned URL: {e}")
                return ""
        else:
            # Local file URL
            media_url = getattr(settings, 'MEDIA_URL', '/media/')
            return f"{media_url}{file_path}"

    @staticmethod
    def delete_file(file_path: str) -> bool:
        """
        Delete a stored file.
        
        Args:
            file_path: Relative file path
            
        Returns:
            True if deleted successfully, False otherwise
        """
        use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
        
        if use_s3:
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
                
                s3_client.delete_object(Bucket=aws_storage_bucket_name, Key=file_path)
                logger.info(f"File deleted from S3: {file_path}")
                return True
            except Exception as e:
                logger.error(f"Error deleting file from S3: {e}")
                return False
        else:
            try:
                media_root = getattr(settings, 'MEDIA_ROOT', None)
                if not media_root:
                    base_dir = getattr(settings, 'BASE_DIR', Path.cwd())
                    media_root = base_dir / 'media'
                
                full_path = Path(media_root) / file_path
                if full_path.exists():
                    full_path.unlink()
                    logger.info(f"File deleted locally: {full_path}")
                    return True
                return False
            except Exception as e:
                logger.error(f"Error deleting local file: {e}")
                return False

