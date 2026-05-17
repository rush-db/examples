"""
Cross-Modal Retrieval - Data Seeder

Creates a cross-modal knowledge graph with:
- IMAGE records with semantic descriptions and embeddings
- AUDIO records with semantic descriptions and embeddings  
- CONCEPT anchor nodes representing shared semantic properties
- Relationships linking media to concepts

Run this script to populate the database with test data.
Safe to run multiple times (idempotent via upsert patterns).
"""

import os
import time
import random
from dotenv import load_dotenv

from rushdb import RushDB
from sentence_transformers import SentenceTransformer

# Load environment
load_dotenv()

# Initialize RushDB client
api_key = os.getenv("RUSHDB_API_KEY")
url = os.getenv("RUSHDB_URL")

if not api_key:
    print("ERROR: RUSHDB_API_KEY not set in .env")
    exit(1)

db = RushDB(api_key, url=url) if url else RushDB(api_key)

# Initialize embedding model (all-MiniLM-L6-v2: 384 dimensions)
print("Loading embedding model (all-MiniLM-L6-v2)...")
model = SentenceTransformer('all-MiniLM-L6-v2')
EMBEDDING_DIM = 384

# Sample data - realistic cross-modal content
IMAGES = [
    {"name": "Golden sunrise mountain", "description": "Golden hour light illuminating snow-capped mountain peaks at dawn", "emotion": "awe", "theme": "nature"},
    {"name": "Ocean waves at sunset", "description": "Pacific waves crashing against rocky shore during orange sunset", "emotion": "serene", "theme": "nature"},
    {"name": "Forest path autumn", "description": "Winding dirt path through colorful autumn forest with filtered sunlight", "emotion": "contemplative", "theme": "nature"},
    {"name": "City skyline night", "description": "Modern city skyline illuminated at night with reflections in water", "emotion": "energetic", "theme": "urban"},
    {"name": "Desert dunes", "description": "Rolling sand dunes in Sahara desert with dramatic shadows", "emotion": "vast", "theme": "nature"},
    {"name": "Flower field spring", "description": "Vast purple lavender field in Provence with rolling hills", "emotion": "peaceful", "theme": "nature"},
    {"name": "Thunderstorm lightning", "description": "Dramatic lightning bolt striking over dark storm clouds", "emotion": "intense", "theme": "nature"},
    {"name": "Coffee shop interior", "description": "Cozy coffee shop interior with warm lighting and wooden furniture", "emotion": "comfortable", "theme": "urban"},
    {"name": "Northern lights", "description": "Green aurora borealis dancing across starry Arctic night sky", "emotion": "magical", "theme": "nature"},
    {"name": "Busy market street", "description": "Vibrant street market in Bangkok with colorful fruits and bustling crowds", "emotion": "exciting", "theme": "urban"},
    {"name": "Misty morning lake", "description": "Calm lake shrouded in morning mist with silhouetted trees", "emotion": "tranquil", "theme": "nature"},
    {"name": "Graffiti wall art", "description": "Vibrant colorful graffiti art covering brick wall in Brooklyn", "emotion": "rebellious", "theme": "urban"},
    {"name": "Rain on window", "description": "Raindrops streaming down window overlooking blurred city lights", "emotion": "melancholic", "theme": "urban"},
    {"name": "Mountain trail vista", "description": "Panoramic view from mountain hiking trail overlooking deep valley", "emotion": "adventurous", "theme": "nature"},
    {"name": "Sunflower field", "description": "Endless bright yellow sunflower field under blue summer sky", "emotion": "joyful", "theme": "nature"},
    {"name": "Underwater coral reef", "description": "Vibrant coral reef teeming with tropical fish underwater", "emotion": "peaceful", "theme": "nature"},
    {"name": "Nightclub lights", "description": "Pulsing neon lights and lasers in crowded electronic music venue", "emotion": "euphoric", "theme": "urban"},
    {"name": "Japanese temple", "description": "Traditional Japanese temple surrounded by cherry blossoms in spring", "emotion": "serene", "theme": "cultural"},
    {"name": "Rocky coastline", "description": "Dramatic Atlantic coastline with crashing waves and dark cliffs", "emotion": "powerful", "theme": "nature"},
    {"name": "Library reading room", "description": "Grand library with towering bookshelves and warm reading lamps", "emotion": "scholarly", "theme": "cultural"},
    {"name": "Sunset beach silhouettes", "description": "Couple walking on beach as silhouettes against orange sunset", "emotion": "romantic", "theme": "nature"},
    {"name": "Industrial factory", "description": "Moody industrial factory interior with machinery and steam", "emotion": "dark", "theme": "urban"},
    {"name": "Snowy village", "description": "Quaint European village covered in fresh snow with chimney smoke", "emotion": "cozy", "theme": "cultural"},
    {"name": "Festival crowd", "description": "Massive crowd at outdoor music festival with stage lights", "emotion": "exciting", "theme": "cultural"},
    {"name": "Misty forest", "description": "Ancient redwood forest shrouded in morning fog and mist", "emotion": "mysterious", "theme": "nature"},
    {"name": "Street musician", "description": "Guitarist performing on cobblestone street in European city", "emotion": "soulful", "theme": "cultural"},
    {"name": "Abstract paint", "description": "Bold abstract painting with vibrant colors and dynamic brushstrokes", "emotion": "creative", "theme": "art"},
    {"name": "Rainbow after storm", "description": "Double rainbow arching over green hills after summer storm", "emotion": "hopeful", "theme": "nature"},
    {"name": "Abandoned building", "description": "Overgrown abandoned mansion with vines and broken windows", "emotion": "eerie", "theme": "urban"},
    {"name": "Garden fountain", "description": "Ornate marble fountain in serene formal garden at twilight", "emotion": "elegant", "theme": "cultural"},
]

AUDIO = [
    {"name": "Gentle rain", "description": "Soft continuous rain on leaves with distant thunder rumbles", "emotion": "peaceful", "theme": "nature"},
    {"name": "Ocean waves ambient", "description": "Rhythmic ocean waves recorded on secluded beach at dusk", "emotion": "serene", "theme": "nature"},
    {"name": "Forest birds", "description": "Morning forest with chirping sparrows and rustling leaves", "emotion": "tranquil", "theme": "nature"},
    {"name": "Electronic beats", "description": "Driving electronic dance music with pulsing bass and synths", "emotion": "energetic", "theme": "electronic"},
    {"name": "Meditation bells", "description": "Tibetan singing bowls and meditation bells in quiet space", "emotion": "serene", "theme": "wellness"},
    {"name": "Jazz piano trio", "description": "Smooth jazz piano with upright bass and soft brushes", "emotion": "sophisticated", "theme": "jazz"},
    {"name": "Thunderstorm recording", "description": "Powerful thunderstorm with heavy rain and wind gusts", "emotion": "intense", "theme": "nature"},
    {"name": "Cafe ambience", "description": "Coffee shop background chatter with espresso machine sounds", "emotion": "comfortable", "theme": "urban"},
    {"name": "String quartet", "description": "Elegant string quartet playing classical composition in concert hall", "emotion": "elegant", "theme": "classical"},
    {"name": "Street performer", "description": "Energetic street drumming circle with African percussion", "emotion": "exciting", "theme": "world"},
    {"name": "Wind through trees", "description": "Gentle wind rustling through pine forest branches", "emotion": "contemplative", "theme": "nature"},
    {"name": "Acoustic guitar folk", "description": "Warm acoustic guitar fingerpicking folk melody", "emotion": "nostalgic", "theme": "folk"},
    {"name": "Heavy metal guitar", "description": "Distorted heavy metal guitar riffs with double bass drums", "emotion": "powerful", "theme": "metal"},
    {"name": "Lullaby piano", "description": "Soft piano lullaby with gentle arpeggios and high notes", "emotion": "soothing", "theme": "classical"},
    {"name": "City traffic", "description": "Urban street scene with car horns and distant sirens", "emotion": "urban", "theme": "urban"},
    {"name": "Symphony orchestra", "description": "Full orchestra building to dramatic crescendo finale", "emotion": "majestic", "theme": "classical"},
    {"name": "Reggae rhythm", "description": "Relaxed reggae groove with offbeat guitar and bass", "emotion": "chill", "theme": "reggae"},
    {"name": "Train journey", "description": "Train on tracks with rhythmic clicks and passing countryside", "emotion": "melancholic", "theme": "travel"},
    {"name": "Children playing", "description": "Children laughing and playing in playground with squeaks", "emotion": "joyful", "theme": "human"},
    {"name": "Ambient synth pad", "description": "Ethereal synthesizer ambient pad with reverb and delay", "emotion": "dreamy", "theme": "electronic"},
    {"name": "Rock anthem", "description": "Classic rock anthem with power chords and soaring vocals", "emotion": "triumphant", "theme": "rock"},
    {"name": "Waterfall cascade", "description": "Powerful waterfall with mist and echoing roar", "emotion": "awe-inspiring", "theme": "nature"},
    {"name": "Bluegrass banjo", "description": "Fast-paced bluegrass banjo with mandolin and fiddle", "emotion": "upbeat", "theme": "folk"},
    {"name": "Lo-fi beats", "description": "Chill lo-fi hip hop beats with vinyl crackle and piano", "emotion": "relaxed", "theme": "hip-hop"},
    {"name": "Crowd cheering", "description": "Sports stadium crowd cheering after winning goal", "emotion": "exciting", "theme": "sports"},
    {"name": "Classical piano", "description": "Solo piano playing romantic era nocturne by moonlight", "emotion": "romantic", "theme": "classical"},
    {"name": "Jazz saxophone", "description": "Smooth jazz saxophone improvisation over walking bass", "emotion": "soulful", "theme": "jazz"},
    {"name": "Campfire crackling", "description": "Cozy campfire with wood crackling and distant crickets", "emotion": "cozy", "theme": "nature"},
    {"name": "Technoindustrial", "description": "Dark technoindustrial track with distorted drums and samples", "emotion": "dark", "theme": "electronic"},
    {"name": "Singer songwriter", "description": "Intimate acoustic song with heartfelt vocals and guitar", "emotion": "emotional", "theme": "folk"},
]

CONCEPTS = [
    {"name": "serenity", "keywords": ["calm", "peaceful", "tranquil", "serene", "gentle"]},
    {"name": "excitement", "keywords": ["energetic", "thrilling", "dynamic", "intense", "pulsing"]},
    {"name": "nature", "keywords": ["outdoor", "organic", "earth", "natural", "wild"]},
    {"name": "urban", "keywords": ["city", "street", "modern", "metropolitan", "concrete"]},
    {"name": "melancholy", "keywords": ["sad", "nostalgic", "bittersweet", "reflective", "wistful"]},
    {"name": "joy", "keywords": ["happy", "uplifting", "cheerful", "bright", "celebratory"]},
    {"name": "mystery", "keywords": ["unknown", "enigmatic", "hidden", "secret", "shadowy"]},
    {"name": "power", "keywords": ["strong", "forceful", "dominant", "massive", "overwhelming"]},
    {"name": "warmth", "keywords": ["cozy", "comforting", "soft", "inviting", "homely"]},
    {"name": "wonder", "keywords": ["amazing", "marvelous", "magical", "spectacular", "stunning"]},
    {"name": "rebellion", "keywords": ["edgy", "defiant", "anti-establishment", "counter-culture", "punk"]},
    {"name": "romance", "keywords": ["love", "passionate", "intimate", "affectionate", "tender"]},
    {"name": "awe", "keywords": ["impressive", "grand", "majestic", "breathtaking", "spectacular"]},
    {"name": "contemplation", "keywords": ["thoughtful", "meditative", "introspective", "pensive", "philosophical"]},
    {"name": "adventure", "keywords": ["exploration", "discovery", "journey", "risk", "expedition"]},
]


def check_data_exists():
    """Check if data already exists in the database."""
    try:
        images = db.records.find({"labels": ["IMAGE"], "limit": 1})
        if images.total > 0:
            print(f"Found {images.total} IMAGE record(s) - data may already exist")
            return True
    except Exception:
        pass
    return False


def get_or_create_concept(name, keywords):
    """Get existing concept or create new one."""
    existing = db.records.find({"labels": ["CONCEPT"], "where": {"name": name}})
    if existing.data:
        return existing.data[0]
    
    # Create concept with embedding
    concept_text = f"{name}: {' '.join(keywords)}"
    vector = model.encode(concept_text).tolist()
    
    concept = db.records.create(
        label="CONCEPT",
        data={"name": name, "keywords": keywords},
        vectors=[{"propertyName": "description", "vector": vector}]
    )
    return concept


def main():
    print("\n" + "="*60)
    print("CROSS-MODAL RETRIEVAL - DATA SEEDER")
    print("="*60 + "\n")
    
    # Check if already seeded
    if check_data_exists():
        response = input("\nExisting data found. Re-seed? (y/N): ")
        if response.lower() != 'y':
            print("Skipping seed. Run with --mode demo to see the demo.")
            return
    
    print("[1/5] Creating CONCEPT anchor nodes...")
    concept_map = {}
    for i, concept_data in enumerate(CONCEPTS):
        concept = get_or_create_concept(concept_data["name"], concept_data["keywords"])
        concept_map[concept_data["name"]] = concept
        if (i + 1) % 5 == 0:
            print(f"    Processed {i + 1}/{len(CONCEPTS)} concepts...")
    print(f"    ✓ Created/found {len(concept_map)} CONCEPT nodes")
    
    print("\n[2/5] Creating IMAGE nodes with embeddings...")
    image_records = []
    for i, img in enumerate(IMAGES):
        description = img["description"]
        vector = model.encode(description).tolist()
        
        image = db.records.create(
            label="IMAGE",
            data={
                "name": img["name"],
                "description": description,
                "emotion": img["emotion"],
                "theme": img["theme"]
            },
            vectors=[{"propertyName": "description", "vector": vector}]
        )
        image_records.append(image)
        
        # Attach to matching concepts (emotion + theme)
        matching_concepts = [img["emotion"], img["theme"]]
        for concept_name in matching_concepts:
            if concept_name in concept_map:
                db.records.attach(
                    source=image,
                    target=concept_map[concept_name],
                    options={"type": "REPRESENTS", "direction": "out"}
                )
        
        if (i + 1) % 10 == 0:
            print(f"    Processed {i + 1}/{len(IMAGES)} images...")
    print(f"    ✓ Created {len(image_records)} IMAGE records")
    
    print("\n[3/5] Creating AUDIO nodes with embeddings...")
    audio_records = []
    for i, aud in enumerate(AUDIO):
        description = aud["description"]
        vector = model.encode(description).tolist()
        
        audio = db.records.create(
            label="AUDIO",
            data={
                "name": aud["name"],
                "description": description,
                "emotion": aud["emotion"],
                "theme": aud["theme"]
            },
            vectors=[{"propertyName": "description", "vector": vector}]
        )
        audio_records.append(audio)
        
        # Attach to matching concepts (emotion + theme)
        matching_concepts = [aud["emotion"], aud["theme"]]
        for concept_name in matching_concepts:
            if concept_name in concept_map:
                db.records.attach(
                    source=audio,
                    target=concept_map[concept_name],
                    options={"type": "EXPRESSES", "direction": "out"}
                )
        
        if (i + 1) % 10 == 0:
            print(f"    Processed {i + 1}/{len(AUDIO)} audio clips...")
    print(f"    ✓ Created {len(audio_records)} AUDIO records")
    
    print("\n[4/5] Creating vector indexes for semantic search...")
    indexes = db.ai.indexes.find()
    existing_labels = [idx['label'] for idx in indexes.data]
    
    # Create IMAGE index
    if "IMAGE" not in existing_labels:
        db.ai.indexes.create({
            "label": "IMAGE",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print("    ✓ Created IMAGE.description vector index")
    else:
        print("    ℹ IMAGE.description index already exists")
    
    # Create AUDIO index
    if "AUDIO" not in existing_labels:
        db.ai.indexes.create({
            "label": "AUDIO",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print("    ✓ Created AUDIO.description vector index")
    else:
        print("    ℹ AUDIO.description index already exists")
    
    # Create CONCEPT index
    if "CONCEPT" not in existing_labels:
        db.ai.indexes.create({
            "label": "CONCEPT",
            "propertyName": "description",
            "sourceType": "external",
            "dimensions": EMBEDDING_DIM,
            "similarityFunction": "cosine"
        })
        print("    ✓ Created CONCEPT.description vector index")
    else:
        print("    ℹ CONCEPT.description index already exists")
    
    print("\n[5/5] Waiting for indexes to be ready...")
    time.sleep(2)  # Brief pause for index initialization
    
    print("\n" + "="*60)
    print("SEEDING COMPLETE")
    print("="*60)
    print(f"  • {len(concept_map)} CONCEPT anchor nodes")
    print(f"  • {len(image_records)} IMAGE records with embeddings")
    print(f"  • {len(audio_records)} AUDIO records with embeddings")
    print(f"  • Cross-modal relationships via concept nodes")
    print(f"  • Vector indexes ready for semantic search")
    print("\nRun `python main.py --mode demo` to see cross-modal queries in action.")


if __name__ == "__main__":
    main()
