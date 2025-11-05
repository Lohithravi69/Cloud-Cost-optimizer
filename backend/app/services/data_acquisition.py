"""
Data acquisition service for collecting cost data from cloud providers
"""
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
import asyncio
from concurrent.futures import ThreadPoolExecutor

from app.core.logging import get_logger
from app.services.aws_cost_explorer import aws_cost_service
from app.services.azure_cost_management import azure_cost_service
from app.services.gcp_billing import gcp_billing_service
from app.schemas.cost import CostDataCreate

logger = get_logger(__name__)


class DataAcquisitionService:
    """Service for acquiring cost data from multiple cloud providers"""

    def __init__(self):
        self.executor = ThreadPoolExecutor(max_workers=10)

    async def sync_all_providers(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        providers: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Synchronize cost data from all configured cloud providers

        Args:
            start_date: Start date for data collection (default: 30 days ago)
            end_date: End date for data collection (default: today)
            providers: List of providers to sync (default: all configured)

        Returns:
            Sync results summary
        """
        if start_date is None:
            start_date = datetime.utcnow() - timedelta(days=30)
        if end_date is None:
            end_date = datetime.utcnow()

        if providers is None:
            providers = ['aws', 'azure', 'gcp']

        logger.info("Starting data acquisition sync", providers=providers)

        results = {}
        tasks = []

        # Create async tasks for each provider
        for provider in providers:
            if provider.lower() == 'aws':
                task = self._sync_aws_data(start_date, end_date)
            elif provider.lower() == 'azure':
                task = self._sync_azure_data(start_date, end_date)
            elif provider.lower() == 'gcp':
                task = self._sync_gcp_data(start_date, end_date)
            else:
                logger.warning("Unknown provider", provider=provider)
                continue

            tasks.append(task)

        # Execute all tasks concurrently
        completed_results = await asyncio.gather(*tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(completed_results):
            provider = providers[i]
            if isinstance(result, Exception):
                logger.error("Provider sync failed", provider=provider, error=str(result))
                results[provider] = {
                    'status': 'error',
                    'error': str(result),
                    'records_processed': 0
                }
            else:
                results[provider] = result

        total_records = sum(r.get('records_processed', 0) for r in results.values())

        logger.info("Data acquisition sync completed", total_records=total_records)

        return {
            'status': 'completed',
            'total_records_processed': total_records,
            'provider_results': results,
            'sync_period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat()
            }
        }

    async def _sync_aws_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Sync AWS cost data"""
        try:
            logger.info("Syncing AWS cost data")

            # Run AWS API calls in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            cost_data = await loop.run_in_executor(
                self.executor,
                lambda: aws_cost_service.get_cost_and_usage(
                    start_date=start_date,
                    end_date=end_date,
                    granularity='DAILY',
                    group_by=['SERVICE', 'REGION']
                )
            )

            # Process and store the data
            processed_records = await self._process_and_store_cost_data(cost_data, 'aws')

            return {
                'status': 'success',
                'records_processed': processed_records,
                'provider': 'aws'
            }

        except Exception as e:
            logger.error("AWS sync failed", error=str(e))
            raise

    async def _sync_azure_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Sync Azure cost data"""
        try:
            logger.info("Syncing Azure cost data")

            # Run Azure API calls in thread pool
            loop = asyncio.get_event_loop()
            cost_data = await loop.run_in_executor(
                self.executor,
                lambda: azure_cost_service.get_cost_data(
                    start_date=start_date,
                    end_date=end_date,
                    granularity='Daily',
                    group_by=['ServiceName', 'ResourceGroupName']
                )
            )

            # Process and store the data
            processed_records = await self._process_and_store_cost_data(cost_data, 'azure')

            return {
                'status': 'success',
                'records_processed': processed_records,
                'provider': 'azure'
            }

        except Exception as e:
            logger.error("Azure sync failed", error=str(e))
            raise

    async def _sync_gcp_data(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Sync GCP cost data"""
        try:
            logger.info("Syncing GCP cost data")

            # Run GCP API calls in thread pool
            loop = asyncio.get_event_loop()
            cost_data = await loop.run_in_executor(
                self.executor,
                lambda: gcp_billing_service.get_cost_data(
                    start_date=start_date,
                    end_date=end_date,
                    granularity='DAILY',
                    group_by=['service', 'region']
                )
            )

            # Process and store the data
            processed_records = await self._process_and_store_cost_data(cost_data, 'gcp')

            return {
                'status': 'success',
                'records_processed': processed_records,
                'provider': 'gcp'
            }

        except Exception as e:
            logger.error("GCP sync failed", error=str(e))
            raise

    async def _process_and_store_cost_data(
        self,
        raw_cost_data: List[Dict[str, Any]],
        provider: str
    ) -> int:
        """
        Process raw cost data and store it in the database

        Args:
            raw_cost_data: Raw cost data from provider
            provider: Cloud provider name

        Returns:
            Number of records processed
        """
        processed_count = 0

        for item in raw_cost_data:
            try:
                # Transform raw data to our schema format
                cost_record = CostDataCreate(
                    provider=provider,
                    service=item.get('dimensions', {}).get('service', 'Unknown'),
                    region=item.get('dimensions', {}).get('region', 'Unknown'),
                    resource_id=item.get('dimensions', {}).get('resource_id'),
                    cost_amount=item['cost_amount'],
                    cost_currency=item['cost_currency'],
                    usage_quantity=item.get('usage_quantity'),
                    usage_unit=item.get('usage_unit'),
                    start_date=datetime.fromisoformat(item['start_date']) if item.get('start_date') else datetime.utcnow(),
                    end_date=datetime.fromisoformat(item['end_date']) if item.get('end_date') else datetime.utcnow(),
                    tags=item.get('dimensions', {}),
                    metadata={
                        'raw_data': item,
                        'processed_at': datetime.utcnow().isoformat()
                    }
                )

                # Here we would typically save to database
                # For now, just log the record
                logger.debug("Processed cost record", record=cost_record.dict())

                processed_count += 1

            except Exception as e:
                logger.error("Failed to process cost record", error=str(e), item=item)
                continue

        return processed_count

    async def get_sync_status(self) -> Dict[str, Any]:
        """Get the current sync status"""
        # This would typically check database for last sync times
        return {
            'last_sync': None,  # Would be populated from DB
            'next_scheduled_sync': None,
            'sync_in_progress': False
        }

    def schedule_recurring_sync(self, interval_hours: int = 24):
        """Schedule recurring data sync (would use Celery or similar)"""
        logger.info("Scheduling recurring sync", interval_hours=interval_hours)
        # Implementation would use Celery beat or similar scheduling system
        pass


# Global service instance
data_acquisition_service = DataAcquisitionService()
