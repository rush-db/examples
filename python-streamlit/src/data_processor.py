import pandas as pd
import numpy as np
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime, date
import json

class DataProcessor:
    """Data processing utilities for RushDB data"""

    def __init__(self):
        pass

    def get_unique_labels(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get unique labels from the data"""
        labels = set()
        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'label'):
                # Record object format
                label = record.label or "EMPTY"
            elif isinstance(record, dict):
                # Dictionary format
                label = record.get('label', record.get('__label', 'EMPTY'))
            else:
                label = "EMPTY"
            labels.add(label)
        return sorted(list(labels))

    def get_label_distribution(self, data: List[Dict[str, Any]]) -> Dict[str, int]:
        """Get distribution of labels"""
        label_counts = {}
        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'label'):
                # Record object format
                label = record.label or "EMPTY"
            elif isinstance(record, dict):
                # Dictionary format
                label = record.get('label', record.get('__label', 'EMPTY'))
            else:
                label = "EMPTY"
            label_counts[label] = label_counts.get(label, 0) + 1
        return label_counts

    def get_all_properties(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get all unique properties from the data"""
        properties = set()
        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'data'):
                # Record object format
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                record_data = record
            else:
                record_data = {}

            if isinstance(record_data, dict):
                properties.update(record_data.keys())
        return sorted(list(properties))

    def get_filterable_properties(self, data: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
        """Get properties suitable for filtering with their metadata"""
        properties = {}

        # Collect all property values
        property_values = {}
        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'data'):
                # Record object format
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                record_data = record
            else:
                record_data = {}

            if isinstance(record_data, dict):
                for key, value in record_data.items():
                    if key not in property_values:
                        property_values[key] = []
                    property_values[key].append(value)

        # Analyze each property
        for prop_name, values in property_values.items():
            # Filter out None values
            non_none_values = [v for v in values if v is not None]

            if not non_none_values:
                continue

            # Determine property type and characteristics
            prop_info = self._analyze_property(prop_name, non_none_values)
            if prop_info:
                properties[prop_name] = prop_info

        return properties

    def _analyze_property(self, prop_name: str, values: List[Any]) -> Optional[Dict[str, Any]]:
        """Analyze a property to determine its type and filtering options"""
        if not values:
            return None

        # Check for string type
        string_values = [v for v in values if isinstance(v, str)]
        if len(string_values) > len(values) * 0.8:  # 80% are strings
            unique_values = list(set(string_values))
            value_counts = {}
            for val in string_values:
                value_counts[val] = value_counts.get(val, 0) + 1

            return {
                'type': 'string',
                'unique_values': unique_values[:100],  # Limit for performance
                'value_counts': dict(sorted(value_counts.items(), key=lambda x: x[1], reverse=True)[:50]),
                'total_unique': len(unique_values)
            }

        # Check for numeric type
        numeric_values = []
        for v in values:
            if isinstance(v, (int, float)):
                numeric_values.append(float(v))
            elif isinstance(v, str):
                try:
                    numeric_values.append(float(v))
                except ValueError:
                    pass

        if len(numeric_values) > len(values) * 0.8:  # 80% are numeric
            return {
                'type': 'number',
                'range': (min(numeric_values), max(numeric_values)),
                'mean': np.mean(numeric_values),
                'std': np.std(numeric_values)
            }

        # Check for date type
        date_values = []
        for v in values:
            if isinstance(v, (date, datetime)):
                date_values.append(v.date() if isinstance(v, datetime) else v)
            elif isinstance(v, str):
                try:
                    parsed_date = datetime.strptime(v, '%Y-%m-%d').date()
                    date_values.append(parsed_date)
                except ValueError:
                    try:
                        parsed_date = datetime.strptime(v, '%Y-%m-%d %H:%M:%S').date()
                        date_values.append(parsed_date)
                    except ValueError:
                        pass

        if len(date_values) > len(values) * 0.6:  # 60% are dates
            return {
                'type': 'date',
                'range': (min(date_values), max(date_values))
            }

        # Default to string if we can't determine type
        unique_values = list(set([str(v) for v in values]))
        if len(unique_values) <= 50:  # Only if reasonable number of unique values
            return {
                'type': 'string',
                'unique_values': unique_values,
                'value_counts': {},
                'total_unique': len(unique_values)
            }

        return None

    def get_date_properties(self, data: List[Dict[str, Any]]) -> List[str]:
        """Get properties that contain date values"""
        properties = self.get_filterable_properties(data)
        return [prop for prop, info in properties.items() if info['type'] == 'date']

    def get_time_series_data(self, data: List[Dict[str, Any]], date_property: str) -> List[Dict[str, Any]]:
        """Get time series data for a specific date property"""
        date_counts = {}

        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'data'):
                # Record object format
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                record_data = record
            else:
                record_data = {}

            if isinstance(record_data, dict) and date_property in record_data:
                date_value = record_data[date_property]

                # Parse date
                parsed_date = None
                if isinstance(date_value, (date, datetime)):
                    parsed_date = date_value.date() if isinstance(date_value, datetime) else date_value
                elif isinstance(date_value, str):
                    try:
                        parsed_date = datetime.strptime(date_value, '%Y-%m-%d').date()
                    except ValueError:
                        try:
                            parsed_date = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S').date()
                        except ValueError:
                            continue

                if parsed_date:
                    date_str = parsed_date.strftime('%Y-%m-%d')
                    date_counts[date_str] = date_counts.get(date_str, 0) + 1

        # Convert to list of dicts for plotting
        time_series = []
        for date_str, count in sorted(date_counts.items()):
            time_series.append({'date': date_str, 'count': count})

        return time_series

    def get_relationship_data(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Get records that have relationship data"""
        relationship_records = []

        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'data'):
                # Record object format
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                record_data = record
            else:
                record_data = {}

            if isinstance(record_data, dict) and ('relationships' in record_data or 'relations' in record_data):
                relationship_records.append(record)

        return relationship_records

    def apply_filters(self, data: List[Dict[str, Any]], filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Apply filters to the data"""
        filtered_data = data.copy()

        for filter_name, filter_value in filters.items():
            if not filter_value:  # Skip empty filters
                continue

            if filter_name == 'labels':
                # Label filter
                if filter_value:
                    temp_filtered = []
                    for record in filtered_data:
                        # Handle Record objects and dict objects
                        if hasattr(record, 'label'):
                            # Record object format
                            label = record.label
                        elif isinstance(record, dict):
                            # Dictionary format
                            label = record.get('label', record.get('__label'))
                        else:
                            label = None

                        if label in filter_value:
                            temp_filtered.append(record)
                    filtered_data = temp_filtered
            else:
                # Property filters
                filtered_data = self._apply_property_filter(filtered_data, filter_name, filter_value)

        return filtered_data

    def _apply_property_filter(self, data: List[Dict[str, Any]], prop_name: str, filter_value: Any) -> List[Dict[str, Any]]:
        """Apply a specific property filter"""
        filtered_data = []

        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'data'):
                # Record object format
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                record_data = record
            else:
                record_data = {}

            if prop_name not in record_data:
                continue

            prop_value = record_data[prop_name]

            # Handle different filter types
            if isinstance(filter_value, list) and filter_value:
                # Multi-select filter
                if str(prop_value) in [str(v) for v in filter_value]:
                    filtered_data.append(record)
            elif isinstance(filter_value, tuple) and len(filter_value) == 2:
                # Range filter (numeric or date)
                min_val, max_val = filter_value

                # Try numeric comparison
                try:
                    numeric_value = float(prop_value)
                    if min_val <= numeric_value <= max_val:
                        filtered_data.append(record)
                    continue
                except (ValueError, TypeError):
                    pass

                # Try date comparison
                try:
                    if isinstance(prop_value, str):
                        prop_date = datetime.strptime(prop_value, '%Y-%m-%d').date()
                    elif isinstance(prop_value, datetime):
                        prop_date = prop_value.date()
                    elif isinstance(prop_value, date):
                        prop_date = prop_value
                    else:
                        continue

                    if min_val <= prop_date <= max_val:
                        filtered_data.append(record)
                except (ValueError, TypeError):
                    pass
            else:
                # Direct value filter
                if prop_value == filter_value:
                    filtered_data.append(record)

        return filtered_data

    def to_dataframe(self, data: List[Dict[str, Any]]) -> pd.DataFrame:
        """Convert RushDB records to a pandas DataFrame"""
        if not data:
            return pd.DataFrame()

        # Debug: Check data structure
        print(f"to_dataframe received data type: {type(data)}")
        if data:
            print(f"First element type: {type(data[0])}")
            if hasattr(data[0], '__dict__'):
                print(f"First element attributes: {list(data[0].__dict__.keys()) if hasattr(data[0], '__dict__') else 'No __dict__'}")

        # Flatten any nested lists that might have been created
        flat_data = []
        for item in data:
            if isinstance(item, list):
                # If we have nested lists, flatten them
                flat_data.extend(item)
            else:
                flat_data.append(item)

        # Use the flattened data
        data = flat_data

        # Flatten the data structure
        flattened_data = []

        for record in data:
            # Handle Record objects and dict objects
            if hasattr(record, 'id'):
                # Record object format
                flat_record = {
                    'id': record.id or '',
                    'label': record.label or '',
                    'created_at': getattr(record, 'created_at', ''),
                    'updated_at': getattr(record, 'updated_at', '')
                }
                record_data = record.data
            elif isinstance(record, dict):
                # Dictionary format
                flat_record = {
                    'id': record.get('__id', record.get('id', '')),
                    'label': record.get('__label', record.get('label', '')),
                    'created_at': record.get('timestamp', record.get('created_at', '')),
                    'updated_at': record.get('timestamp', record.get('updated_at', ''))
                }
                record_data = record
            else:
                # Unknown format, skip
                print(f"Warning: Unknown record format: {type(record)}")
                continue

            # Add data properties
            if isinstance(record_data, dict):
                for key, value in record_data.items():
                    # Skip internal fields that are already handled
                    if key.startswith('__') or key in ['id', 'label', 'created_at', 'updated_at']:
                        continue
                    # Handle complex values
                    if isinstance(value, (dict, list)):
                        flat_record[key] = json.dumps(value)
                    else:
                        flat_record[key] = value

            flattened_data.append(flat_record)

        df = pd.DataFrame(flattened_data)
        return df

    def get_summary_statistics(self, data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Get summary statistics for the dataset"""
        print(data)
        if not data:
            return {}

        df = self.to_dataframe(data)

        stats = {
            'total_records': len(data),
            'unique_labels': len(self.get_unique_labels(data)),
            'properties': len(self.get_all_properties(data)),
            'label_distribution': self.get_label_distribution(data)
        }

        # Numeric statistics
        numeric_columns = df.select_dtypes(include=[np.number]).columns
        if len(numeric_columns) > 0:
            stats['numeric_stats'] = df[numeric_columns].describe().to_dict()

        return stats