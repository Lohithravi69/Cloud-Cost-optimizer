"""
Cloud provider service factory and interfaces
"""
from typing import Optional

from app.core.config import settings


class CloudProviderService:
    """
    Factory for cloud provider services
    """

    @staticmethod
    def get_provider(provider_name: str) -> Optional[object]:
        """
        Get provider service instance based on provider name

        Args:
            provider_name: Name of the cloud provider (aws, azure, gcp)

        Returns:
            Provider service instance or None if not supported
        """
        # TODO: Implement actual provider services
        # For now, return placeholder
        providers = {
            "aws": None,  # AWSProvider(access_key=settings.AWS_ACCESS_KEY_ID, ...)
            "azure": None,  # AzureProvider(...)
            "gcp": None,  # GCPProvider(...)
        }

        return providers.get(provider_name.lower())


def get_provider_service(provider_name: str) -> Optional[object]:
    """
    Convenience function to get provider service

    Args:
        provider_name: Name of the cloud provider

    Returns:
        Provider service instance or None
    """
    return CloudProviderService.get_provider(provider_name)
