"""
AWS Cost Explorer API integration service
"""
import boto3
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.cost import CostDataCreate

logger = get_logger(__name__)


class AWSCostExplorerService:
    """Service for interacting with AWS Cost Explorer API"""

    def __init__(self):
        self.client = boto3.client(
            'ce',
            region_name='us-east-1'  # Cost Explorer is only available in us-east-1
        )

    def get_cost_and_usage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'DAILY',
        group_by: Optional[List[str]] = None,
        filter_dimensions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cost and usage data from AWS Cost Explorer

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: Dimensions to group by (SERVICE, AZ, etc.)
            filter_dimensions: Filters to apply

        Returns:
            List of cost and usage data points
        """
        try:
            # Build the request parameters
            params = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': granularity,
                'Metrics': ['BlendedCost', 'UsageQuantity'],
                'GroupBy': []
            }

            # Add group by dimensions
            if group_by:
                for dimension in group_by:
                    params['GroupBy'].append({'Type': 'DIMENSION', 'Key': dimension})

            # Add filters if provided
            if filter_dimensions:
                params['Filter'] = self._build_filter_expression(filter_dimensions)

            logger.info("Fetching AWS cost data", params=params)

            # Make the API call
            response = self.client.get_cost_and_usage(**params)

            # Process and return the results
            return self._process_cost_response(response)

        except Exception as e:
            logger.error("Failed to fetch AWS cost data", error=str(e))
            raise

    def get_cost_forecast(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'MONTHLY'
    ) -> Dict[str, Any]:
        """
        Get cost forecast from AWS Cost Explorer

        Args:
            start_date: Start date for forecast
            end_date: End date for forecast
            granularity: Forecast granularity

        Returns:
            Forecast data
        """
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': granularity,
                'Metric': 'BLENDED_COST'
            }

            logger.info("Fetching AWS cost forecast", params=params)

            response = self.client.get_cost_forecast(**params)

            return self._process_forecast_response(response)

        except Exception as e:
            logger.error("Failed to fetch AWS cost forecast", error=str(e))
            raise

    def get_reservation_coverage(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'MONTHLY'
    ) -> Dict[str, Any]:
        """
        Get reservation coverage data

        Args:
            start_date: Start date for coverage data
            end_date: End date for coverage data
            granularity: Coverage granularity

        Returns:
            Reservation coverage data
        """
        try:
            params = {
                'TimePeriod': {
                    'Start': start_date.strftime('%Y-%m-%d'),
                    'End': end_date.strftime('%Y-%m-%d')
                },
                'Granularity': granularity,
                'Metrics': ['CoverageHoursPercentage', 'OnDemandCost', 'ReservedHours']
            }

            logger.info("Fetching AWS reservation coverage", params=params)

            response = self.client.get_reservation_coverage(**params)

            return self._process_coverage_response(response)

        except Exception as e:
            logger.error("Failed to fetch AWS reservation coverage", error=str(e))
            raise

    def _build_filter_expression(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build AWS Cost Explorer filter expression"""
        filter_expression = {}

        # Handle service filters
        if 'services' in filters:
            filter_expression = {
                'Dimensions': {
                    'Key': 'SERVICE',
                    'Values': filters['services']
                }
            }

        # Handle region filters
        if 'regions' in filters:
            if filter_expression:
                filter_expression = {
                    'And': [
                        filter_expression,
                        {
                            'Dimensions': {
                                'Key': 'REGION',
                                'Values': filters['regions']
                            }
                        }
                    ]
                }
            else:
                filter_expression = {
                    'Dimensions': {
                        'Key': 'REGION',
                        'Values': filters['regions']
                    }
                }

        return filter_expression

    def _process_cost_response(self, response: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Cost Explorer API response"""
        results = []

        for result in response.get('ResultsByTime', []):
            start_date = result['TimePeriod']['Start']
            end_date = result['TimePeriod']['End']

            for group in result.get('Groups', []):
                cost_data = {
                    'start_date': start_date,
                    'end_date': end_date,
                    'cost_amount': Decimal(group['Metrics']['BlendedCost']['Amount']),
                    'cost_currency': group['Metrics']['BlendedCost']['Unit'],
                    'usage_quantity': Decimal(group['Metrics']['UsageQuantity']['Amount']) if 'UsageQuantity' in group['Metrics'] else None,
                    'usage_unit': group['Metrics']['UsageQuantity']['Unit'] if 'UsageQuantity' in group['Metrics'] else None,
                    'dimensions': {}
                }

                # Extract dimension values
                for dimension in group.get('Keys', []):
                    if 'SERVICE' in dimension:
                        cost_data['dimensions']['service'] = dimension
                    elif 'REGION' in dimension:
                        cost_data['dimensions']['region'] = dimension
                    elif 'AZ' in dimension:
                        cost_data['dimensions']['availability_zone'] = dimension

                results.append(cost_data)

        return results

    def _process_forecast_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process forecast API response"""
        forecast_data = []

        for result in response.get('ResultsByTime', []):
            forecast_data.append({
                'start_date': result['TimePeriod']['Start'],
                'end_date': result['TimePeriod']['End'],
                'forecast_amount': Decimal(result['Groups'][0]['Metrics']['BLENDED_COST']['Amount']),
                'forecast_currency': result['Groups'][0]['Metrics']['BLENDED_COST']['Unit']
            })

        return {
            'forecast_data': forecast_data,
            'total_forecast': sum(item['forecast_amount'] for item in forecast_data)
        }

    def _process_coverage_response(self, response: Dict[str, Any]) -> Dict[str, Any]:
        """Process reservation coverage response"""
        coverage_data = []

        for result in response.get('ResultsByTime', []):
            coverage_data.append({
                'start_date': result['TimePeriod']['Start'],
                'end_date': result['TimePeriod']['End'],
                'coverage_percentage': Decimal(result['Groups'][0]['Metrics']['CoverageHoursPercentage']['Amount']),
                'on_demand_cost': Decimal(result['Groups'][0]['Metrics']['OnDemandCost']['Amount']),
                'reserved_hours': Decimal(result['Groups'][0]['Metrics']['ReservedHours']['Amount'])
            })

        return {
            'coverage_data': coverage_data,
            'average_coverage': sum(item['coverage_percentage'] for item in coverage_data) / len(coverage_data) if coverage_data else 0
        }


# Global service instance
aws_cost_service = AWSCostExplorerService()
