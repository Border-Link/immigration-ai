import hashlib


class FileHash:
    """Utility class for computing hashes of uploaded files."""
    
    def __init__(self, file_path):
        self.file_path = file_path

    def generate_file_hash(self, hash_type="md5"):
        """
        Generate hash of a file by reading it in chunks.
        
        Args:
            hash_type: Hash algorithm (default: md5)
            
        Returns:
            Hash as hexadecimal string
        """
        hash_format = hashlib.new(hash_type)
        for chunk in self.file_path.chunks():
            hash_format.update(chunk)
        return hash_format.hexdigest()


class ContentHash:
    """Utility class for computing hashes of text content."""
    
    @staticmethod
    def compute_hash(text: str, hash_type: str = "sha256") -> str:
        """
        Compute hash of text content for change detection.
        
        Args:
            text: Text content to hash
            hash_type: Hash algorithm (default: sha256)
            
        Returns:
            Hash as hexadecimal string
        """
        hash_format = hashlib.new(hash_type)
        hash_format.update(text.encode('utf-8'))
        return hash_format.hexdigest()
    
    @staticmethod
    def compute_sha256(text: str) -> str:
        """
        Compute SHA-256 hash of text content (convenience method).
        
        Args:
            text: Text content to hash
            
        Returns:
            SHA-256 hash as hexadecimal string
        """
        return ContentHash.compute_hash(text, "sha256")