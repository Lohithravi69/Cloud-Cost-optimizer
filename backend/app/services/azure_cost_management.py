"""
Azure Cost Management API integration service
"""
import requests
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal
import json

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.cost import CostDataCreate

logger = get_logger(__name__)


class AzureCostManagementService:
    """Service for interacting with Azure Cost Management API"""

    def __init__(self):
        self.base_url = "https://management.azure.com"
        self.api_version = "2023-03-01"
        # These would be set from environment variables or config
        self.subscription_id = getattr(settings, 'AZURE_SUBSCRIPTION_ID', None)
        self.client_id = getattr(settings, 'AZURE_CLIENT_ID', None)
        self.client_secret = getattr(settings, 'AZURE_CLIENT_SECRET', None)
        self.tenant_id = getattr(settings, 'AZURE_TENANT_ID', None)
        self.access_token = None

    def _get_access_token(self) -> str:
        """Get Azure access token using service principal"""
        if self.access_token:
            return self.access_token

        token_url = f"https://login.microsoftonline.com/{self.tenant_id}/oauth2/v2.0/token"

        data = {
            'grant_type': 'client_credentials',
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'scope': 'https://management.azure.com/.default'
        }

        response = requests.post(token_url, data=data)
        response.raise_for_status()

        self.access_token = response.json()['access_token']
        return self.access_token

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'Daily',
        group_by: Optional[List[str]] = None,
        filter_dimensions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cost data from Azure Cost Management

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: Daily, Monthly, or Hourly
            group_by: Dimensions to group by
            filter_dimensions: Filters to apply

        Returns:
            List of cost data points
        """
        try:
            token = self._get_access_token()

            url = f"{self.base_url}/subscriptions/{self.subscription_id}/providers/Microsoft.CostManagement/query"
            url += f"?api-version={self.api_version}"

            # Build the query payload
            query_payload = self._build_cost_query(
                start_date, end_date, granularity, group_by, filter_dimensions
            )

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            logger.info("Fetching Azure cost data", subscription_id=self.subscription_id)

            response = requests.post(url, headers=headers, json=query_payload)
            response.raise_for_status()

            data = response.json()
            return self._process_cost_response(data)

        except Exception as e:
            logger.error("Failed to fetch Azure cost data", error=str(e))
            raise

    def get_budget_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve budget data from Azure

        Returns:
            List of budget configurations
        """
        try:
            token = self._get_access_token()

            url = f"{self.base_url}/subscriptions/{self.subscription_id}/providers/Microsoft.Consumption/budgets"
            url += f"?api-version={self.api_version}"

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            return self._process_budget_response(data)

        except Exception as e:
            logger.error("Failed to fetch Azure budget data", error=str(e))
            raise

    def get_reservation_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve reservation data from Azure

        Returns:
            List of reservation details
        """
        try:
            token = self._get_access_token()

            url = f"{self.base_url}/providers/Microsoft.Capacity/reservations"
            url += f"?api-version={self.api_version}"

            headers = {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json'
            }

            response = requests.get(url, headers=headers)
            response.raise_for_status()

            data = response.json()
            return self._process_reservation_response(data)

        except Exception as e:
            logger.error("Failed to fetch Azure reservation data", error=str(e))
            raise

    def _build_cost_query(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
        group_by: Optional[List[str]],
        filter_dimensions: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """Build Azure Cost Management query payload"""
        query = {
            "type": "ActualCost",
            "timeframe": "Custom",
            "timePeriod": {
                "from": start_date.strftime('%Y-%m-%dT%H:%M:%SZ'),
                "to": end_date.strftime('%Y-%m-%dT%H:%M:%SZ')
            },
            "dataset": {
                "granularity": granularity,
                "aggregation": {
                    "totalCost": {
                        "name": "Cost",
                        "function": "Sum"
                    },
                    "totalCostUSD": {
                        "name": "CostUSD",
                        "function": "Sum"
                    }
                },
                "grouping": []
            }
        }

        # Add grouping
        if group_by:
            for dimension in group_by:
                query["dataset"]["grouping"].append({
                    "type": "Dimension",
                    "name": dimension
                })

        # Add filtering
        if filter_dimensions:
            query["dataset"]["filter"] = self._build_filter_expression(filter_dimensions)

        return query

    def _build_filter_expression(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """Build Azure filter expression"""
        filter_expression = {
            "Dimensions": {
                "Name": "ResourceGroupName",
                "Operator": "In",
                "Values": filters.get('resource_groups', [])
            }
        }

        # Add service filters
        if 'services' in filters:
            filter_expression = {
                "And": [
                    filter_expression,
                    {
                        "Dimensions": {
                            "Name": "ServiceName",
                            "Operator": "In",
                            "Values": filters['services']
                        }
                    }
                ]
            }

        return filter_expression

    def _process_cost_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Azure Cost Management API response"""
        results = []

        for row in data.get('properties', {}).get('rows', []):
            # Azure returns data in a specific column order
            # This is a simplified processing - actual column mapping would depend on the query
            cost_data = {
                'start_date': row[0] if len(row) > 0 else None,
                'end_date': row[1] if len(row) > 1 else None,
                'cost_amount': Decimal(str(row[2])) if len(row) > 2 else Decimal('0'),
                'cost_currency': 'USD',  # Azure typically returns in USD
                'usage_quantity': None,  # Azure doesn't always provide usage quantity
                'usage_unit': None,
                'dimensions': {}
            }

            # Extract dimension values from columns
            if len(row) > 3:
                for i, col in enumerate(row[3:], 3):
                    if col and isinstance(col, str):
                        if 'resource' in col.lower():
                            cost_data['dimensions']['resource_id'] = col
                        elif 'service' in col.lower():
                            cost_data['dimensions']['service'] = col
                        elif 'location' in col.lower():
                            cost_data['dimensions']['region'] = col

            results.append(cost_data)

        return results

    def _process_budget_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Azure budget API response"""
        budgets = []

        for budget in data.get('value', []):
            budgets.append({
                'name': budget['name'],
                'amount': Decimal(str(budget['properties']['amount'])),
                'currency': budget['properties']['currency'],
                'time_grain': budget['properties']['timeGrain'],
                'start_date': budget['properties']['timePeriod']['startDate'],
                'end_date': budget['properties']['timePeriod']['endDate'],
                'notifications': budget['properties'].get('notifications', {})
            })

        return budgets

    def _process_reservation_response(self, data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Process Azure reservation API response"""
        reservations = []

        for reservation in data.get('value', []):
            reservations.append({
                'reservation_id': reservation['id'],
                'name': reservation['name'],
                'type': reservation['type'],
                'location': reservation['location'],
                'capacity': reservation.get('properties', {}).get('capacity', {}),
                'provisioning_state': reservation.get('properties', {}).get('provisioningState')
            })

        return reservations


# Global service instance
azure_cost_service = AzureCostManagementService()
