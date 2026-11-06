"""
Seed script for RushDB Indexing Tutorial.

Generates mock e-commerce product data to demonstrate indexing capabilities.
This script is idempotent - safe to run multiple times.
"""

import os
import random
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from rushdb import RushDB

# Product categories and templates
CATEGORIES = ["Electronics", "Clothing", "Home & Garden", "Sports", "Books"]

PRODUCT_TEMPLATES = {
    "Electronics": [
        {"name": "Sony WH-1000XM4", "description": "Industry-leading noise cancellation with premium sound quality. 30-hour battery life with quick charging.", "price": 349.99, "brand": "Sony"},
        {"name": "Bose QuietComfort 45", "description": "Balanced audio performance with world-class noise cancellation. Comfortable for all-day wear.", "price": 329.00, "brand": "Bose"},
        {"name": "Apple AirPods Max", "description": "High-fidelity audio with Active Noise Cancellation. Computational audio creates an immersive experience.", "price": 549.00, "brand": "Apple"},
        {"name": "Samsung Galaxy S24 Ultra", "description": "6.8-inch AMOLED display with 200MP camera. Galaxy AI built-in for enhanced productivity.", "price": 1299.99, "brand": "Samsung"},
        {"name": "Dell XPS 13", "description": "13.4-inch InfinityEdge display. Intel Core Ultra processors with AI capabilities.", "price": 999.00, "brand": "Dell"},
        {"name": "MacBook Air M3", "description": "Supercharged by M3 chip. Fanless design with up to 18 hours of battery life.", "price": 1099.00, "brand": "Apple"},
        {"name": "iPad Pro 12.9", "description": "Liquid Retina XDR display with ProMotion. M4 chip for ultimate performance.", "price": 1099.00, "brand": "Apple"},
        {"name": "Kindle Paperwhite", "description": "6.8-inch display with adjustable warm light. 10-week battery life for uninterrupted reading.", "price": 139.99, "brand": "Amazon"},
        {"name": "Nintendo Switch OLED", "description": "7-inch OLED screen with enhanced portability. 64GB internal storage expandable via microSD.", "price": 349.99, "brand": "Nintendo"},
        {"name": "PlayStation 5", "description": "Next-gen gaming with 4K TV gaming and 120fps. Ultra-high speed SSD for instant loading.", "price": 499.99, "brand": "Sony"},
        {"name": "LG C3 65-inch OLED", "description": "Self-lit OLED pixels deliver perfect blacks. a9 AI Processor Gen6 for stunning picture.", "price": 1499.99, "brand": "LG"},
        {"name": "JBL Flip 6 Bluetooth Speaker", "description": "Portable waterproof speaker with 12 hours of playtime. Powerful JBL Original Pro Sound.", "price": 129.95, "brand": "JBL"},
        {"name": "Logitech MX Master 3S", "description": "Advanced wireless mouse with 8K DPI sensor. Quiet clicks and MagSpeed scroll wheel.", "price": 99.99, "brand": "Logitech"},
        {"name": "Razer Huntsman V3 Pro", "description": "Analog optical switches with adjustable actuation. Media keys and programmable macros.", "price": 169.99, "brand": "Razer"},
        {"name": "Anker PowerCore 26800", "description": "26800mAh portable charger with triple port output. Charge three devices simultaneously.", "price": 65.99, "brand": "Anker"},
    ],
    "Clothing": [
        {"name": "Nike Air Max 90", "description": "Iconic running shoes with visible Air cushioning. Leather and textile upper for durability.", "price": 130.00, "brand": "Nike"},
        {"name": "Adidas Ultraboost 22", "description": "Responsive Boost midsole with Linear Energy Push. Primeknit+ upper adapts to your foot.", "price": 190.00, "brand": "Adidas"},
        {"name": "Levi's 501 Original Fit Jeans", "description": "The original button fly jeans since 1873. Classic straight leg with iconic straight fit.", "price": 69.50, "brand": "Levi's"},
        {"name": "Patagonia Better Sweater", "description": "100% recycled polyester fleece. Raglan sleeves for mobility and comfort.", "price": 139.00, "brand": "Patagonia"},
        {"name": "Allbirds Wool Runners", "description": "Sustainable wool sneakers with eucalyptus tree fiber laces. Machine washable.", "price": 98.00, "brand": "Allbirds"},
        {"name": "Arc'teryx Beta AR Jacket", "description": "Gore-Tex Pro shell for all-round weather protection. Helmet-compatible hood.", "price": 599.00, "brand": "Arc'teryx"},
        {"name": "Ray-Ban Aviator Classic", "description": "Tear-drop lenses with thin metal frame. Polarized options available.", "price": 163.00, "brand": "Ray-Ban"},
        {"name": "Carhartt WIP Detroit Jacket", "description": "Heavy-duty duck canvas with blanket lining. Corduroy collar and triple-stitched seams.", "price": 229.00, "brand": "Carhartt"},
    ],
    "Home & Garden": [
        {"name": "Instant Pot Duo 7-in-1", "description": "Electric pressure cooker, slow cooker, rice cooker, steamer, sauté pan, yogurt maker, and warmer.", "price": 89.99, "brand": "Instant Pot"},
        {"name": "Dyson V15 Detect", "description": "Laser reveals microscopic dust. Piezo sensor counts and sizes particles. 60-minute runtime.", "price": 749.99, "brand": "Dyson"},
        {"name": "Ninja Foodi Air Fryer", "description": "7-in-1 functionality including air fry, roast, bake, dehydrate, and reheat.", "price": 199.99, "brand": "Ninja"},
        {"name": "Roomba j9+", "description": "Self-emptying robot vacuum with PrecisionVision Navigation. Avoids pet waste and cords.", "price": 899.99, "brand": "iRobot"},
        {"name": "KitchenAid Stand Mixer", "description": "5.5-quart bowl-lift stand mixer with 10 speeds. Metal construction for durability.", "price": 449.99, "brand": "KitchenAid"},
        {"name": "Weber Spirit II E-310", "description": "3-burner propane gas grill with porcelain-enameled cast iron cooking grates.", "price": 549.00, "brand": "Weber"},
        {"name": "Fiskars Bypass Lopper", "description": "Sharp blade cuts branches up to 2 inches thick. Low-friction coating reduces gumming.", "price": 39.99, "brand": "Fiskars"},
    ],
    "Sports": [
        {"name": "Peloton Bike+", "description": "24-inch rotating HD touchscreen with Apple GymKit. Auto-Follow for seamless resistance changes.", "price": 2495.00, "brand": "Peloton"},
        {"name": "Yeti Tundra 45 Cooler", "description": "Rotomolded construction keeps ice for days. PermaFrost insulation rated for 2-inch thick walls.", "price": 299.99, "brand": "YETI"},
        {"name": "Garmin Forerunner 965", "description": "AMOLED touchscreen GPS running watch with advanced training metrics and recovery insights.", "price": 599.99, "brand": "Garmin"},
        {"name": "Hypervolt Go 2", "description": "Portable percussion massage device with 3 speed settings. Quiet brushless motor.", "price": 199.99, "brand": "Hyperice"},
        {"name": "Theragun Prime", "description": "Muscle treatment device with 5 attachments. Ergonomic multi-grip for hard-to-reach areas.", "price": 299.00, "brand": "Theragun"},
        {"name": "Hydro Flask 32oz Wide Mouth", "description": "TempShield insulation keeps drinks cold for 24 hours. BPA-free and dishwasher safe.", "price": 44.95, "brand": "Hydro Flask"},
        {"name": "Titleist Pro V1 Golf Balls", "description": "Tour-proven performance with exceptional short game spin. 12 balls per box.", "price": 54.99, "brand": "Titleist"},
    ],
    "Books": [
        {"name": "The Pragmatic Programmer", "description": "Your journey to mastery by David Thomas and Andrew Hunt. 20th anniversary edition.", "price": 49.99, "brand": "Addison-Wesley"},
        {"name": "Clean Code by Robert Martin", "description": "A handbook of agile software craftsmanship. Learn to write code that stands the test of time.", "price": 42.99, "brand": "Prentice Hall"},
        {"name": "Designing Data-Intensive Applications", "description": "The big ideas behind reliable, scalable, and maintainable systems by Martin Kleppmann.", "price": 59.99, "brand": "O'Reilly"},
        {"name": "System Design Interview Vol 2", "description": "An insider's guide by Alex Xu. Real-world system design questions and solutions.", "price": 39.99, "brand": "Byte Dive Publishing"},
        {"name": "Elements of Programming Interviews", "description": "300 questions and solutions in Python, Java, and C++. Comprehensive preparation guide.", "price": 49.99, "brand": "EPI"},
        {"name": "Deep Work by Cal Newport", "description": "Rules for focused success in a distracted world. Master the art of concentration.", "price": 16.99, "brand": "Grand Central Publishing"},
    ]
}


def get_or_create_label(db: RushDB, label: str) -> str:
    """Get or create a label for categorization."""
    existing = db.labels.find({})
    for lbl in existing.data:
        if lbl.name == label:
            return lbl.name
    # Label is auto-created on first record, just return it
    return label


def seed_products(db: RushDB) -> int:
    """
    Seed product data. Checks for existing data to ensure idempotency.
    Returns the count of products created.
    """
    # Check if products already exist
    existing = db.records.find({"labels": ["PRODUCT"], "limit": 1})
    if existing.total > 0:
        print(f"  Products already exist ({existing.total} total). Skipping seed.")
        return 0
    
    print("\n  Seeding products across 5 categories...")
    count = 0
    
    # Use a transaction for atomicity
    with db.transactions.begin() as tx:
        for category in CATEGORIES:
            templates = PRODUCT_TEMPLATES.get(category, [])
            for template in templates:
                # Generate variations to create more products
                for variant in range(2):  # 2 variants per template
                    variant_suffix = "" if variant == 0 else f" {['Pro', 'Lite', 'Max', 'Mini'][variant]}"
                    
                    product_data = {
                        "name": f"{template['name']}{variant_suffix}",
                        "description": template["description"],
                        "shortDescription": template["description"][:100],
                        "category": category,
                        "price": round(template["price"] * (0.9 if variant == 1 else 1.0), 2),
                        "brand": template["brand"],
                        "inStock": random.choice([True, True, True, False]),
                        "rating": round(random.uniform(3.5, 5.0), 1),
                        "reviewCount": random.randint(10, 5000),
                        "sku": f"SKU-{category[:3].upper()}-{count:04d}",
                    }
                    
                    db.records.create(
                        label="PRODUCT",
                        data=product_data,
                        transaction=tx
                    )
                    count += 1
                    
                    if count % 50 == 0:
                        print(f"    Created {count} products...")
    
    return count


def main():
    """Main seed function."""
    print("=" * 50)
    print("RushDB Indexing Tutorial - Data Seeding")
    print("=" * 50)
    
    api_key = os.getenv("RUSHDB_API_KEY")
    if not api_key:
        print("ERROR: RUSHDB_API_KEY environment variable not set.")
        print("Please create a .env file with your API key.")
        return
    
    url = os.getenv("RUSHDB_URL")
    db = RushDB(api_key, url=url) if url else RushDB(api_key)
    
    print("\n[1/1] Seeding product data...")
    count = seed_products(db)
    
    if count > 0:
        print(f"\n✓ Successfully seeded {count} products")
    else:
        print("\n✓ Data already exists, no seeding needed")
    
    print("\n" + "=" * 50)
    print("Seeding complete!")
    print("=" * 50)


if __name__ == "__main__":
    main()
