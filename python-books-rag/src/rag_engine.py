from typing import List, Dict, Any, Optional
from sentence_transformers import SentenceTransformer
from rushdb import RushDB
import json


class TextProcessor:
    """Handles text vectorization."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        self.model = SentenceTransformer(model_name)

    def vectorize_text(self, text: str) -> List[float]:
        """Convert text to vector embedding."""
        embedding = self.model.encode(text)
        return embedding.tolist()


class RagService:
    """Handles RushDB operations for record storage and retrieval."""

    def __init__(self, api_key: str, base_url: str = None,
                 model_name: str = "all-MiniLM-L6-v2"):
        # Initialize connection with error handling
        try:
            if base_url:
                self.db = RushDB(api_key, base_url=base_url)
            else:
                self.db = RushDB(api_key)
            # Verify connection by making a simple API call
            self.db.ping()
        except Exception as e:
            raise ConnectionError(f"Failed to connect to RushDB: {str(e)}")

        # Initialize text processor
        try:
            self.processor = TextProcessor(model_name=model_name)
        except Exception as e:
            raise ValueError(f"Failed to initialize text processor: {str(e)}")

    def set_embedding_model(self, model_name: str):
        """Change the embedding model used by the processor."""
        self.processor.model = SentenceTransformer(model_name)

    def set_model_by_dimension(self, dimension: int):
        """Set an appropriate model based on the requested vector dimension.

        This is a simple implementation. In a production environment, you might
        want to have a mapping of dimensions to appropriate models.
        """
        # Some common models and their dimensions
        if dimension == 384:
            self.set_embedding_model("all-MiniLM-L6-v2")
        elif dimension == 768:
            self.set_embedding_model("all-mpnet-base-v2")
        else:
            # Default to all-MiniLM-L6-v2 if no matching dimension
            print(f"Warning: No matching model for dimension {dimension}. Using default.")
            self.set_embedding_model("all-MiniLM-L6-v2")

    def index_records(self, search_query: Dict, field: str):
        """Process records and add embedding property to each record."""
        processed_count = 0
        error_count = 0
        skipped_count = 0
        current_skip = 0
        batch_size = search_query.get("limit", 100)  # Use provided limit or default to 100

        try:
            # Create a copy of search_query to modify for pagination
            paginated_query = search_query.copy()

            while True:
                # Set pagination parameters
                paginated_query["skip"] = current_skip
                paginated_query["limit"] = batch_size

                print(f"Fetching records: skip={current_skip}, limit={batch_size}")
                raw_results = self.db.records.find(paginated_query)

                # Check if we have any records in this batch
                if not raw_results or len(raw_results.data) == 0:
                    break

                print(f"Processing batch of {len(raw_results.data)} records (total available: {raw_results.total})")

                # Process records in current batch
                for record in raw_results.data:
                    try:
                        record_data = record.to_dict(exclude_internal=False)
                        record_id = record_data["__id"]

                        if field not in record_data:
                            print(f"Field '{field}' not found in record {record_id}")
                            skipped_count += 1
                            continue

                        # Get the field content
                        content = record_data[field]
                        if not content or not isinstance(content, str):
                            print(f"Invalid content in field '{field}' for record {record_id}")
                            skipped_count += 1
                            continue

                        print(f"Processing record {record_id}...")

                        # Vectorize the content directly
                        embedding = self.processor.vectorize_text(content)

                        # Update the record with the embedding
                        record.update({"properties": [{"name": "embedding", "value": embedding, "type": "vector"}]})

                        processed_count += 1
                        print(f"Added embedding to record {record_id}")

                    except Exception as record_error:
                        print(f"Error processing record: {str(record_error)}")
                        error_count += 1
                        continue

                # Check if there are more records to process
                if not raw_results.has_more:
                    break

                # Move to next batch
                current_skip += len(raw_results.data)
                print(f"Batch complete. Moving to next batch...")

            print(f"Indexing complete. Processed: {processed_count}, Errors: {error_count}, Skipped: {skipped_count}")

            return {
                "processed": processed_count,
                "errors": error_count,
                "skipped": skipped_count,
                "message": "Indexing complete"
            }
        except Exception as e:
            error_message = f"Error during indexing: {str(e)}"
            print(error_message)
            return {
                "processed": processed_count,
                "errors": error_count + 1,
                "skipped": skipped_count,
                "message": error_message
            }

    def search(self, query: str, search_query: Dict) -> Dict:
        query_vector = self.processor.vectorize_text(query)

        try:
            raw_results = self.db.records.find({
                **search_query,
                "where": {
                    **search_query.get('where', {}),
                    "embedding": {
                        "$vector": {
                            "fn": "gds.similarity.cosine",
                            "query": query_vector,
                            "threshold": 0.7
                        }
                    }
                },
                "aggregate": {
                    "score": {
                        "alias": "$record",
                        "field": "embedding",
                        "fn": "gds.similarity.cosine",
                        "query": query_vector
                    }
                },
                "orderBy": {"score": "desc"},
                "limit": search_query.get("limit", 10)
            })

            return {
                "success": True,
                "total": raw_results.total,
                "data": [item.to_dict(exclude_internal=False) for item in raw_results.data]
            }
        except Exception as e:
            error_message = f"RushDB search query failed: {str(e)}"
            print(error_message)
            raise ValueError(error_message)
