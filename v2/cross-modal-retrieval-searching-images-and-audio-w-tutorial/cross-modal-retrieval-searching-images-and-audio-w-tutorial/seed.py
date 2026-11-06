"""
Seed script for Cross-Modal Retrieval Tutorial

Generates sample data for images and audio with realistic metadata.
The sample data represents a multimedia collection with shared categories
that will be used for cross-modal retrieval demonstrations.
"""

import json
import random
import os
from pathlib import Path

# Sample data configuration

CATEGORIES = [
    "nature", "urban", "people", "technology", "music",
    "sports", "animals", "food", "travel", "art"
]

MOODS = [
    "calm", "energetic", "melancholic", "uplifting",
    "mysterious", "playful", "serious", "whimsical"
]

# Image descriptions - realistic, varied content
IMAGE_DESCRIPTIONS = [
    {"description": "A serene mountain lake at dawn with mist rising from the water surface", "category": "nature", "mood": "calm"},
    {"description": "Busy city street with neon signs reflecting on wet pavement at night", "category": "urban", "mood": "energetic"},
    {"description": "Child laughing while playing in a autumn leaf pile", "category": "people", "mood": "uplifting"},
    {"description": "Close-up of server racks with blinking LED lights in a data center", "category": "technology", "mood": "mysterious"},
    {"description": "Acoustic guitar on a wooden floor next to an open window with sunlight", "category": "music", "mood": "calm"},
    {"description": "Soccer player scoring a goal with crowd cheering in background", "category": "sports", "mood": "energetic"},
    {"description": "Golden retriever running through a field of wildflowers", "category": "animals", "mood": "playful"},
    {"description": "Artisan pizza being pulled from a wood-fired oven", "category": "food", "mood": "whimsical"},
    {"description": "Sunset over Santorini white buildings and blue domes", "category": "travel", "mood": "calm"},
    {"description": "Abstract painting with bold colors and geometric shapes", "category": "art", "mood": "mysterious"},
    {"description": "Waterfall cascading down mossy rocks in a tropical rainforest", "category": "nature", "mood": "calm"},
    {"description": "Tokyo street crossing at rush hour with hundreds of pedestrians", "category": "urban", "mood": "energetic"},
    {"description": "Elderly couple dancing together in a dimly lit ballroom", "category": "people", "mood": "melancholic"},
    {"description": "Futuristic robotics arm assembling electronic components", "category": "technology", "mood": "serious"},
    {"description": "Vinyl record spinning on a turntable with warm light glow", "category": "music", "mood": "whimsical"},
    {"description": "Basketball player mid-dunk with dramatic lighting", "category": "sports", "mood": "energetic"},
    {"description": "Cat sleeping on a pile of colorful books", "category": "animals", "mood": "calm"},
    {"description": "Elaborate sushi platter with fresh ingredients and garnishes", "category": "food", "mood": "playful"},
    {"description": "Moroccan marketplace with colorful spices and textiles", "category": "travel", "mood": "energetic"},
    {"description": "Sculpture made of recycled metal pieces forming a human figure", "category": "art", "mood": "serious"},
    {"description": "Northern lights dancing over a frozen Arctic lake", "category": "nature", "mood": "mysterious"},
    {"description": "Abandoned factory with vines growing through broken windows", "category": "urban", "mood": "melancholic"},
    {"description": "Musician performing solo piano on an empty stage", "category": "music", "mood": "melancholic"},
    {"description": "Close-up of a hummingbird feeding from a bright flower", "category": "animals", "mood": "playful"},
    {"description": "Parisian cafe terrace with croissants and coffee on a清晨 table", "category": "travel", "mood": "calm"},
]

# Audio descriptions - matching the multimodal theme
audio_descriptions = [
    {"description": "Gentle rain on forest leaves with distant bird calls", "category": "nature", "mood": "calm"},
    {"description": "Busy subway station with announcements and footsteps", "category": "urban", "mood": "energetic"},
    {"description": "Children playing and laughing in a playground", "category": "people", "mood": "uplifting"},
    {"description": "Electronic hum and beeps from computer terminals", "category": "technology", "mood": "mysterious"},
    {"description": "Acoustic guitar fingerpicking pattern with warm reverb", "category": "music", "mood": "calm"},
    {"description": "Crowd cheering and stadium anthem for championship game", "category": "sports", "mood": "energetic"},
    {"description": "Dog barking and running through grass", "category": "animals", "mood": "playful"},
    {"description": "Sizzling sounds from a grill with meat hitting hot surface", "category": "food", "mood": "whimsical"},
    {"description": "Ocean waves crashing on rocky shore at sunset", "category": "travel", "mood": "calm"},
    {"description": "Experimental electronic music with industrial textures", "category": "art", "mood": "mysterious"},
    {"description": "Thunderstorm approaching with wind through trees", "category": "nature", "mood": "serious"},
    {"description": "Traffic sounds and car horns in a downtown intersection", "category": "urban", "mood": "energetic"},
    {"description": "Heartfelt conversation between two people sharing stories", "category": "people", "mood": "melancholic"},
    {"description": "Mechanical keyboard typing and mouse clicks", "category": "technology", "mood": "serious"},
    {"description": "Jazz quartet improvisation with piano, bass, drums, sax", "category": "music", "mood": "uplifting"},
    {"description": "Whistle and crowd roar during a running race finish", "category": "sports", "mood": "energetic"},
    {"description": "Cat purring and meowing softly while being petted", "category": "animals", "mood": "calm"},
    {"description": "Clinking glasses and chatter in a busy restaurant kitchen", "category": "food", "mood": "playful"},
    {"description": "Traditional market sounds with merchants and customers bargaining", "category": "travel", "mood": "energetic"},
    {"description": "Dramatic orchestral crescendo with strings and percussion", "category": "art", "mood": "serious"},
    {"description": "Stream flowing over smooth stones in a quiet forest glade", "category": "nature", "mood": "calm"},
    {"description": "Sirens and emergency vehicle sounds in city traffic", "category": "urban", "mood": "mysterious"},
    {"description": "Soft piano melody with minor chord progressions", "category": "music", "mood": "melancholic"},
    {"description": "Bird songs at dawn with morning chorus", "category": "animals", "mood": "uplifting"},
    {"description": "Train station announcement with departure sounds", "category": "travel", "mood": "serious"},
]


def generate_sample_data():
    """Generate sample data for images and audio."""
    
    images = []
    audio_files = []
    concepts = []
    
    # Generate image records
    for i, img in enumerate(IMAGE_DESCRIPTIONS):
        images.append({
            "id": f"img_{i+1:03d}",
            "file_path": f"/sample_data/images/{img['category']}_{i+1}.jpg",
            "description": img["description"],
            "category": img["category"],
            "mood": img["mood"],
            "tags": random.sample(["landscape", "portrait", "close-up", "wide-angle", "macro", "aerial"], 3)
        })
    
    # Generate audio records
    for i, aud in enumerate(audio_descriptions):
        audio_files.append({
            "id": f"aud_{i+1:03d}",
            "file_path": f"/sample_data/audio/{aud['category']}_{i+1}.wav",
            "description": aud["description"],
            "category": aud["category"],
            "mood": aud["mood"],
            "duration_seconds": random.randint(30, 300),
            "sample_rate": random.choice([44100, 48000])
        })
    
    # Generate concept nodes for cross-modal linking
    concept_data = [
        {"id": "concept_nature", "name": "nature", "type": "category", "description": "Natural environments and elements"},
        {"id": "concept_urban", "name": "urban", "type": "category", "description": "City and metropolitan environments"},
        {"id": "concept_people", "name": "people", "type": "category", "description": "Human subjects and activities"},
        {"id": "concept_technology", "name": "technology", "type": "category", "description": "Tech-related content and devices"},
        {"id": "concept_music", "name": "music", "type": "category", "description": "Musical content and instruments"},
        {"id": "concept_sports", "name": "sports", "type": "category", "description": "Sports and athletic activities"},
        {"id": "concept_animals", "name": "animals", "type": "category", "description": "Animal subjects"},
        {"id": "concept_food", "name": "food", "type": "category", "description": "Culinary and food content"},
        {"id": "concept_travel", "name": "travel", "type": "category", "description": "Travel and destinations"},
        {"id": "concept_art", "name": "art", "type": "category", "description": "Artistic and creative content"},
        {"id": "concept_calm", "name": "calm", "type": "mood", "description": "Peaceful and serene atmosphere"},
        {"id": "concept_energetic", "name": "energetic", "type": "mood", "description": "High energy and dynamic atmosphere"},
        {"id": "concept_melancholic", "name": "melancholic", "type": "mood", "description": "Reflective and emotional atmosphere"},
        {"id": "concept_uplifting", "name": "uplifting", "type": "mood", "description": "Positive and inspiring atmosphere"},
        {"id": "concept_mysterious", "name": "mysterious", "type": "mood", "description": "Intriguing and enigmatic atmosphere"},
        {"id": "concept_playful", "name": "playful", "type": "mood", "description": "Fun and lighthearted atmosphere"},
    ]
    
    for concept in concept_data:
        concepts.append(concept)
    
    return {
        "images": images,
        "audio": audio_files,
        "concepts": concepts
    }


def main():
    """Generate and save sample data."""
    print("Generating sample data for cross-modal retrieval tutorial...")
    
    data = generate_sample_data()
    
    # Create data directory if it doesn't exist
    data_dir = Path(__file__).parent / "data"
    data_dir.mkdir(exist_ok=True)
    
    # Save to JSON
    output_path = data_dir / "sample_data.json"
    with open(output_path, "w") as f:
        json.dump(data, f, indent=2)
    
    print(f"\n✅ Sample data generated successfully!")
    print(f"   - {len(data['images'])} images")
    print(f"   - {len(data['audio'])} audio files")
    print(f"   - {len(data['concepts'])} concept nodes")
    print(f"   Saved to: {output_path}")
    print("\nRun 'python main.py' to start the cross-modal retrieval tutorial.")


if __name__ == "__main__":
    main()
