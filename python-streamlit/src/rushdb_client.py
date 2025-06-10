import json
import random
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from rushdb import RushDB

class RushDBClient:
    """RushDB client for data operations"""

    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.client = None
        self.connect()

    def connect(self):
        """Connect to RushDB"""
        try:
            self.client = RushDB(
                api_key=self.config['api_token'],
                # base_url=self.config.get('base_url')
            )
        except Exception as e:
            raise Exception(f"Failed to connect to RushDB: {str(e)}")

    def test_connection(self) -> bool:
        """Test the RushDB connection"""
        try:
            # Try a simple query to test connection
            result = self.client.records.find({"limit": 1})
            return True
        except Exception as e:
            print(f"Connection test failed: {e}")
            return False

    def fetch_all_records(self, limit: int = 1000) -> tuple[List[Dict[str, Any]], int]:
        """Fetch all records from RushDB"""
        try:
            # Get the first batch to get total count
            result = self.client.records.find({
                "limit": min(100, limit),
                "offset": 0
            })

            # Extract data and total from the response
            if isinstance(result, dict) and 'data' in result:
                # New SDK format with data and total
                all_records = list(result['data'] or [])  # Ensure it's a list
                total = result.get('total', len(all_records))

                # If we need more records, fetch them
                if len(all_records) < limit and len(all_records) < total:
                    offset = 100
                    page_size = 100

                    while len(all_records) < limit and len(all_records) < total:
                        next_result = self.client.records.find({
                            "limit": min(page_size, limit - len(all_records)),
                            "offset": offset
                        })

                        if isinstance(next_result, dict) and 'data' in next_result:
                            next_data = list(next_result['data'] or [])  # Ensure it's a list
                        else:
                            next_data = list(next_result or [])  # Ensure it's a list

                        if not next_data:
                            break

                        all_records.extend(next_data)
                        offset += page_size

                        # Break if we got less than page_size (end of data)
                        if len(next_data) < page_size:
                            break

                return all_records, total
            else:
                # Legacy format - just a list
                all_records = list(result or [])  # Ensure it's a list
                offset = 100
                page_size = 100

                while len(all_records) < limit:
                    next_result = self.client.records.find({
                        "limit": min(page_size, limit - len(all_records)),
                        "offset": offset
                    })

                    if not next_result or len(next_result) == 0:
                        break

                    all_records.extend(list(next_result))  # Ensure it's a list
                    offset += page_size

                    # Break if we got less than page_size (end of data)
                    if len(next_result) < page_size:
                        break

                return all_records, len(all_records)

        except Exception as e:
            raise Exception(f"Failed to fetch records: {str(e)}")

    def fetch_records_by_label(self, labels: List[str], limit: int = 1000) -> List[Dict[str, Any]]:
        """Fetch records by specific labels"""
        try:
            result = self.client.records.find({
                "labels": labels,
                "limit": limit
            })
            # Handle both new SDK format and legacy format
            if isinstance(result, dict) and 'data' in result:
                return list(result['data'] or [])
            else:
                return list(result or [])
        except Exception as e:
            raise Exception(f"Failed to fetch records by label: {str(e)}")

    def search_records(self, query: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search records with custom query"""
        try:
            result = self.client.records.find(query)
            # Handle both new SDK format and legacy format
            if isinstance(result, dict) and 'data' in result:
                return list(result['data'] or [])
            else:
                return list(result or [])
        except Exception as e:
            raise Exception(f"Failed to search records: {str(e)}")

    def create_record(self, label: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a single record"""
        try:
            result = self.client.records.create(label=label, data=data)
            return result
        except Exception as e:
            raise Exception(f"Failed to create record: {str(e)}")

    def fetch_all_labels(self) -> List[str]:
        """Fetch all available labels from RushDB"""
        try:
            result = self.client.labels.list({})
            if result and 'data' in result:
                # Extract label names from the result
                labels = list(result['data'].keys())
                return labels
            elif result:
                # Legacy format - might be a direct list or dict
                if isinstance(result, dict):
                    return list(result.keys())
                else:
                    return list(result)
            return []
        except Exception as e:
            raise Exception(f"Failed to fetch labels: {str(e)}")

    def generate_sample_data(self) -> bool:
        """Generate sample data for demonstration"""
        try:
            # Sample data templates
            sample_data = [
                # Customer records
                {
                    "label": "Customer",
                    "data": {
                        "name": "Acme Corporation",
                        "industry": "Technology",
                        "size": "Large",
                        "revenue": 10000000,
                        "location": "San Francisco",
                        "country": "USA",
                        "founded": "2010-01-15",
                        "employees": 500,
                        "status": "Active"
                    }
                },
                {
                    "label": "Customer",
                    "data": {
                        "name": "Tech Innovations Ltd",
                        "industry": "Software",
                        "size": "Medium",
                        "revenue": 5000000,
                        "location": "Austin",
                        "country": "USA",
                        "founded": "2015-03-22",
                        "employees": 150,
                        "status": "Active"
                    }
                },
                # Product records
                {
                    "label": "Product",
                    "data": {
                        "name": "Database Pro",
                        "category": "Software",
                        "price": 299.99,
                        "version": "2.1.0",
                        "release_date": "2024-01-15",
                        "downloads": 15000,
                        "rating": 4.8,
                        "platform": "Cloud"
                    }
                },
                {
                    "label": "Product",
                    "data": {
                        "name": "Analytics Suite",
                        "category": "Software",
                        "price": 199.99,
                        "version": "1.5.2",
                        "release_date": "2024-02-01",
                        "downloads": 8500,
                        "rating": 4.6,
                        "platform": "Web"
                    }
                },
                # Transaction records
                {
                    "label": "Transaction",
                    "data": {
                        "customer_name": "Acme Corporation",
                        "product_name": "Database Pro",
                        "amount": 299.99,
                        "quantity": 1,
                        "date": "2024-01-20",
                        "payment_method": "Credit Card",
                        "status": "Completed",
                        "region": "North America"
                    }
                }
            ]

            # Generate additional random data
            for i in range(20):
                # Random customer
                customer_data = {
                    "label": "Customer",
                    "data": {
                        "name": f"Company {i+1}",
                        "industry": random.choice(["Technology", "Healthcare", "Finance", "Manufacturing", "Retail"]),
                        "size": random.choice(["Small", "Medium", "Large"]),
                        "revenue": random.randint(100000, 50000000),
                        "location": random.choice(["New York", "San Francisco", "Austin", "Seattle", "Boston"]),
                        "country": "USA",
                        "founded": f"{random.randint(2000, 2020)}-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                        "employees": random.randint(10, 2000),
                        "status": random.choice(["Active", "Inactive", "Prospect"])
                    }
                }
                sample_data.append(customer_data)

                # Random transaction
                transaction_data = {
                    "label": "Transaction",
                    "data": {
                        "customer_name": f"Company {i+1}",
                        "product_name": random.choice(["Database Pro", "Analytics Suite", "Mobile App Builder"]),
                        "amount": round(random.uniform(99.99, 999.99), 2),
                        "quantity": random.randint(1, 10),
                        "date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
                        "payment_method": random.choice(["Credit Card", "Bank Transfer", "PayPal"]),
                        "status": random.choice(["Completed", "Pending", "Failed"]),
                        "region": random.choice(["North America", "Europe", "Asia Pacific"])
                    }
                }
                sample_data.append(transaction_data)

            # Create records in batches
            for record in sample_data:
                self.create_record(record['label'], record['data'])

            return True

        except Exception as e:
            print(f"Failed to generate sample data: {e}")
            return False