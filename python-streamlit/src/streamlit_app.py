import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
from typing import Dict, List, Any, Optional
import json
from datetime import datetime, date
import sys
from pathlib import Path

# Handle imports
try:
    from .config import get_config
    from .rushdb_client import RushDBClient
    from .data_processor import DataProcessor
    from .chart_generator import ChartGenerator
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent))
    from config import get_config
    from rushdb_client import RushDBClient
    from data_processor import DataProcessor
    from chart_generator import ChartGenerator

# Page configuration
st.set_page_config(
    page_title="RushDB Data Explorer",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 2rem;
        border-radius: 10px;
        margin-bottom: 2rem;
        text-align: center;
    }
    .metric-card {
        background: white;
        padding: 1rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .filter-section {
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    .stSelectbox > div > div {
        background-color: white;
    }
</style>
""", unsafe_allow_html=True)

class StreamlitApp:
    def __init__(self):
        self.init_session_state()
        self.rushdb_client = None
        self.data_processor = None
        self.chart_generator = None

    def init_session_state(self):
        """Initialize session state variables"""
        if 'connected' not in st.session_state:
            st.session_state.connected = False
        if 'data' not in st.session_state:
            st.session_state.data = None
        if 'total' not in st.session_state:
            st.session_state.total = None
        if 'filtered_data' not in st.session_state:
            st.session_state.filtered_data = None
        if 'filters' not in st.session_state:
            st.session_state.filters = {}
        if 'refresh_data' not in st.session_state:
            st.session_state.refresh_data = False

    def setup_connection(self):
        """Setup RushDB connection"""
        try:
            config = get_config()

            if not config['api_token']:
                st.error("🔐 RushDB API token not found! Please check your .env file.")
                with st.expander("🔧 Setup Instructions"):
                    st.markdown("""
                    1. Copy `.env.example` to `.env`
                    2. Add your RushDB API token from [RushDB Dashboard](https://app.rushdb.com)
                    3. Restart the application
                    """)
                return False

            self.rushdb_client = RushDBClient(config)
            self.data_processor = DataProcessor()
            self.chart_generator = ChartGenerator()

            # Test connection
            if self.rushdb_client.test_connection():
                st.session_state.connected = True
                st.success("✅ Connected to RushDB successfully!")

                # Fetch and print all available labels to console
                try:
                    labels = self.rushdb_client.fetch_all_labels()
                    print("🏷️  Available labels in RushDB:")
                    if labels:
                        for i, label in enumerate(labels, 1):
                            print(f"  {i}. {label}")
                    else:
                        print("  No labels found")
                    print(f"📊 Total labels: {len(labels)}")
                except Exception as e:
                    print(f"❌ Error fetching labels: {str(e)}")

                # Automatically load data after successful connection
                print("🔄 Auto-loading data...")
                try:
                    data, total = self.rushdb_client.fetch_all_records()
                    if data:
                        st.session_state.data = data
                        st.session_state.total = total
                        st.session_state.filtered_data = data
                        print(f"✅ Auto-loaded {len(data)} records")
                        st.success(f"📊 Auto-loaded {len(data)} records of {total} - ready for visualization!")
                    else:
                        print("⚠️  No records found in database")
                        st.info("📊 Connected successfully, but no records found. You can generate sample data using the sidebar.")
                except Exception as e:
                    print(f"❌ Error auto-loading data: {str(e)}")
                    st.warning(f"⚠️ Connected but couldn't load data: {str(e)}")

                return True
            else:
                st.error("❌ Failed to connect to RushDB")
                return False

        except Exception as e:
            st.error(f"❌ Connection error: {str(e)}")
            return False

    def render_header(self):
        """Render the main header"""
        st.markdown("""
        <div class="main-header">
            <h1>📊 RushDB Data Explorer</h1>
            <p>Interactive data visualization and filtering with RushDB</p>
        </div>
        """, unsafe_allow_html=True)

    def render_sidebar(self):
        """Render the sidebar with connection and data controls"""
        with st.sidebar:
            st.header("🔧 Data Controls")

            # Connection status
            if st.session_state.connected:
                st.success("🟢 Connected to RushDB")
            else:
                st.error("🔴 Not connected")
                if st.button("🔄 Connect to RushDB"):
                    self.setup_connection()

            st.divider()

            # Data loading section
            if st.session_state.connected:
                st.subheader("📂 Data Management")

                # Show current data status
                if st.session_state.total is not None:
                    record_count = st.session_state.total
                    st.info(f"📊 {record_count} records loaded and ready!")
                else:
                    st.warning("📊 No data loaded yet")

                # Sample data generator
                if st.button("🎲 Generate Sample Data"):
                    with st.spinner("Generating sample data..."):
                        if self.generate_sample_data():
                            st.success("Sample data generated!")
                            # Auto-reload data after generating sample data
                            with st.spinner("Loading new data..."):
                                self.load_data()
                        else:
                            st.error("Failed to generate sample data")

                # Load data
                if st.button("📊 Load Data"):
                    if self.rushdb_client is None:
                        st.error("❌ Please connect to RushDB first!")
                    else:
                        with st.spinner("Loading data from RushDB..."):
                            self.load_data()

                # Data refresh
                if st.button("🔄 Refresh Data"):
                    if self.rushdb_client is None:
                        st.error("❌ Please connect to RushDB first!")
                    else:
                        st.session_state.refresh_data = True
                        self.load_data()

                st.divider()

                # Filters section
                if st.session_state.data is not None:
                    st.subheader("🔍 Filters")
                    self.render_filters()

    def generate_sample_data(self):
        """Generate sample data in RushDB"""
        print(self.rushdb_client)
        try:
            return self.rushdb_client.generate_sample_data()
        except Exception as e:
            st.error(f"Error generating sample data: {str(e)}")
            return False

    def load_data(self):
        """Load data from RushDB"""
        if self.rushdb_client is None:
            st.error("❌ RushDB client not initialized. Please connect first.")
            return

        try:
            with st.spinner("Loading data..."):
                data, total = self.rushdb_client.fetch_all_records()
                if data:
                    st.session_state.data = data
                    st.session_state.total = total
                    st.session_state.filtered_data = data
                    st.success(f"Loaded {len(data)} records of {total} total records")
                else:
                    st.warning("No data found in RushDB")
        except Exception as e:
            st.error(f"Error loading data: {str(e)}")

    def render_filters(self):
        """Render dynamic filters based on available data"""
        if not st.session_state.data:
            return

        data = st.session_state.data

        # Get available properties for filtering
        properties = self.data_processor.get_filterable_properties(data)

        # Label filter
        labels = self.data_processor.get_unique_labels(data)
        if labels:
            selected_labels = st.multiselect(
                "Labels",
                options=labels,
                default=st.session_state.filters.get('labels', [])
            )
            st.session_state.filters['labels'] = selected_labels

        # Property filters
        for prop_name, prop_info in properties.items():
            if prop_info['type'] == 'string':
                unique_values = prop_info['unique_values'][:50]  # Limit to 50 values
                selected_values = st.multiselect(
                    f"{prop_name}",
                    options=unique_values,
                    default=st.session_state.filters.get(prop_name, [])
                )
                st.session_state.filters[prop_name] = selected_values

            elif prop_info['type'] == 'number':
                min_val, max_val = prop_info['range']
                if min_val != max_val:
                    selected_range = st.slider(
                        f"{prop_name}",
                        min_value=float(min_val),
                        max_value=float(max_val),
                        value=st.session_state.filters.get(prop_name, (float(min_val), float(max_val)))
                    )
                    st.session_state.filters[prop_name] = selected_range

            elif prop_info['type'] == 'date':
                min_date, max_date = prop_info['range']
                if min_date != max_date:
                    selected_date_range = st.date_input(
                        f"{prop_name}",
                        value=st.session_state.filters.get(prop_name, (min_date, max_date)),
                        min_value=min_date,
                        max_value=max_date
                    )
                    if len(selected_date_range) == 2:
                        st.session_state.filters[prop_name] = selected_date_range

        # Apply filters button
        if st.button("🔍 Apply Filters"):
            self.apply_filters()

        # Clear filters button
        if st.button("🗑️ Clear Filters"):
            st.session_state.filters = {}
            st.session_state.filtered_data = st.session_state.data
            st.rerun()

    def apply_filters(self):
        """Apply selected filters to the data"""
        if not st.session_state.data:
            return

        filtered_data = self.data_processor.apply_filters(
            st.session_state.data,
            st.session_state.filters
        )
        st.session_state.filtered_data = filtered_data
        st.success(f"Filtered to {len(filtered_data)} records")

    def render_main_content(self):
        """Render the main content area"""
        if not st.session_state.connected:
            st.info("👆 Please connect to RushDB using the sidebar to get started.")
            return

        if st.session_state.data is None:
            st.info("📊 Load data using the sidebar to start exploring.")
            return

        # Data overview
        self.render_data_overview()

        # Charts section
        st.header("📈 Data Visualizations")
        self.render_charts()

        # Data table
        st.header("🗃️ Data Table")
        self.render_data_table()

    def render_data_overview(self):
        """Render data overview metrics"""
        st.header("📊 Data Overview")

        total_records = st.session_state.total if st.session_state.total else 0
        filtered_records = len(st.session_state.filtered_data) if st.session_state.filtered_data else 0

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Total Records", total_records)

        with col2:
            st.metric("Filtered Records", filtered_records)

        with col3:
            if st.session_state.data:
                labels = self.data_processor.get_unique_labels(st.session_state.data)
                st.metric("Unique Labels", len(labels))
            else:
                st.metric("Unique Labels", 0)

        with col4:
            if st.session_state.filtered_data:
                properties = self.data_processor.get_all_properties(st.session_state.filtered_data)
                st.metric("Properties", len(properties))
            else:
                st.metric("Properties", 0)

    def render_charts(self):
        """Render various charts based on the data"""
        if not st.session_state.filtered_data:
            st.info("No data available for visualization")
            return

        data = st.session_state.filtered_data

        # Chart tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Label Distribution", "📈 Property Analysis", "🕐 Time Series", "🔗 Relationships"])

        with tab1:
            self.render_label_charts(data)

        with tab2:
            self.render_property_charts(data)

        with tab3:
            self.render_time_series_charts(data)

        with tab4:
            self.render_relationship_charts(data)

    def render_label_charts(self, data):
        """Render label distribution charts"""
        st.subheader("Label Distribution")

        # Label counts
        label_counts = self.data_processor.get_label_distribution(data)

        if label_counts:
            col1, col2 = st.columns(2)

            with col1:
                # Pie chart
                fig_pie = self.chart_generator.create_pie_chart(
                    label_counts,
                    "Label Distribution"
                )
                st.plotly_chart(fig_pie, use_container_width=True)

            with col2:
                # Bar chart
                fig_bar = self.chart_generator.create_bar_chart(
                    list(label_counts.keys()),
                    list(label_counts.values()),
                    "Label Counts",
                    "Labels",
                    "Count"
                )
                st.plotly_chart(fig_bar, use_container_width=True)

    def render_property_charts(self, data):
        """Render property analysis charts"""
        st.subheader("Property Analysis")

        properties = self.data_processor.get_filterable_properties(data)

        if not properties:
            st.info("No properties available for analysis")
            return

        # Property selection
        prop_name = st.selectbox(
            "Select property to analyze:",
            options=list(properties.keys())
        )

        if prop_name:
            prop_info = properties[prop_name]

            if prop_info['type'] == 'string':
                # String property distribution
                value_counts = prop_info['value_counts']
                fig = self.chart_generator.create_bar_chart(
                    list(value_counts.keys())[:20],  # Top 20 values
                    list(value_counts.values())[:20],
                    f"{prop_name} Distribution",
                    prop_name,
                    "Count"
                )
                st.plotly_chart(fig, use_container_width=True)

            elif prop_info['type'] == 'number':
                # Numeric property histogram
                values = [item['data'].get(prop_name) for item in data if prop_name in item['data']]
                values = [v for v in values if v is not None]

                if values:
                    fig = self.chart_generator.create_histogram(
                        values,
                        f"{prop_name} Distribution",
                        prop_name,
                        "Frequency"
                    )
                    st.plotly_chart(fig, use_container_width=True)

    def render_time_series_charts(self, data):
        """Render time series charts"""
        st.subheader("Time Series Analysis")

        # Check for date properties
        date_properties = self.data_processor.get_date_properties(data)

        if not date_properties:
            st.info("No date properties found for time series analysis")
            return

        # Date property selection
        date_prop = st.selectbox(
            "Select date property:",
            options=date_properties
        )

        if date_prop:
            # Time series of record counts
            time_series_data = self.data_processor.get_time_series_data(data, date_prop)

            if time_series_data:
                fig = self.chart_generator.create_time_series_chart(
                    time_series_data,
                    f"Records Over Time ({date_prop})",
                    "Date",
                    "Record Count"
                )
                st.plotly_chart(fig, use_container_width=True)

    def render_relationship_charts(self, data):
        """Render relationship analysis charts"""
        st.subheader("Relationship Analysis")

        # Get records with relationships
        relationship_data = self.data_processor.get_relationship_data(data)

        if not relationship_data:
            st.info("No relationships found in the data")
            return

        # Relationship type distribution
        rel_type_counts = {}
        for record in relationship_data:
            for rel in record.get('relationships', []):
                rel_type = rel.get('type', 'Unknown')
                rel_type_counts[rel_type] = rel_type_counts.get(rel_type, 0) + 1

        if rel_type_counts:
            fig = self.chart_generator.create_bar_chart(
                list(rel_type_counts.keys()),
                list(rel_type_counts.values()),
                "Relationship Type Distribution",
                "Relationship Type",
                "Count"
            )
            st.plotly_chart(fig, use_container_width=True)

    def render_data_table(self):
        """Render the data table with pagination"""
        if not st.session_state.filtered_data:
            st.info("No data to display")
            return

        data = st.session_state.filtered_data

        # Convert to DataFrame for better display
        df = self.data_processor.to_dataframe(data)

        # Pagination
        page_size = st.selectbox("Records per page:", [10, 25, 50, 100], index=1)
        total_pages = len(df) // page_size + (1 if len(df) % page_size > 0 else 0)

        if total_pages > 0:
            page = st.selectbox("Page:", range(1, total_pages + 1))
            start_idx = (page - 1) * page_size
            end_idx = min(start_idx + page_size, len(df))

            # Display table
            st.dataframe(
                df.iloc[start_idx:end_idx],
                use_container_width=True,
                hide_index=True
            )

            st.caption(f"Showing {start_idx + 1}-{end_idx} of {len(df)} records")
        else:
            st.info("No data to display")

    def run(self):
        """Main application entry point"""
        self.render_header()

        # Setup connection on first run
        if not st.session_state.connected:
            self.setup_connection()

        # Render sidebar
        self.render_sidebar()

        # Render main content
        self.render_main_content()

def main():
    """Main function"""
    app = StreamlitApp()
    app.run()

if __name__ == "__main__":
    main()
