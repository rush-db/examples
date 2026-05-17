"""
Time-Series Reasoning with Temporal Edges in RushDB
====================================================

This tutorial demonstrates how to use RushDB for time-series reasoning
by modeling events as records connected with temporal relationships.

Key patterns demonstrated:
1. Time-range queries using temporal properties
2. Temporal edge traversal (following BEFORE/AFTER relationships)
3. Causal chain discovery (following CAUSED relationships)
4. Sequence pattern detection (PRECEDED relationships)
5. Aggregation over temporal paths

Run: python main.py
(First run: python seed.py to create sample data)
"""

import os
from datetime import datetime, timedelta
from collections import defaultdict
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY not found. Copy .env.example to .env")

db = RushDB(API_KEY)

# ============================================================================
# SECTION 1: TIME-RANGE QUERIES
# ============================================================================

def query_events_in_time_range():
    """
    Find all sensor events within a specific time window.
    This is the foundational time-series query pattern.
    """
    print("\n" + "=" * 60)
    print("1. TIME-RANGE QUERIES")
    print("=" * 60)
    
    # Define time range: last 6 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=6)
    
    print(f"\nQuery: Events between {start_time.isoformat()} and {end_time.isoformat()}")
    print("-" * 50)
    
    # Query using timestamp field comparison
    # Note: In RushDB, we filter by the stored timestamp property
    result = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "timestamp": {
                "$gte": start_time.isoformat(),
                "$lte": end_time.isoformat()
            }
        },
        "limit": 10,
        "orderBy": {"field": "timestamp", "direction": "asc"}
    })
    
    print(f"\nFound {result.total} events in time range")
    
    # Group by type
    events_by_type = defaultdict(list)
    for record in result.data:
        events_by_type[record.fields.get("type", "UNKNOWN")].append(record)
    
    print("\nEvents by type:")
    for event_type, events in sorted(events_by_type.items()):
        print(f"  • {event_type}: {len(events)} events")
    
    return result


# ============================================================================
# SECTION 2: TEMPORAL EDGE TRAVERSAL
# ============================================================================

def traverse_temporal_edges():
    """
    Traverse events connected by temporal relationships.
    RushDB's graph structure lets us follow edges between events.
    """
    print("\n" + "=" * 60)
    print("2. TEMPORAL EDGE TRAVERSAL")
    print("=" * 60)
    
    # Find a CRITICAL event (power surge) to start traversal
    critical_events = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "severity": "CRITICAL"
        },
        "limit": 1
    })
    
    if critical_events.total == 0:
        print("\nNo critical events found. Run seed.py first!")
        return
    
    start_event = critical_events.data[0]
    print(f"\nStarting from CRITICAL event: {start_event.fields.get('event_id')}")
    print(f"  Type: {start_event.fields.get('type')}")
    print(f"  Floor: {start_event.fields.get('floor')}")
    print(f"  Time: {start_event.fields.get('timestamp')}")
    
    print("\nFollowing CAUSED relationships...")
    print("-" * 50)
    
    # Use $relation filter to traverse edges
    # Find events that were CAUSED by the critical event
    downstream = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "SENSOR_EVENT": {
                "$relation": {"type": "CAUSED", "direction": "in"},
                "$source": {"event_id": start_event.fields.get("event_id")}
            }
        },
        "limit": 5
    })
    
    print(f"\nEvents caused by this critical event: {downstream.total}")
    for event in downstream.data[:3]:
        print(f"  • {event.fields.get('event_id')}: {event.fields.get('type')}")
        print(f"    at {event.fields.get('timestamp')}")
    
    # Find events that PRECEDED this critical event
    upstream = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "SENSOR_EVENT": {
                "$relation": {"type": "PRECEDED", "direction": "in"},
                "$source": {"event_id": start_event.fields.get("event_id")}
            }
        },
        "limit": 5
    })
    
    print(f"\nEvents that preceded this event: {upstream.total}")
    for event in upstream.data[:3]:
        print(f"  • {event.fields.get('event_id')}: {event.fields.get('type')}")
        print(f"    at {event.fields.get('timestamp')}")
    
    return start_event, downstream, upstream


# ============================================================================
# SECTION 3: CAUSAL CHAIN DISCOVERY
# ============================================================================

def discover_causal_chains():
    """
    Trace causal chains through multiple levels of CAUSED relationships.
    This demonstrates RushDB's ability to reason about event provenance.
    """
    print("\n" + "=" * 60)
    print("3. CAUSAL CHAIN DISCOVERY")
    print("=" * 60)
    
    # Find events with CAUSED relationships
    # We'll look for TEMPERATURE_ALERT -> HVAC_ADJUSTMENT chains
    temp_alerts = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "type": "TEMPERATURE_ALERT"
        },
        "limit": 5
    })
    
    print(f"\nFinding causal chains starting from TEMPERATURE_ALERT events...")
    print("-" * 50)
    
    chains_found = 0
    
    for temp_event in temp_alerts.data[:3]:
        event_id = temp_event.fields.get("event_id")
        timestamp = temp_event.fields.get("timestamp")
        floor = temp_event.fields.get("floor")
        
        # Find HVAC events that this temp alert CAUSED
        caused_hvac = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "type": "HVAC_ADJUSTMENT",
                "floor": floor,
                "SENSOR_EVENT": {
                    "$relation": {"type": "CAUSED", "direction": "in"},
                    "$source": {"event_id": event_id}
                }
            },
            "limit": 1
        })
        
        if caused_hvac.total > 0:
            chains_found += 1
            hvac_event = caused_hvac.data[0]
            
            print(f"\n✓ CAUSAL CHAIN #{chains_found}:")
            print(f"  [Level 0] {event_id}")
            print(f"      Type: TEMPERATURE_ALERT")
            print(f"      Floor: {floor}, Time: {timestamp}")
            print(f"      Value: {temp_event.fields.get('value')}°C")
            print(f"        ↓ CAUSED")
            print(f"  [Level 1] {hvac_event.fields.get('event_id')}")
            print(f"      Type: HVAC_ADJUSTMENT")
            print(f"      Action: {hvac_event.fields.get('action')}")
            print(f"      Time: {hvac_event.fields.get('timestamp')}")
    
    print(f"\n{'='*50}")
    print(f"Summary: Found {chains_found} complete causal chains")
    
    return chains_found


# ============================================================================
# SECTION 4: SEQUENCE PATTERN DETECTION
# ============================================================================

def detect_sequence_patterns():
    """
    Detect recurring event sequences using PRECEDED relationships.
    This pattern helps identify normal vs anomalous behavior.
    """
    print("\n" + "=" * 60)
    print("4. SEQUENCE PATTERN DETECTION")
    print("=" * 60)
    
    # Find HVAC adjustment sequences
    print("\nAnalyzing HVAC adjustment sequences...")
    print("-" * 50)
    
    # Find first HVAC event
    first_hvac = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "type": "HVAC_ADJUSTMENT"
        },
        "orderBy": {"field": "timestamp", "direction": "asc"},
        "limit": 1
    })
    
    if first_hvac.total == 0:
        print("No HVAC events found.")
        return
    
    start_event = first_hvac.data[0]
    start_id = start_event.fields.get("event_id")
    
    print(f"\nStarting sequence from: {start_id}")
    print(f"  Type: {start_event.fields.get('type')}")
    print(f"  Time: {start_event.fields.get('timestamp')}")
    
    # Follow PRECEDED chain
    sequence = [start_event]
    current = start_event
    
    for depth in range(1, 10):  # Follow up to 10 links
        next_events = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "SENSOR_EVENT": {
                    "$relation": {"type": "PRECEDED", "direction": "in"},
                    "$source": {"event_id": current.fields.get("event_id")}
                }
            },
            "orderBy": {"field": "timestamp", "direction": "asc"},
            "limit": 1
        })
        
        if next_events.total == 0:
            break
        
        next_event = next_events.data[0]
        sequence.append(next_event)
        
        # Calculate time delta
        prev_time = datetime.fromisoformat(current.fields.get("timestamp"))
        next_time = datetime.fromisoformat(next_event.fields.get("timestamp"))
        delta_minutes = (next_time - prev_time).total_seconds() / 60
        
        print(f"\n  [Depth {depth}] {next_event.fields.get('event_id')}")
        print(f"      Type: {next_event.fields.get('type')}, Action: {next_event.fields.get('action')}")
        print(f"      +{delta_minutes:.1f} minutes")
        
        current = next_event
    
    print(f"\n{'='*50}")
    print(f"Sequence length: {len(sequence)} events")
    print(f"Pattern: HVAC_ADJUSTMENT → (repeat)")
    
    return sequence


# ============================================================================
# SECTION 5: TEMPORAL AGGREGATION
# ============================================================================

def aggregate_over_temporal_window():
    """
    Aggregate event counts over temporal windows.
    Useful for dashboards, anomaly detection, and reporting.
    """
    print("\n" + "=" * 60)
    print("5. TEMPORAL AGGREGATION")
    print("=" * 60)
    
    # Get all events from last 12 hours
    end_time = datetime.now()
    start_time = end_time - timedelta(hours=12)
    
    result = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "timestamp": {
                "$gte": start_time.isoformat(),
                "$lte": end_time.isoformat()
            }
        },
        "limit": 1000
    })
    
    print(f"\nAggregating {result.total} events from last 12 hours...")
    print("-" * 50)
    
    # Group by type and floor
    by_type = defaultdict(int)
    by_floor = defaultdict(int)
    by_hour = defaultdict(int)
    by_severity = defaultdict(int)
    
    for record in result.data:
        fields = record.fields
        by_type[fields.get("type", "UNKNOWN")] += 1
        by_floor[fields.get("floor", 0)] += 1
        by_severity[fields.get("severity", "UNKNOWN")] += 1
        
        # Parse hour from timestamp
        timestamp = fields.get("timestamp", "")
        if timestamp:
            hour = datetime.fromisoformat(timestamp).strftime("%H:00")
            by_hour[hour] += 1
    
    print("\nEvents by TYPE:")
    for event_type, count in sorted(by_type.items(), key=lambda x: -x[1]):
        bar = "█" * (count // 5)
        print(f"  {event_type:20} {count:4} {bar}")
    
    print("\nEvents by FLOOR:")
    for floor, count in sorted(by_floor.items()):
        bar = "█" * (count // 5)
        print(f"  Floor {floor}:        {count:4} {bar}")
    
    print("\nEvents by SEVERITY:")
    for severity, count in sorted(by_severity.items(), key=lambda x: -x[1]):
        pct = (count / result.total * 100) if result.total > 0 else 0
        bar = "█" * int(pct / 5)
        print(f"  {severity:10} {count:4} ({pct:5.1f}%) {bar}")
    
    print("\nEvents by HOUR:")
    for hour in sorted(by_hour.keys()):
        count = by_hour[hour]
        bar = "█" * (count // 3)
        print(f"  {hour} {count:4} {bar}")
    
    return {
        "by_type": dict(by_type),
        "by_floor": dict(by_floor),
        "by_severity": dict(by_severity),
        "by_hour": dict(by_hour),
        "total": result.total
    }


# ============================================================================
# SECTION 6: TEMPORAL REASONING QUERIES
# ============================================================================

def run_temporal_reasoning_queries():
    """
    Advanced temporal reasoning queries combining time filters with graph traversal.
    """
    print("\n" + "=" * 60)
    print("6. ADVANCED TEMPORAL REASONING QUERIES")
    print("=" * 60)
    
    # Query 1: Find all POWER_SURGE events and their downstream effects
    print("\n[Query 1] Power surge → cascade analysis")
    print("-" * 50)
    
    power_surges = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "type": "POWER_SURGE"
        },
        "limit": 3
    })
    
    total_cascade_events = 0
    for surge in power_surges.data:
        surge_id = surge.fields.get("event_id")
        
        # Find all events CAUSED by this surge
        cascade = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "SENSOR_EVENT": {
                    "$relation": {"type": "CAUSED", "direction": "in"},
                    "$source": {"event_id": surge_id}
                }
            },
            "limit": 10
        })
        
        cascade_types = [e.fields.get("type") for e in cascade.data]
        total_cascade_events += cascade.total
        
        print(f"\n  Surge {surge_id}:")
        print(f"    Voltage: {surge.fields.get('voltage_spike')}V")
        print(f"    Severity: {surge.fields.get('severity')}")
        print(f"    Caused {cascade.total} downstream events: {cascade_types}")
    
    print(f"\n  Total cascade events: {total_cascade_events}")
    
    # Query 2: Find events that have long causal chains
    print("\n[Query 2] Events with longest causal chains")
    print("-" * 50)
    
    # Find events with CAUSED relationships
    caused_events = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "where": {
            "SENSOR_EVENT": {
                "$relation": {"type": "CAUSED", "direction": "out"}
            }
        },
        "limit": 20
    })
    
    # Count downstream for each
    chain_lengths = []
    for event in caused_events.data:
        downstream = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "SENSOR_EVENT": {
                    "$relation": {"type": "CAUSED", "direction": "in"},
                    "$source": {"event_id": event.fields.get("event_id")}
                }
            }
        })
        chain_lengths.append({
            "event_id": event.fields.get("event_id"),
            "type": event.fields.get("type"),
            "chain_length": downstream.total
        })
    
    # Sort by chain length
    chain_lengths.sort(key=lambda x: -x["chain_length"])
    
    print("\n  Top events by causal influence:")
    for item in chain_lengths[:5]:
        if item["chain_length"] > 0:
            print(f"    {item['event_id']}: {item['type']} → {item['chain_length']} effects")
    
    # Query 3: Temporal isolation - find events with no temporal relationships
    print("\n[Query 3] Isolated events (no temporal relationships)")
    print("-" * 50)
    
    all_events = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "limit": 100
    })
    
    isolated_count = 0
    for event in all_events.data:
        event_id = event.fields.get("event_id")
        
        # Check for any relationships
        has_upstream = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "SENSOR_EVENT": {
                    "$relation": {"direction": "out"},
                    "$source": {"event_id": event_id}
                }
            },
            "limit": 1
        })
        
        has_downstream = db.records.find({
            "labels": ["SENSOR_EVENT"],
            "where": {
                "SENSOR_EVENT": {
                    "$relation": {"direction": "in"},
                    "$source": {"event_id": event_id}
                }
            },
            "limit": 1
        })
        
        if has_upstream.total == 0 and has_downstream.total == 0:
            isolated_count += 1
    
    print(f"\n  Isolated events (sample): {isolated_count} out of {all_events.total} sampled")
    print(f"  (Isolated events may indicate data quality issues or rare events)")


# ============================================================================
# MAIN EXECUTION
# ============================================================================

def main():
    print("\n" + "#" * 60)
    print("# TIME-SERIES REASONING WITH TEMPORAL EDGES IN RUSHDB")
    print("#" * 60)
    print("\nThis tutorial demonstrates RushDB's temporal reasoning capabilities")
    print("using a smart building sensor dataset with temporal relationships.")
    print("\nRun 'python seed.py' first to create the sample data.")
    
    # Check for data
    initial_check = db.records.find({
        "labels": ["SENSOR_EVENT"],
        "limit": 1
    })
    
    if initial_check.total == 0:
        print("\n❌ No SENSOR_EVENT records found!")
        print("   Please run 'python seed.py' first to create sample data.")
        return
    
    print(f"\n✓ Found {initial_check.total}+ SENSOR_EVENT records in database")
    
    # Run all demonstrations
    query_events_in_time_range()
    traverse_temporal_edges()
    discover_causal_chains()
    detect_sequence_patterns()
    aggregate_over_temporal_window()
    run_temporal_reasoning_queries()
    
    print("\n" + "#" * 60)
    print("# TUTORIAL COMPLETE")
    print("#" * 60)
    print("\nKey takeaways:")
    print("  1. RushDB stores events as records with temporal properties")
    print("  2. Temporal edges (CAUSED, BEFORE, PRECEDED) form a time graph")
    print("  3. Graph traversal enables causal chain discovery")
    print("  4. Time-range queries + graph traversal = powerful reasoning")
    print("\nLearn more: https://docs.rushdb.com")
    print("#" * 60 + "\n")


if __name__ == "__main__":
    main()
