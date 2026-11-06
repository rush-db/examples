"""
Seed script for multi-modal retrieval pipeline.

Generates sample product catalog with:
- Text descriptions (real embeddings via sentence-transformers)
- Image embeddings (simulated for reproducibility)

Run this once before main.py to populate the database.
"""

import os
import random
import numpy as np
from pathlib import Path

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

# Import RushDB
from rushdb import RushDB

# Load environment
load_dotenv()

# Configuration
API_KEY = os.getenv("RUSHDB_API_KEY")
URL = os.getenv("RUSHDB_URL")

if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

# Initialize RushDB client
if URL:
    db = RushDB(API_KEY, url=URL)
else:
    db = RushDB(API_KEY)

# Sample product catalog
PRODUCTS = [
    {
        "name": "Wireless Noise-Canceling Headphones",
        "category": "Electronics",
        "description": "Premium over-ear headphones with active noise cancellation, 30-hour battery life, and crystal-clear audio quality. Features plush memory foam ear cushions for extended comfort.",
        "price": 299.99,
        "image_url": "https://example.com/images/headphones.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Smart Fitness Watch",
        "category": "Wearables",
        "description": "Advanced fitness tracker with heart rate monitoring, GPS, sleep tracking, and 50+ workout modes. Water-resistant up to 50 meters. Syncs seamlessly with iOS and Android.",
        "price": 199.99,
        "image_url": "https://example.com/images/smartwatch.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Ergonomic Office Chair",
        "category": "Furniture",
        "description": "Fully adjustable ergonomic chair with lumbar support, breathable mesh back, and padded armrests. Supports up to 300 lbs. Ideal for long work sessions.",
        "price": 449.99,
        "image_url": "https://example.com/images/chair.jpg",
        "image_type": "lifestyle_photo",
    },
    {
        "name": "4K Ultra HD Monitor",
        "category": "Electronics",
        "description": "32-inch 4K display with HDR support, 144Hz refresh rate, and 1ms response time. Perfect for gaming and professional video editing. Includes USB-C and HDMI ports.",
        "price": 599.99,
        "image_url": "https://example.com/images/monitor.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Portable Bluetooth Speaker",
        "category": "Electronics",
        "description": "Waterproof portable speaker with 360-degree sound, 24-hour battery life, and built-in microphone for hands-free calls. Compact design fits in any bag.",
        "price": 79.99,
        "image_url": "https://example.com/images/speaker.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Mechanical Gaming Keyboard",
        "category": "Electronics",
        "description": "RGB backlit mechanical keyboard with Cherry MX switches, dedicated media controls, and USB passthrough. Features aircraft-grade aluminum frame for durability.",
        "price": 149.99,
        "image_url": "https://example.com/images/keyboard.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Stainless Steel Water Bottle",
        "category": "Kitchen",
        "description": "Double-wall vacuum insulated bottle keeps drinks cold for 24 hours or hot for 12 hours. BPA-free, leak-proof lid. Holds 32oz of your favorite beverage.",
        "price": 34.99,
        "image_url": "https://example.com/images/bottle.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Premium Coffee Maker",
        "category": "Kitchen",
        "description": " programmable 12-cup coffee maker with built-in grinder, thermal carafe, and brew strength control. Features auto-on timer and keep-warm function.",
        "price": 179.99,
        "image_url": "https://example.com/images/coffeemaker.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Standing Desk Converter",
        "category": "Furniture",
        "description": "Height-adjustable standing desk converter with spacious work surface, monitor shelf, and keyboard tray. Smooth gas spring lift mechanism for easy transitions.",
        "price": 289.99,
        "image_url": "https://example.com/images/deskconverter.jpg",
        "image_type": "lifestyle_photo",
    },
    {
        "name": "Wireless Charging Pad",
        "category": "Electronics",
        "description": "Fast wireless charger compatible with all Qi-enabled devices. Sleek minimalist design with LED indicator and built-in safety features against overcharging.",
        "price": 39.99,
        "image_url": "https://example.com/images/charger.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Premium Yoga Mat",
        "category": "Fitness",
        "description": "Extra-thick non-slip yoga mat with alignment lines. Made from eco-friendly TPE material. Provides excellent cushioning for joints during floor exercises.",
        "price": 59.99,
        "image_url": "https://example.com/images/yogamat.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Noise-Canceling Earbuds",
        "category": "Electronics",
        "description": "True wireless earbuds with active noise cancellation, transparency mode, and 8-hour battery life. IPX5 water resistant for workouts. Includes three ear tip sizes.",
        "price": 179.99,
        "image_url": "https://example.com/images/earbuds.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Smart LED Desk Lamp",
        "category": "Electronics",
        "description": "Adjustable desk lamp with 5 color temperatures, 10 brightness levels, and built-in USB charging port. Touch controls and memory function remember your preferences.",
        "price": 49.99,
        "image_url": "https://example.com/images/lamp.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Resistance Bands Set",
        "category": "Fitness",
        "description": "Complete set of 5 resistance bands with different tension levels. Includes door anchor, handles, and ankle straps. Perfect for home workouts and physical therapy.",
        "price": 29.99,
        "image_url": "https://example.com/images/bands.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Laptop Backpack",
        "category": "Accessories",
        "description": "Durable backpack with padded laptop compartment fits up to 17 inches. Features anti-theft pocket, USB charging port, and ergonomic shoulder straps.",
        "price": 69.99,
        "image_url": "https://example.com/images/backpack.jpg",
        "image_type": "lifestyle_photo",
    },
    {
        "name": "Portable Power Bank",
        "category": "Electronics",
        "description": "20000mAh high-capacity power bank with 65W fast charging. Charges laptops, tablets, and phones. Includes LED display showing remaining battery level.",
        "price": 79.99,
        "image_url": "https://example.com/images/powerbank.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Electric Pressure Cooker",
        "category": "Kitchen",
        "description": "8-quart multi-functional pressure cooker with 12 preset programs. Makes rice, soup, stew, meat, and more. Features a delay timer and keep-warm function.",
        "price": 119.99,
        "image_url": "https://example.com/images/pressurecooker.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Webcam 4K Ultra HD",
        "category": "Electronics",
        "description": "Premium webcam with 4K resolution, auto-focus, and built-in privacy shutter. Dual stereo microphones with noise cancellation. Ideal for streaming and video calls.",
        "price": 159.99,
        "image_url": "https://example.com/images/webcam.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Adjustable Dumbbells",
        "category": "Fitness",
        "description": "Space-saving adjustable dumbbells from 5 to 52.5 lbs. Quick-change weight selector with ergonomic grip. Perfect for home gyms with limited space.",
        "price": 299.99,
        "image_url": "https://example.com/images/dumbbells.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Mesh Office Chair",
        "category": "Furniture",
        "description": "Breathable mesh back office chair with synchronized tilt mechanism. Adjustable armrests, lumbar support, and headrest. Supports extended sitting comfortably.",
        "price": 399.99,
        "image_url": "https://example.com/images/meshchair.jpg",
        "image_type": "lifestyle_photo",
    },
    {
        "name": "Tablet Stand",
        "category": "Accessories",
        "description": "Aluminum tablet and phone stand with adjustable angle. Non-slip base keeps devices secure. Compatible with tablets up to 12.9 inches.",
        "price": 24.99,
        "image_url": "https://example.com/images/tabletstand.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Wireless Mouse",
        "category": "Electronics",
        "description": "Ergonomic wireless mouse with silent clicks and 4000 DPI adjustable sensor. 70-hour battery life with USB-C charging. Ambidextrous design suits all users.",
        "price": 49.99,
        "image_url": "https://example.com/images/mouse.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Blender Pro Series",
        "category": "Kitchen",
        "description": "High-performance blender with 1400 watt motor and 6 preset programs. Tritan jar is BPA-free and dishwasher safe. Makes smoothies, soups, and frozen desserts.",
        "price": 149.99,
        "image_url": "https://example.com/images/blender.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Air Purifier HEPA",
        "category": "Home",
        "description": "True HEPA air purifier covers rooms up to 500 sq ft. Features air quality indicator, sleep mode, and timer. Removes 99.97% of airborne particles.",
        "price": 199.99,
        "image_url": "https://example.com/images/airpurifier.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Mechanical Pencil Set",
        "category": "Office",
        "description": "Professional drafting pencils with 6 different lead weights. Includes erasers, lead pointer, and carrying case. Preferred by artists and engineers.",
        "price": 34.99,
        "image_url": "https://example.com/images/pencils.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "USB-C Hub 10-in-1",
        "category": "Electronics",
        "description": "Multi-port USB-C hub with HDMI, USB-A, SD card reader, Ethernet, and audio jack. Supports 100W power delivery pass-through. Aluminum construction.",
        "price": 59.99,
        "image_url": "https://example.com/images/usbhub.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Insulated Lunch Bag",
        "category": "Accessories",
        "description": "Thermal lunch bag with multiple compartments and leak-proof lining. Keeps food cold for 8 hours. Machine washable and collapsible for easy storage.",
        "price": 19.99,
        "image_url": "https://example.com/images/lunchbag.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Electric Kettle",
        "category": "Kitchen",
        "description": "Stainless steel electric kettle with 1.7L capacity and 1500W heating element. Boils water in under 5 minutes. Auto shut-off and boil-dry protection.",
        "price": 39.99,
        "image_url": "https://example.com/images/kettle.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "Jump Rope Speed",
        "category": "Fitness",
        "description": "Adjustable speed jump rope with ball bearings for smooth rotation. Non-slip handles and tangle-free cable. Burns calories faster than running.",
        "price": 14.99,
        "image_url": "https://example.com/images/jumprope.jpg",
        "image_type": "product_photo",
    },
    {
        "name": "LED Strip Lights",
        "category": "Home",
        "description": "16ft color-changing LED strip lights with 44-key remote. Multiple modes including music sync. Adhesive backing for easy installation anywhere.",
        "price": 29.99,
        "image_url": "https://example.com/images/ledstrip.jpg",
        "image_type": "lifestyle_photo",
    },
]


def normalize_vector(vec: np.ndarray) -> list:
    """Normalize vector to unit length for cosine similarity."""
    norm = np.linalg.norm(vec)
    if norm == 0:
        return vec.tolist()
    return (vec / norm).tolist()


def generate_simulated_image_embedding(product_name: str, category: str) -> list:
    """
    Generate simulated image embedding based on product metadata.
    
    In production, you would use CLIP or similar model to encode actual images.
    This simulation creates deterministic vectors based on product attributes
    to demonstrate the multi-modal pattern without requiring image downloads.
    """
    # Create a base seed for reproducibility
    seed_value = hash(f"{product_name}{category}") % (2**31)
    rng = random.Random(seed_value)
    
    # Generate 512-dim vector (simulating CLIP embeddings)
    raw = np.array([rng.gauss(0, 1) for _ in range(512)])
    
    # Add category-specific bias to create meaningful clusters
    category_bias = {
        "Electronics": np.array([1.0] * 64 + [0.0] * 448),
        "Furniture": np.array([0.0] * 64 + [1.0] * 64 + [0.0] * 384),
        "Kitchen": np.array([0.0] * 128 + [1.0] * 64 + [0.0] * 320),
        "Fitness": np.array([0.0] * 192 + [1.0] * 64 + [0.0] * 256),
        "Accessories": np.array([0.0] * 256 + [1.0] * 64 + [0.0] * 192),
        "Wearables": np.array([0.0] * 320 + [1.0] * 64 + [0.0] * 128),
        "Office": np.array([0.0] * 384 + [1.0] * 64 + [0.0] * 64),
        "Home": np.array([0.0] * 448 + [1.0] * 64),
    }
    
    category_vector = category_bias.get(category, np.zeros(512))
    combined = raw * 0.8 + category_vector * 0.2
    
    return normalize_vector(combined)


def check_existing_data():
    """Check if data already exists to avoid duplicates."""
    result = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    return len(result.data) > 0


def cleanup_existing_indexes():
    """Remove existing indexes before re-seeding."""
    existing = db.ai.indexes.find()
    for idx in existing.data:
        if idx["label"] == "PRODUCT":
            try:
                db.ai.indexes.delete(idx["__id"])
                print(f"  Deleted existing index: {idx['propertyName']}")
            except Exception as e:
                print(f"  Warning: Could not delete index {idx['__id']}: {e}")


def cleanup_existing_records():
    """Remove existing products before re-seeding."""
    result = db.records.delete_many({"labels": ["PRODUCT"]})
    print(f"  Deleted existing records")


def main():
    print("\n" + "=" * 60)
    print("Multi-Modal Retrieval Pipeline - Data Seeding")
    print("=" * 60 + "\n")

    # Check for existing data
    if check_existing_data():
        response = input("\nExisting PRODUCT records found. Re-seed? (y/N): ")
        if response.lower() == "y":
            print("\nCleaning up existing data...")
            cleanup_existing_indexes()
            cleanup_existing_records()
        else:
            print("Skipping seeding. Run main.py to use existing data.")
            return

    print("Initializing text embedding model...")
    model = SentenceTransformer("all-MiniLM-L6-v2")
    print(f"  Model: all-MiniLM-L6-v2 (384 dimensions)\n")

    # Create vector indexes
    print("Creating vector indexes...")
    
    text_index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "text_embedding",
        "sourceType": "external",
        "dimensions": 384,
        "similarityFunction": "cosine",
    })
    print(f"  Text embedding index: {text_index.data.get('__id', 'created')}")
    print(f"  Status: {text_index.data.get('status', 'awaiting_vectors')}")

    image_index = db.ai.indexes.create({
        "label": "PRODUCT",
        "propertyName": "image_embedding",
        "sourceType": "external",
        "dimensions": 512,
        "similarityFunction": "cosine",
    })
    print(f"  Image embedding index: {image_index.data.get('__id', 'created')}")
    print(f"  Status: {image_index.data.get('status', 'awaiting_vectors')}\n")

    # Generate embeddings and create records
    print(f"Generating embeddings and creating {len(PRODUCTS)} products...")
    print("-" * 40)

    created_products = []
    text_vectors = []
    image_vectors = []

    # Batch generate text embeddings for efficiency
    texts = [f"{p['name']} {p['description']}" for p in PRODUCTS]
    text_embeddings = model.encode(texts, normalize_embeddings=True)

    for i, product_data in enumerate(PRODUCTS):
        # Generate text embedding
        text_vec = text_embeddings[i].tolist()
        
        # Generate simulated image embedding
        image_vec = generate_simulated_image_embedding(
            product_data["name"],
            product_data["category"]
        )

        # Create product record with embedded vectors
        product = db.records.create(
            label="PRODUCT",
            data={
                "name": product_data["name"],
                "category": product_data["category"],
                "description": product_data["description"],
                "price": product_data["price"],
                "image_url": product_data["image_url"],
                "image_type": product_data["image_type"],
            },
            vectors=[
                {"propertyName": "text_embedding", "vector": text_vec},
                {"propertyName": "image_embedding", "vector": image_vec},
            ]
        )
        
        created_products.append(product)
        text_vectors.append({"recordId": product.id, "vector": text_vec})
        image_vectors.append({"recordId": product.id, "vector": image_vec})

        if (i + 1) % 5 == 0:
            print(f"  Progress: {i + 1}/{len(PRODUCTS)} products created")

    # Upsert vectors into indexes
    print("\nIndexing vectors...")
    text_idx_id = text_index.data.get("__id")
    image_idx_id = image_index.data.get("__id")

    if text_idx_id:
        db.ai.indexes.upsert_vectors(text_idx_id, {"items": text_vectors})
        print("  Text embeddings indexed")
    
    if image_idx_id:
        db.ai.indexes.upsert_vectors(image_idx_id, {"items": image_vectors})
        print("  Image embeddings indexed")

    # Create a COLLECTION to group products
    print("\nCreating collection...")
    collection = db.records.create(
        label="COLLECTION",
        data={
            "name": "E-Commerce Catalog",
            "description": "Main product catalog for multi-modal search demo",
        }
    )

    # Attach products to collection
    for product in created_products:
        db.records.attach(
            source=product,
            target=collection,
            options={"type": "BELONGS_TO", "direction": "out"}
        )
    print(f"  Attached {len(created_products)} products to collection\n")

    print("=" * 60)
    print("Seeding complete!")
    print("=" * 60)
    print(f"\n  Products created: {len(PRODUCTS)}")
    print(f"  Text vectors: {len(text_vectors)} (384-dim)")
    print(f"  Image vectors: {len(image_vectors)} (512-dim)")
    print(f"  Collection: {collection.id}")
    print("\nRun 'python main.py' to explore the retrieval pipeline.\n")


if __name__ == "__main__":
    main()
