"""
Seed script: Creates time-series sensor events and temporal relationships in RushDB.

This script generates mock IoT/sensor data for a smart building and connects
events with temporal relationships to enable reasoning over sequences.

Run: python seed.py
"""

import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found in environment. Copy .env.example to .env")

db = RushDB(API_KEY)

# ============================================================================
# Event Types and Temporal Relationship Types
# ============================================================================

TEMPORAL_RELATIONSHIPS = {
    "CAUSED": "Event A directly caused Event B",
    "TRIGGERED_BY": "Event B was triggered by Event A",
    "BEFORE": "Event A happened before Event B (no direct causation)",
    "PRECEDED": "Event A preceded Event B in a sequence",
}

EVENT_TYPES = [
    "TEMPERATURE_ALERT",
    "HVAC_ADJUSTMENT",
    "OCCUPANCY_CHANGE",
    "POWER_SURGE",
    "DOOR_ACCESS",
    "LIGHTING_CHANGE",
    "SECURITY_ALERT",
    "SYSTEM_ERROR",
]

# ============================================================================
# Generate Mock Time-Series Data
# ============================================================================

def generate_sensor_events(num_floors: int = 3, hours: int = 24) -> list[dict]:
    """
    Generate realistic sensor events for a smart building.
    Events include alerts, adjustments, and state changes.
    """
    events = []
    base_time = datetime.now() - timedelta(hours=hours)
    
    # Sensor IDs per floor
    sensors = {
        f"floor_{i}": {
            "temp": f"TEMP-{i:02d}",
            "door": f"DOOR-{i:02d}",
            "power": f"POWER-{i:02d}",
            "motion": f"MOTION-{i:02d}",
        }
        for i in range(1, num_floors + 1)
    }
    
    event_sequence = 0
    
    for minute_offset in range(hours * 60):
        current_time = base_time + timedelta(minutes=minute_offset)
        minute = current_time.minute
        hour = current_time.hour
        
        # Temperature fluctuations (every 15 minutes per floor)
        if minute % 15 == 0:
            for floor_id, floor_sensors in sensors.items():
                floor_num = int(floor_id.split("_")[1])
                event_sequence += 1
                
                # Temperature varies by floor (higher floors warmer)
                base_temp = 20 + (floor_num * 0.5)
                temp_change = ((minute_offset % 60) - 30) * 0.1
                
                events.append({
                    "event_id": f"EVT-{event_sequence:05d}",
                    "type": "TEMPERATURE_ALERT",
                    "sensor_id": floor_sensors["temp"],
                    "floor": floor_num,
                    "timestamp": current_time.isoformat(),
                    "value": round(base_temp + temp_change, 1),
                    "threshold": 25.0,
                    "severity": "WARNING" if temp_change > 0 else "INFO",
                })
        
        # HVAC adjustments (triggered by temperature, ~30 min after alerts)
        if minute % 30 == 10:
            for floor_id, floor_sensors in sensors.items():
                floor_num = int(floor_id.split("_")[1])
                event_sequence += 1
                
                events.append({
                    "event_id": f"EVT-{event_sequence:05d}",
                    "type": "HVAC_ADJUSTMENT",
                    "sensor_id": f"HVAC-{floor_num:02d}",
                    "floor": floor_num,
                    "timestamp": current_time.isoformat(),
                    "action": "COOLING" if minute_offset % 2 == 0 else "HEATING",
                    "previous_temp": round(22 + (floor_num * 0.3), 1),
                    "target_temp": round(21 + (floor_num * 0.3), 1),
                    "severity": "INFO",
                })
        
        # Occupancy changes (morning arrival, evening departure)
        if hour in [8, 9, 10, 17, 18, 19]:
            if minute in [0, 15, 30, 45]:
                for floor_id, floor_sensors in sensors.items():
                    floor_num = int(floor_id.split("_")[1])
                    event_sequence += 1
                    
                    is_arrival = hour in [8, 9, 10]
                    occupancy_delta = 5 if is_arrival else -5
                    
                    events.append({
                        "event_id": f"EVT-{event_sequence:05d}",
                        "type": "OCCUPANCY_CHANGE",
                        "sensor_id": floor_sensors["motion"],
                        "floor": floor_num,
                        "timestamp": current_time.isoformat(),
                        "occupancy_delta": occupancy_delta,
                        "trigger": "ARRIVAL" if is_arrival else "DEPARTURE",
                        "severity": "INFO",
                    })
        
        # Power surges (rare, random)
        if minute_offset % 97 == 0 or minute_offset % 151 == 0:
            floor_num = (minute_offset % num_floors) + 1
            floor_sensors = sensors[f"floor_{floor_num}"]
            event_sequence += 1
            
            events.append({
                "event_id": f"EVT-{event_sequence:05d}",
                "type": "POWER_SURGE",
                "sensor_id": floor_sensors["power"],
                "floor": floor_num,
                "timestamp": current_time.isoformat(),
                "voltage_spike": round(220 + (minute_offset % 50), 1),
                "duration_ms": 50,
                "severity": "CRITICAL",
            })
        
        # Door access events
        if minute in [0, 20, 40]:
            for floor_id, floor_sensors in sensors.items():
                floor_num = int(floor_id.split("_")[1])
                event_sequence += 1
                
                users = ["alice", "bob", "charlie", "diana", "evan"]
                
                events.append({
                    "event_id": f"EVT-{event_sequence:05d}",
                    "type": "DOOR_ACCESS",
                    "sensor_id": floor_sensors["door"],
                    "floor": floor_num,
                    "timestamp": current_time.isoformat(),
                    "user": users[minute_offset % len(users)],
                    "action": "GRANTED" if minute_offset % 10 != 0 else "DENIED",
                    "severity": "WARNING" if minute_offset % 10 == 0 else "INFO",
                })
        
        # Lighting changes (correlated with occupancy)
        if hour in [7, 8, 17, 18] and minute in [0, 30]:
            for floor_id, floor_sensors in sensors.items():
                floor_num = int(floor_id.split("_")[1])
                event_sequence += 1
                
                events.append({
                    "event_id": f"EVT-{event_sequence:05d}",
                    "type": "LIGHTING_CHANGE",
                    "sensor_id": f"LIGHT-{floor_num:02d}",
                    "floor": floor_num,
                    "timestamp": current_time.isoformat(),
                    "action": "ON" if hour < 12 else "OFF",
                    "brightness": 100 if hour < 12 else 0,
                    "severity": "INFO",
                })
    
    return events


def generate_temporal_relationships(events: list[dict]) -> list[tuple]:
    """
    Generate temporal relationships between events based on causality patterns.
    
    Returns list of tuples: (source_event_id, target_event_id, relationship_type, metadata)
    """
    relationships = []
    
    # Index events by floor and type for quick lookup
    events_by_floor = {}
    for evt in events:
        floor = evt["floor"]
        if floor not in events_by_floor:
            events_by_floor[floor] = []
        events_by_floor[floor].append(evt)
    
    # Create temporal links based on event patterns
    for floor, floor_events in events_by_floor.items():
        # Sort by timestamp
        floor_events.sort(key=lambda e: e["timestamp"])
        
        temp_alerts = [e for e in floor_events if e["type"] == "TEMPERATURE_ALERT"]
        hvac_adjustments = [e for e in floor_events if e["type"] == "HVAC_ADJUSTMENT"]
        occupancy_changes = [e for e in floor_events if e["type"] == "OCCUPANCY_CHANGE"]
        lighting_changes = [e for e in floor_events if e["type"] == "LIGHTING_CHANGE"]
        power_surges = [e for e in floor_events if e["type"] == "POWER_SURGE"]
        door_access = [e for e in floor_events if e["type"] == "DOOR_ACCESS"]
        
        # CAUSED: Temperature alert -> HVAC adjustment (30 min delay)
        for i, temp_evt in enumerate(temp_alerts):
            # Find the next HVAC event after this temp event
            temp_time = datetime.fromisoformat(temp_evt["timestamp"])
            for hvac_evt in hvac_adjustments:
                hvac_time = datetime.fromisoformat(hvac_evt["timestamp"])
                if 25 <= (hvac_time - temp_time).total_seconds() / 60 <= 35:
                    relationships.append((
                        temp_evt["event_id"],
                        hvac_evt["event_id"],
                        "CAUSED",
                        {"delay_minutes": round((hvac_time - temp_time).total_seconds() / 60, 1)}
                    ))
                    break
        
        # TRIGGERED_BY: Occupancy change -> Lighting change
        for occ_evt in occupancy_changes:
            occ_time = datetime.fromisoformat(occ_evt["timestamp"])
            for light_evt in lighting_changes:
                light_time = datetime.fromisoformat(light_evt["timestamp"])
                time_diff = (light_time - occ_time).total_seconds() / 60
                if 0 <= time_diff <= 5:
                    relationships.append((
                        occ_evt["event_id"],
                        light_evt["event_id"],
                        "TRIGGERED_BY",
                        {"delay_minutes": round(time_diff, 1)}
                    ))
                    break
        
        # CAUSED: Power surge -> Security alert (if severity is CRITICAL)
        for power_evt in power_surges:
            if power_evt["severity"] == "CRITICAL":
                power_time = datetime.fromisoformat(power_evt["timestamp"])
                # Look for security alerts within 5 minutes
                for other_evt in floor_events:
                    other_time = datetime.fromisoformat(other_evt["timestamp"])
                    time_diff = (other_time - power_time).total_seconds() / 60
                    if 0 < time_diff <= 5 and other_evt["type"] not in ["POWER_SURGE"]:
                        relationships.append((
                            power_evt["event_id"],
                            other_evt["event_id"],
                            "CAUSED",
                            {"delay_minutes": round(time_diff, 1)}
                        ))
                        break
        
        # BEFORE: Door access followed by occupancy change
        for door_evt in door_access:
            if door_evt.get("action") == "GRANTED":
                door_time = datetime.fromisoformat(door_evt["timestamp"])
                for occ_evt in occupancy_changes:
                    occ_time = datetime.fromisoformat(occ_evt["timestamp"])
                    time_diff = (occ_time - door_time).total_seconds() / 60
                    if 0 < time_diff <= 3:
                        relationships.append((
                            door_evt["event_id"],
                            occ_evt["event_id"],
                            "PRECEDED",
                            {"delay_minutes": round(time_diff, 1)}
                        ))
                        break
        
        # PRECEDED: Sequential HVAC adjustments in same zone
        for i in range(len(hvac_adjustments) - 1):
            current = hvac_adjustments[i]
            next_evt = hvac_adjustments[i + 1]
            current_time = datetime.fromisoformat(current["timestamp"])
            next_time = datetime.fromisoformat(next_evt["timestamp"])
            time_diff = (next_time - current_time).total_seconds() / 60
            
            if time_diff <= 60:  # Within 1 hour
                relationships.append((
                    current["event_id"],
                    next_evt["event_id"],
                    "PRECEDED",
                    {"delay_minutes": round(time_diff, 1)}
                ))
    
    return relationships


# ============================================================================
# Seed the Database
# ============================================================================

def seed_database():
    """Create time-series events and temporal relationships in RushDB."""
    print("=" * 60)
    print("RUSHDB TIME-SERIES SEED SCRIPT")
    print("=" * 60)
    
    # Check if data already exists
    existing = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "limit": 1
    })
    
    if existing.total > 0:
        print(f"\n✓ Found {existing.total} existing SENSOR_EVENT records.")
        print("  Skipping seed (data already exists).")
        print("  To re-seed, delete existing records first.")
        return False
    
    print("\n1. Generating sensor events...")
    events = generate_sensor_events(num_floors=3, hours=24)
    print(f"   Generated {len(events)} events")
    
    print("\n2. Generating temporal relationships...")
    relationships = generate_temporal_relationships(events)
    print(f"   Generated {len(relationships)} temporal relationships")
    
    print("\n3. Creating events in RushDB (batched)...")
    
    # Create events in batches
    batch_size = 100
    event_records = []
    
    for i in range(0, len(events), batch_size):
        batch = events[i:i + batch_size]
        records = db.records.create_many(
            label="SENSOR_EVENT",
            data=batch
        )
        event_records.extend(records)
        print(f"   Created batch {i // batch_size + 1}: {len(records)} events")
    
    # Build event_id -> record mapping
    print("\n4. Building event index...")
    event_id_to_record = {}
    for record in event_records:
        event_id = record.fields.get("event_id")
        if event_id:
            event_id_to_record[event_id] = record
    
    print(f"   Indexed {len(event_id_to_record)} records")
    
    print("\n5. Creating temporal relationships...")
    rel_count = 0
    for source_id, target_id, rel_type, metadata in relationships:
        source_record = event_id_to_record.get(source_id)
        target_record = event_id_to_record.get(target_id)
        
        if source_record and target_record:
            db.records.attach(
                source=source_record,
                target=target_record,
                options={"type": rel_type}
            )
            rel_count += 1
            
            if rel_count % 50 == 0:
                print(f"   Created {rel_count} relationships...")
    
    print(f"\n6. Created {rel_count} temporal relationships")
    
    print("\n" + "=" * 60)
    print("SEED COMPLETE")
    print("=" * 60)
    print(f"\nSummary:")
    print(f"  • {len(event_records)} SENSOR_EVENT records")
    print(f"  • {rel_count} temporal relationships")
    print(f"  • Event types: {', '.join(EVENT_TYPES[:4])}...")
    print(f"\nRun 'python main.py' to demonstrate temporal reasoning!")
    
    return True


if __name__ == "__main__":
    seed_database()
