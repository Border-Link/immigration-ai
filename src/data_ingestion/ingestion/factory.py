from typing import Optional
from .base_ingestion import BaseIngestionSystem
from .uk_ingestion import UKIngestionSystem
import logging
from django.conf import settings

logger = logging.getLogger('django')


class IngestionSystemFactory:
    """
    Factory for creating jurisdiction-specific ingestion systems.
    """
    
    _systems = {
        'UK': UKIngestionSystem,
        # Future implementations:
        # 'US': USIngestionSystem,
        # 'CA': CanadaIngestionSystem,
        # 'AU': AustraliaIngestionSystem,
    }
    
    @classmethod
    def create(cls, data_source) -> Optional[BaseIngestionSystem]:
        """
        Create an ingestion system for the given data source.
        
        Args:
            data_source: DataSource model instance
            
        Returns:
            Instance of the appropriate ingestion system, or None if not supported
        """
        jurisdiction = data_source.jurisdiction
        
        if jurisdiction not in cls._systems:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"No ingestion system available for jurisdiction: {jurisdiction}")
            return None
        
        system_class = cls._systems[jurisdiction]
        
        try:
            return system_class(data_source)
        except Exception as e:
            if getattr(settings, "APP_ENV", None) != "test":
                logger.error(f"Error creating ingestion system for {jurisdiction}: {e}")
            return None
    
    @classmethod
    def register_system(cls, jurisdiction: str, system_class):
        """
        Register a new ingestion system for a jurisdiction.
        
        Args:
            jurisdiction: Jurisdiction code (e.g., 'US', 'CA')
            system_class: Class that implements BaseIngestionSystem
        """
        if not issubclass(system_class, BaseIngestionSystem):
            raise ValueError(f"{system_class} must inherit from BaseIngestionSystem")
        
        cls._systems[jurisdiction] = system_class
        if getattr(settings, "APP_ENV", None) != "test":
            logger.info(f"Registered ingestion system for jurisdiction: {jurisdiction}")
    
    @classmethod
    def get_supported_jurisdictions(cls) -> list:
        """Get list of supported jurisdictions."""
        return list(cls._systems.keys())

