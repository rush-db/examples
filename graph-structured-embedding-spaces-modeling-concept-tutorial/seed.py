"""
Seed script for Graph-Structured Embedding Spaces tutorial.

Creates a concept hierarchy around software architecture and design patterns.
Idempotent: safe to run multiple times (checks for existing data first).
"""

import os
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.getenv("RUSHDB_API_KEY")
def get_db():
    if not API_KEY:
        raise ValueError("RUSHDB_API_KEY environment variable is not set")
    return RushDB(API_KEY)


def check_existing_data(db):
    """Check if concepts already exist to avoid duplicate seeding."""
    result = db.records.find({"labels": ["DOMAIN"], "limit": 1})
    return len(result.data) > 0


def seed_concepts(db):
    """Create the complete concept graph with relationships."""
    print("Seeding concept graph...\n")
    
    # ============================================================
    # DOMAIN LEVEL — Top of the hierarchy
    # ============================================================
    design_patterns = db.records.create(
        label="DOMAIN",
        data={
            "name": "Design Patterns",
            "description": "Reusable solutions to commonly occurring problems in software design"
        },
        vectors=[{"propertyName": "description", "vector": [0.1, 0.3, 0.5, 0.7, 0.2]}]
    )
    print(f"Created DOMAIN: {design_patterns.data['name']}")
    
    software_arch = db.records.create(
        label="DOMAIN",
        data={
            "name": "Software Architecture",
            "description": "Fundamental structures of a software system and the discipline of creating such structures"
        },
        vectors=[{"propertyName": "description", "vector": [0.4, 0.6, 0.2, 0.8, 0.1]}]
    )
    print(f"Created DOMAIN: {software_arch.data['name']}")
    
    # Connect domains
    db.records.attach(
        source=design_patterns,
        target=software_arch,
        options={"type": "BELONGS_TO"}
    )
    print("  └─ BELONGS_TO → Software Architecture")
    
    # ============================================================
    # CATEGORY LEVEL — Groupings within domains
    # ============================================================
    creational = db.records.create(
        label="CATEGORY",
        data={
            "name": "Creational Patterns",
            "description": "Design patterns that deal with object creation mechanisms"
        },
        vectors=[{"propertyName": "description", "vector": [0.2, 0.4, 0.6, 0.5, 0.3]}]
    )
    structural = db.records.create(
        label="CATEGORY",
        data={
            "name": "Structural Patterns",
            "description": "Design patterns that ease the design by identifying a simple way to realize relationships between entities"
        },
        vectors=[{"propertyName": "description", "vector": [0.3, 0.5, 0.4, 0.6, 0.2]}]
    )
    behavioral = db.records.create(
        label="CATEGORY",
        data={
            "name": "Behavioral Patterns",
            "description": "Design patterns that identify common communication patterns between objects"
        },
        vectors=[{"propertyName": "description", "vector": [0.4, 0.3, 0.7, 0.4, 0.5]}]
    )
    print(f"\nCreated CATEGORY: {creational.data['name']}")
    print(f"Created CATEGORY: {structural.data['name']}")
    print(f"Created CATEGORY: {behavioral.data['name']}")
    
    # Connect categories to domain
    for category in [creational, structural, behavioral]:
        db.records.attach(
            source=category,
            target=design_patterns,
            options={"type": "BELONGS_TO"}
        )
    print("  └─ All categories attached to Design Patterns")
    
    # ============================================================
    # CONCEPT LEVEL — Individual patterns
    # ============================================================
    concepts_data = [
        # Creational patterns
        ("Factory Method", "Provides an interface for creating objects in a superclass, allowing subclasses to alter the type", 
         creational, [0.2, 0.3, 0.7, 0.4, 0.3], ["abstract", "factory", "creation", "subclass"]),
        ("Abstract Factory", "Provides an interface for creating families of related objects without specifying their concrete classes",
         creational, [0.3, 0.2, 0.6, 0.5, 0.4], ["abstract", "family", "creation", "interface"]),
        ("Builder", "Separates the construction of a complex object from its representation",
         creational, [0.1, 0.5, 0.6, 0.3, 0.4], ["construction", "stepwise", "complex", "fluent"]),
        ("Singleton", "Ensures a class has only one instance and provides a global point of access to it",
         creational, [0.4, 0.4, 0.3, 0.2, 0.5], ["single", "instance", "global", "restricted"]),
        
        # Structural patterns
        ("Adapter", "Allows objects with incompatible interfaces to collaborate",
         structural, [0.5, 0.4, 0.3, 0.6, 0.2], ["compatibility", "wrapper", "interface", "translation"]),
        ("Bridge", "Separates an abstraction from its implementation so that the two can vary independently",
         structural, [0.4, 0.3, 0.5, 0.7, 0.3], ["abstraction", "implementation", "decouple", "independent"]),
        ("Decorator", "Attaches new behaviors to objects by placing them inside wrapper objects",
         structural, [0.2, 0.6, 0.4, 0.3, 0.5], ["wrapper", "enhance", "dynamic", "composition"]),
        ("Facade", "Provides a simplified interface to a complex subsystem",
         structural, [0.3, 0.4, 0.2, 0.5, 0.4], ["simplified", "interface", "complex", "abstraction"]),
        
        # Behavioral patterns
        ("Observer", "Defines a subscription mechanism to notify multiple objects about events",
         behavioral, [0.4, 0.3, 0.6, 0.4, 0.3], ["subscription", "notification", "event", "dependency"]),
        ("Strategy", "Defines a family of algorithms, encapsulates each one, and makes them interchangeable",
         behavioral, [0.3, 0.5, 0.4, 0.3, 0.4], ["algorithm", "interchangeable", "family", "encapsulated"]),
        ("Command", "Encapsulates a request as an object, allowing parameterization and queuing",
         behavioral, [0.2, 0.4, 0.5, 0.4, 0.4], ["request", "encapsulated", "parameterized", "undoable"]),
        ("State", "Allows an object to alter its behavior when its internal state changes",
         behavioral, [0.5, 0.3, 0.4, 0.3, 0.5], ["state", "behavior", "change", "context"]),
    ]
    
    concepts = []
    for i, (name, desc, category, vec, tags) in enumerate(concepts_data):
        concept = db.records.create(
            label="CONCEPT",
            data={
                "name": name,
                "description": desc,
                "tags": tags
            },
            vectors=[{"propertyName": "description", "vector": vec}]
        )
        concepts.append(concept)
        
        # Connect to category
        db.records.attach(
            source=concept,
            target=category,
            options={"type": "IS_A"}
        )
        
        if (i + 1) % 4 == 0:
            print(f"Created 4 CONCEPTs...")
    
    print(f"\nCreated {len(concepts)} CONCEPT records")
    
    # ============================================================
    # ARCHITECTURAL STYLES — Software architecture domain
    # ============================================================
    arch_styles = [
        ("Monolithic Architecture", "All components in a single deployable unit with shared codebase", [0.3, 0.2, 0.4, 0.6, 0.3]),
        ("Microservices Architecture", "System divided into small, independent services that communicate via APIs", [0.4, 0.5, 0.3, 0.7, 0.4]),
        ("Event-Driven Architecture", "System reacts to events and processes them asynchronously", [0.5, 0.4, 0.6, 0.3, 0.5]),
        ("Layered Architecture", "System organized in layers with specific responsibilities", [0.2, 0.3, 0.3, 0.5, 0.3]),
        ("Hexagonal Architecture", "Core business logic isolated from external concerns via ports and adapters", [0.3, 0.5, 0.5, 0.4, 0.4]),
    ]
    
    arch_concepts = []
    for name, desc, vec in arch_styles:
        concept = db.records.create(
            label="ARCHITECTURE",
            data={"name": name, "description": desc},
            vectors=[{"propertyName": "description", "vector": vec}]
        )
        arch_concepts.append(concept)
        
        db.records.attach(
            source=concept,
            target=software_arch,
            options={"type": "IS_A"}
        )
    
    print(f"Created {len(arch_concepts)} ARCHITECTURE records")
    
    # ============================================================
    # EXPLICIT SIMILARITY RELATIONSHIPS
    # These represent "nearby" concepts in the embedding space
    # ============================================================
    similarity_pairs = [
        # Factory Method and Abstract Factory — both deal with object creation
        (concepts[0], concepts[1], " closely related creation patterns"),
        # Builder and Factory — alternative creation mechanisms
        (concepts[2], concepts[0], " alternative creation strategies"),
        # Adapter and Bridge — structural composition patterns
        (concepts[4], concepts[5], " structural patterns with composition"),
        # Observer and State — both deal with state changes
        (concepts[8], concepts[11], " patterns involving state management"),
        # Strategy and Command — behavioral patterns for flexibility
        (concepts[9], concepts[10], " interchangeable behavior patterns"),
        # Adapter and Decorator — both wrap objects
        (concepts[4], concepts[6], " wrapper patterns"),
        # Facade and Adapter — both provide interfaces
        (concepts[7], concepts[4], " interface patterns"),
        # Microservices and Event-Driven — related distributed patterns
        (arch_concepts[1], arch_concepts[2], " distributed system patterns"),
        # Hexagonal and Layered — both organize code structure
        (arch_concepts[4], arch_concepts[3], " structural organization patterns"),
    ]
    
    for source, target, note in similarity_pairs:
        db.records.attach(
            source=source,
            target=target,
            options={"type": "RELATED_TO"}
        )
    
    print(f"\nCreated {len(similarity_pairs)} RELATED_TO relationships")
    
    # ============================================================
    # PREREQUISITE RELATIONSHIPS
    # Concept A is prerequisite for Concept B (learning order)
    # ============================================================
    prereq_pairs = [
        # Must understand singleton before understanding abstract factory
        (concepts[3], concepts[1]),
        # Decorator builds on adapter understanding
        (concepts[4], concepts[6]),
        # Observer requires understanding events
        (arch_concepts[2], concepts[8]),
        # Layered architecture is foundational
        (arch_concepts[3], arch_concepts[4]),
    ]
    
    for prereq, dependent in prereq_pairs:
        db.records.attach(
            source=prereq,
            target=dependent,
            options={"type": "PREREQUISITE_FOR"}
        )
    
    print(f"Created {len(prereq_pairs)} PREREQUISITE_FOR relationships")
    print("\n" + "=" * 60)
    print("Seeding complete! Concept graph ready for traversal.")
    print("=" * 60)


if __name__ == "__main__":
    db = get_db()
    
    if check_existing_data(db):
        print("Data already exists. Skipping seed.")
        print("Delete existing records or run on a fresh project to reseed.")
    else:
        seed_concepts(db)
