"""
Google Cloud Billing API integration service
"""
from google.cloud import billing_v1
from google.cloud import bigquery
from google.oauth2 import service_account
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from decimal import Decimal

from app.core.config import settings
from app.core.logging import get_logger
from app.schemas.cost import CostDataCreate

logger = get_logger(__name__)


class GCPBillingService:
    """Service for interacting with Google Cloud Billing API"""

    def __init__(self):
        # These would be set from environment variables or config
        self.project_id = getattr(settings, 'GCP_PROJECT_ID', None)
        self.billing_account_id = getattr(settings, 'GCP_BILLING_ACCOUNT_ID', None)
        self.credentials_path = getattr(settings, 'GCP_CREDENTIALS_PATH', None)

        # Initialize clients
        self.billing_client = None
        self.bq_client = None

        if self.credentials_path:
            credentials = service_account.Credentials.from_service_account_file(
                self.credentials_path
            )
            self.billing_client = billing_v1.CloudBillingClient(credentials=credentials)
            self.bq_client = bigquery.Client(
                project=self.project_id,
                credentials=credentials
            )

    def get_cost_data(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str = 'DAILY',
        group_by: Optional[List[str]] = None,
        filter_dimensions: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Retrieve cost data from Google Cloud Billing

        Args:
            start_date: Start date for cost data
            end_date: End date for cost data
            granularity: DAILY, MONTHLY, or HOURLY
            group_by: Dimensions to group by
            filter_dimensions: Filters to apply

        Returns:
            List of cost data points
        """
        try:
            if not self.bq_client:
                raise ValueError("BigQuery client not initialized. Check GCP credentials.")

            # Build BigQuery query for billing data
            query = self._build_billing_query(
                start_date, end_date, granularity, group_by, filter_dimensions
            )

            logger.info("Fetching GCP cost data", project_id=self.project_id)

            # Execute query
            query_job = self.bq_client.query(query)
            results = query_job.result()

            # Process results
            return self._process_billing_results(results)

        except Exception as e:
            logger.error("Failed to fetch GCP cost data", error=str(e))
            raise

    def get_budget_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve budget data from Google Cloud

        Returns:
            List of budget configurations
        """
        try:
            if not self.billing_client:
                raise ValueError("Billing client not initialized. Check GCP credentials.")

            budgets = []

            # List all budgets for the billing account
            request = billing_v1.ListBudgetsRequest(
                parent=f"billingAccounts/{self.billing_account_id}"
            )

            for budget in self.billing_client.list_budgets(request=request):
                budgets.append({
                    'name': budget.name,
                    'display_name': budget.display_name,
                    'amount': Decimal(str(budget.amount.specified_amount.units)) + Decimal(str(budget.amount.specified_amount.nanos)) / Decimal('1000000000'),
                    'currency': budget.amount.specified_amount.currency_code,
                    'budget_filter': budget.budget_filter,
                    'threshold_rules': [
                        {
                            'threshold_percent': rule.threshold_percent,
                            'spend_basis': rule.spend_basis
                        } for rule in budget.threshold_rules
                    ]
                })

            return budgets

        except Exception as e:
            logger.error("Failed to fetch GCP budget data", error=str(e))
            raise

    def get_reservation_data(self) -> List[Dict[str, Any]]:
        """
        Retrieve reservation data from Google Cloud

        Returns:
            List of reservation details
        """
        try:
            if not self.bq_client:
                raise ValueError("BigQuery client not initialized. Check GCP credentials.")

            # Query for reservations (Compute Engine reservations)
            query = """
            SELECT
                name,
                zone,
                specificReservation.name as reservation_name,
                specificReservation.count as vm_count,
                specificReservation.instanceProperties.machineType as machine_type,
                creationTimestamp
            FROM `compute.googleapis.com/reservations`
            WHERE DATE(creationTimestamp) >= DATE_SUB(CURRENT_DATE(), INTERVAL 365 DAY)
            """

            query_job = self.bq_client.query(query)
            results = query_job.result()

            reservations = []
            for row in results:
                reservations.append({
                    'name': row.name,
                    'zone': row.zone,
                    'reservation_name': row.reservation_name,
                    'vm_count': row.vm_count,
                    'machine_type': row.machine_type,
                    'creation_timestamp': row.creationTimestamp
                })

            return reservations

        except Exception as e:
            logger.error("Failed to fetch GCP reservation data", error=str(e))
            raise

    def _build_billing_query(
        self,
        start_date: datetime,
        end_date: datetime,
        granularity: str,
        group_by: Optional[List[str]],
        filter_dimensions: Optional[Dict[str, Any]]
    ) -> str:
        """Build BigQuery for GCP billing data"""
        # GCP billing data is typically stored in BigQuery dataset
        dataset = f"`{self.project_id}.billing_export.gcp_billing_export_v1_*`"

        # Base query
        query = f"""
        SELECT
            DATE(usage_start_time) as usage_date,
            service.description as service,
            location.region as region,
            resource.name as resource_name,
            SUM(cost) as total_cost,
            SUM(usage.amount) as usage_amount,
            usage.unit as usage_unit
        FROM {dataset}
        WHERE DATE(usage_start_time) BETWEEN '{start_date.strftime('%Y-%m-%d')}' AND '{end_date.strftime('%Y-%m-%d')}'
        """

        # Add grouping
        if group_by:
            group_columns = []
            for dimension in group_by:
                if dimension.lower() == 'service':
                    group_columns.append('service.description')
                elif dimension.lower() == 'region':
                    group_columns.append('location.region')
                elif dimension.lower() == 'resource':
                    group_columns.append('resource.name')

            if group_columns:
                query += f"\nGROUP BY {', '.join(group_columns + ['DATE(usage_start_time)'])}"
            else:
                query += "\nGROUP BY DATE(usage_start_time), service.description, location.region, resource.name"
        else:
            query += "\nGROUP BY DATE(usage_start_time), service.description, location.region, resource.name"

        # Add filtering
        if filter_dimensions:
            conditions = []

            if 'services' in filter_dimensions:
                services = "', '".join(filter_dimensions['services'])
                conditions.append(f"service.description IN ('{services}')")

            if 'regions' in filter_dimensions:
                regions = "', '".join(filter_dimensions['regions'])
                conditions.append(f"location.region IN ('{regions}')")

            if conditions:
                query += f"\nAND {' AND '.join(conditions)}"

        query += "\nORDER BY usage_date DESC"

        return query

    def _process_billing_results(self, results) -> List[Dict[str, Any]]:
        """Process BigQuery billing results"""
        cost_data = []

        for row in results:
            cost_data.append({
                'start_date': row.usage_date.isoformat() if row.usage_date else None,
                'end_date': row.usage_date.isoformat() if row.usage_date else None,
                'cost_amount': Decimal(str(row.total_cost)) if row.total_cost else Decimal('0'),
                'cost_currency': 'USD',  # GCP billing is typically in USD
                'usage_quantity': Decimal(str(row.usage_amount)) if row.usage_amount else None,
                'usage_unit': row.usage_unit,
                'dimensions': {
                    'service': row.service,
                    'region': row.region,
                    'resource_name': row.resource_name
                }
            })

        return cost_data

    def get_cost_forecast(
        self,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Get cost forecast using historical data analysis

        Args:
            start_date: Start date for forecast
            end_date: End date for forecast

        Returns:
            Forecast data based on historical trends
        """
        try:
            if not self.bq_client:
                raise ValueError("BigQuery client not initialized.")

            # Simple forecasting based on average daily costs
            query = f"""
            SELECT
                DATE(usage_start_time) as usage_date,
                SUM(cost) as daily_cost
            FROM `{self.project_id}.billing_export.gcp_billing_export_v1_*`
            WHERE DATE(usage_start_time) >= DATE_SUB(CURRENT_DATE(), INTERVAL 90 DAY)
            GROUP BY DATE(usage_start_time)
            ORDER BY usage_date DESC
            """

            query_job = self.bq_client.query(query)
            results = query_job.result()

            # Calculate average daily cost
            total_cost = 0
            days_count = 0

            for row in results:
                total_cost += float(row.daily_cost)
                days_count += 1

            avg_daily_cost = total_cost / days_count if days_count > 0 else 0

            # Calculate forecast period
            forecast_days = (end_date - start_date).days
            forecast_amount = avg_daily_cost * forecast_days

            return {
                'forecast_amount': Decimal(str(forecast_amount)),
                'forecast_currency': 'USD',
                'forecast_period_days': forecast_days,
                'average_daily_cost': Decimal(str(avg_daily_cost)),
                'confidence_level': 'LOW'  # Simple average-based forecast
            }

        except Exception as e:
            logger.error("Failed to generate GCP cost forecast", error=str(e))
            raise


# Global service instance
gcp_billing_service = GCPBillingService()
