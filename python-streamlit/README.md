# RushDB Streamlit Data Visualization App

A powerful Streamlit application for visualizing and filtering data stored in RushDB cloud projects. This app provides an intuitive interface to connect to your RushDB instance, load data, and create interactive visualizations using Plotly.

## Features

- 🔌 **Easy RushDB Connection**: Connect to your RushDB cloud project with API token
- 📊 **Interactive Data Visualization**: Create bar charts, line charts, scatter plots, and histograms
- 🔍 **Advanced Filtering**: Filter data by columns, values, and date ranges
- 📈 **Real-time Analytics**: View data statistics and insights
- 🎨 **Modern UI**: Clean and intuitive Streamlit interface

## Prerequisites

- Python 3.8 or higher
- RushDB API token (get one from your RushDB cloud project)
- UV package manager (recommended) or pip

## Quick Start

### 1. Environment Setup

Create a `.env` file in the project root with your RushDB API token:

```bash
RUSHDB_API_TOKEN=your_rushdb_token_here
```

### 2. Installation & Running

Using UV (recommended):

```bash
# Install dependencies and run the application
uv run streamlit run src/streamlit_app.py
```

Using pip:

```bash
# Install dependencies
pip install -e .

# Run the application
streamlit run src/streamlit_app.py
```

### 3. Access the Application

Open your browser and navigate to:

- Local: http://localhost:8501
- Network: http://192.168.1.5:8501

## How to Use

### Step 1: Connect to RushDB

1. Open the application in your browser
2. Click the **"Connect to RushDB"** button in the sidebar
3. The app will automatically use your API token from the `.env` file
4. Wait for the ✅ "Connected to RushDB successfully!" message

### Step 2: Load Your Data

1. After successful connection, click **"Load Data"** button
2. The app will fetch all records from your RushDB project
3. View the data summary and sample records

### Step 3: Create Visualizations

1. **Select Chart Type**: Choose from Bar Chart, Line Chart, Scatter Plot, or Histogram
2. **Configure Axes**:
   - Select X-axis column (categorical or numerical)
   - Select Y-axis column (numerical for most charts)
   - For scatter plots, optionally select color grouping
3. **Apply Filters** (optional):
   - Filter by specific column values
   - Set date ranges for time-series data
   - Use text search across all columns
4. **Generate Chart**: Click "Generate Chart" to create your visualization

### Step 4: Analyze Results

- View interactive Plotly charts with zoom, pan, and hover features
- Check data statistics and filtered record counts
- Export visualizations as images if needed

## Project Structure

```
python-streamlit/
├── src/
│   ├── streamlit_app.py      # Main Streamlit application
│   ├── rushdb_client.py      # RushDB connection and operations
│   ├── data_processor.py     # Data processing utilities
│   ├── chart_generator.py    # Plotly chart generation
│   └── config.py            # Configuration management
├── .env                     # Environment variables
├── pyproject.toml          # Project dependencies
├── README.md               # This file
└── run_app.py             # Alternative app runner
```

## Troubleshooting

### Common Issues

**Error: "RushDB client not initialized"**

- Make sure you clicked "Connect to RushDB" first before loading data
- Verify your API token is correctly set in the `.env` file

**Error: "'NoneType' object has no attribute 'fetch_all_records'"**

- This has been fixed in the latest version
- Ensure you're using the updated code with proper null checks

**No data appears after loading**

- Check that your RushDB project actually contains data
- Verify your API token has the correct permissions

**Charts not displaying**

- Ensure you have selected appropriate columns for X and Y axes
- Check that your data contains the expected data types

### Getting Help

1. Check the Streamlit sidebar for status messages and errors
2. Verify your RushDB connection status before proceeding
3. Ensure your data has the expected structure and types
4. Check the terminal output for detailed error messages

## Dependencies

- **streamlit**: Web application framework
- **rushdb**: RushDB client library
- **plotly**: Interactive plotting library
- **pandas**: Data manipulation and analysis
- **python-dotenv**: Environment variable management

## Development

To modify or extend the application:

1. **Add new chart types**: Extend `chart_generator.py`
2. **Add new filters**: Modify filtering logic in `streamlit_app.py`
3. **Customize UI**: Update the Streamlit interface components
4. **Add data processing**: Extend `data_processor.py`

## License

This project is part of the RushDB examples collection.
