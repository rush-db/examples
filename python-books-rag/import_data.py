from src.config import get_config
from rushdb import RushDB
import os

config = get_config()

def import_data():
    """Import data into RushDB."""
    try:
        # Initialize RushDB client
        db = RushDB(
            api_key=config['api_key'],
            base_url=config['base_url']
        )

        with open(os.path.join(os.path.dirname(__file__), 'test_data', 'data.csv'), 'r') as f:
            books_csv = f.read()

        db.records.import_csv(
            label="BOOK",
            data=books_csv
        )

        print("✅ Data imported successfully")
    except Exception as e:
        print(f"❌ Error importing data: {e}")

if __name__ == "__main__":
    import_data()
