#!/usr/bin/env python3
"""
Trust Scoring Agents: Weighted Evidence Graphs for Response Reliability

This example demonstrates how to use RushDB to build a trust scoring system
for AI-generated responses by modeling evidence as a weighted property graph.

Key concepts:
- Agents generate responses with varying reliability
- Evidence is weighted by source reliability and corroboration
- Trust scores are calculated by traversing the evidence graph
- Sources and agents build track records over time
"""

import os
from collections import defaultdict
from dotenv import load_dotenv
from rushdb import RushDB

# Load environment
load_dotenv()

API_KEY = os.environ.get("RUSHDB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHDB_API_KEY environment variable is required")

db = RushDB(API_KEY)


def calculate_response_trust_score(response):
    """
    Calculate trust score for a response based on supporting evidence.
    
    Trust = Σ(Evidence Weight × Source Reliability × Corroboration Factor)
    
    Args:
        response: Record with RESPONSE label
    
    Returns:
        float: Trust score between 0 and 1
    """
    # Find supporting evidence
    supporting_evidence = db.records.find({
        "labels": ["EVIDENCE"],
        "where": {
            "RESPONSE": {
                "$relation": {"type": "SUPPORTS", "direction": "in"}
            }
        }
    })
    
    # Find contradicting evidence
    contradicting_evidence = db.records.find({
        "labels": ["EVIDENCE"],
        "where": {
            "RESPONSE": {
                "$relation": {"type": "CONTRADICTS", "direction": "in"}
            }
        }
    })
    
    if not supporting_evidence.data:
        return 0.0
    
    total_score = 0.0
    evidence_count = 0
    
    for evidence in supporting_evidence.data:
        weight = evidence.get("weight", 0.5)
        
        # Find source reliability via claims
        source_reliability = 0.7  # default
        claims = db.records.find({
            "labels": ["CLAIM"],
            "where": {
                "EVIDENCE": {
                    "$relation": {"type": "MAKES", "direction": "in"}
                }
            }
        })
        
        for claim in claims.data:
            sources = db.records.find({
                "labels": ["SOURCE"],
                "where": {
                    "CLAIM": {
                        "$relation": {"type": "CITES", "direction": "in"}
                    }
                }
            })
            if sources.data:
                source_reliability = sources.data[0].get("base_reliability", 0.7)
                break
        
        total_score += weight * source_reliability
        evidence_count += 1
    
    # Apply corroboration factor: more supporting = higher score
    corroboration_factor = 1.0 + (0.1 * (evidence_count - 1))
    contradiction_penalty = 0.1 * len(contradicting_evidence.data)
    
    base_score = total_score / max(evidence_count, 1)
    trust_score = base_score * corroboration_factor - contradiction_penalty
    
    return max(0.0, min(1.0, trust_score))  # clamp to [0, 1]


def calculate_agent_trust(agent):
    """
    Calculate trust score for an agent based on their responses and vouching.
    
    Agent Trust = (Base Trust × 0.4) + (Avg Response Trust × 0.4) + (Vouching Score × 0.2)
    
    Args:
        agent: Record with AGENT label
    
    Returns:
        float: Agent trust score between 0 and 1
    """
    base_trust = agent.get("base_trust", 0.7)
    
    # Get agent's responses
    responses = db.records.find({
        "labels": ["RESPONSE"],
        "where": {
            "AGENT": {
                "$relation": {"type": "GENERATED", "direction": "in"}
            }
        }
    })
    
    avg_response_trust = 0.0
    if responses.data:
        trust_scores = [calculate_response_trust_score(r) for r in responses.data]
        avg_response_trust = sum(trust_scores) / len(trust_scores)
    
    # Get vouching score
    vouched_by = db.records.find({
        "labels": ["AGENT"],
        "where": {
            "AGENT": {
                "$relation": {"type": "VOUCHES_FOR", "direction": "in"}
            }
        }
    })
    
    vouching_score = 0.0
    if vouched_by.data:
        vouched_trusts = [v.get("base_trust", 0.7) for v in vouched_by.data]
        vouching_score = sum(vouched_trusts) / len(vouched_trusts)
    
    # Weighted combination
    trust = (base_trust * 0.4) + (avg_response_trust * 0.4) + (vouching_score * 0.2)
    return max(0.0, min(1.0, trust))


def get_high_reliability_responses(min_trust=0.7):
    """
    Find all responses with trust score above threshold.
    
    Args:
        min_trust: Minimum trust score threshold
    
    Returns:
        list: Responses with trust scores
    """
    all_responses = db.records.find({"labels": ["RESPONSE"], "limit": 100})
    
    scored_responses = []
    for response in all_responses.data:
        trust = calculate_response_trust_score(response)
        if trust >= min_trust:
            scored_responses.append({
                "response": response,
                "trust_score": trust
            })
    
    # Sort by trust score descending
    scored_responses.sort(key=lambda x: x["trust_score"], reverse=True)
    return scored_responses


def trace_evidence_chain(evidence):
    """
    Trace the full evidence chain: Evidence -> Claim -> Source.
    
    Args:
        evidence: Evidence record
    
    Returns:
        dict: Evidence chain with source reliability
    """
    chain = {
        "evidence": evidence.data,
        "claims": [],
        "sources": []
    }
    
    # Find claims made by this evidence
    claims = db.records.find({
        "labels": ["CLAIM"],
        "where": {
            "EVIDENCE": {
                "$relation": {"type": "MAKES", "direction": "in"}
            }
        }
    })
    
    for claim in claims.data:
        chain["claims"].append(claim.data)
        
        # Find sources cited by this claim
        sources = db.records.find({
            "labels": ["SOURCE"],
            "where": {
                "CLAIM": {
                    "$relation": {"type": "CITES", "direction": "in"}
                }
            }
        })
        
        for source in sources.data:
            if source.data not in chain["sources"]:
                chain["sources"].append(source.data)
    
    return chain


def analyze_corroboration(response):
    """
    Analyze corroboration for a response: supporting vs contradicting evidence.
    
    Args:
        response: Response record
    
    Returns:
        dict: Corroboration analysis
    """
    supporting = db.records.find({
        "labels": ["EVIDENCE"],
        "where": {
            "RESPONSE": {
                "$relation": {"type": "SUPPORTS", "direction": "in"}
            }
        }
    })
    
    contradicting = db.records.find({
        "labels": ["EVIDENCE"],
        "where": {
            "RESPONSE": {
                "$relation": {"type": "CONTRADICTS", "direction": "in"}
            }
        }
    })
    
    net_adjustment = len(supporting.data) * 0.1 - len(contradicting.data) * 0.15
    
    return {
        "supporting_count": len(supporting.data),
        "contradicting_count": len(contradicting.data),
        "net_trust_adjustment": net_adjustment,
        "reliability": "High" if len(supporting.data) > 2 else "Moderate" if len(supporting.data) > 0 else "Low"
    }


def rank_agents_by_trust():
    """
    Rank all agents by their calculated trust score.
    
    Returns:
        list: Agents sorted by trust score descending
    """
    all_agents = db.records.find({"labels": ["AGENT"], "limit": 100})
    
    ranked_agents = []
    for agent in all_agents.data:
        trust = calculate_agent_trust(agent)
        ranked_agents.append({
            "agent": agent,
            "trust_score": trust
        })
    
    ranked_agents.sort(key=lambda x: x["trust_score"], reverse=True)
    return ranked_agents


def find_reliable_sources(min_reliability=0.85):
    """
    Find sources with reliability above threshold.
    
    Args:
        min_reliability: Minimum reliability score
    
    Returns:
        list: Reliable sources
    """
    sources = db.records.find({
        "labels": ["SOURCE"],
        "where": {
            "base_reliability": {"$gte": min_reliability}
        },
        "limit": 100
    })
    return sources.data


def main():
    print("\n" + "=" * 60)
    print("Trust Scoring Agents: Weighted Evidence Graphs")
    print("=" * 60 + "\n")
    
    # Count total records
    agents = db.records.find({"labels": ["AGENT"], "limit": 100})
    responses = db.records.find({"labels": ["RESPONSE"], "limit": 100})
    evidence = db.records.find({"labels": ["EVIDENCE"], "limit": 100})
    sources = db.records.find({"labels": ["SOURCE"], "limit": 100})
    
    print(f"Loaded {agents.total} agents, {responses.total} responses, "
          f"{evidence.total} evidence pieces, {sources.total} sources\n")
    
    # 1. Agent Trust Rankings
    print("--- Agent Trust Rankings ---")
    ranked_agents = rank_agents_by_trust()
    for i, item in enumerate(ranked_agents[:5], 1):
        agent_name = item["agent"].get("name", "Unknown")
        trust = item["trust_score"]
        print(f"{i}. {agent_name}: {trust:.3f}")
    print()
    
    # 2. Response Trust Scores (sample)
    print("--- Response Trust Scores (sample) ---")
    sample_responses = responses.data[:5]
    for response in sample_responses:
        trust = calculate_response_trust_score(response)
        text = response.get("text", "")[:50]
        label = "High confidence" if trust > 0.75 else "Moderate" if trust > 0.5 else "Low"
        print(f"  '{text}...': {trust:.3f} ({label})")
    print()
    
    # 3. High-Reliability Responses
    print("--- Finding high-reliability responses ---")
    high_trust = get_high_reliability_responses(min_trust=0.7)
    print(f"Found {len(high_trust)} responses with trust > 0.7")
    if high_trust:
        top = high_trust[0]
        text = top["response"].get("text", "")[:50]
        print(f"  Top: '{text}...' (trust: {top['trust_score']:.3f})")
    print()
    
    # 4. Graph Traversal: Trace Evidence Chain
    print("--- Graph Traversal: Tracing evidence chain ---")
    if evidence.data:
        sample_evidence = evidence.data[0]
        chain = trace_evidence_chain(sample_evidence)
        
        desc = chain["evidence"].get("description", "Unknown")[:40]
        print(f"Evidence '{desc}...'")
        
        if chain["sources"]:
            source_name = chain["sources"][0].get("name", "Unknown")
            reliability = chain["sources"][0].get("base_reliability", 0.7)
            print(f"  Source '{source_name}' reliability: {reliability}")
            
        # Count how many responses this evidence supports
        supported = db.records.find({
            "labels": ["RESPONSE"],
            "where": {
                "EVIDENCE": {
                    "$relation": {"type": "SUPPORTS", "direction": "in"}
                }
            }
        })
        print(f"  Supports {supported.total} responses")
    print()
    
    # 5. Corroboration Analysis
    print("--- Corroboration analysis ---")
    if responses.data:
        sample_resp = responses.data[3]  # Pick a middle response
        text = sample_resp.get("text", "")[:40]
        analysis = analyze_corroboration(sample_resp)
        
        print(f"Response '{text}...' has:")
        print(f"  {analysis['supporting_count']} supporting evidence pieces")
        print(f"  {analysis['contradicting_count']} contradicting evidence pieces")
        print(f"  Net trust adjustment: {analysis['net_trust_adjustment']:+.2f}")
    print()
    
    # 6. Reliable Sources
    print("--- Reliable Sources ---")
    reliable = find_reliable_sources(min_reliability=0.85)
    print(f"Found {len(reliable)} sources with reliability > 0.85")
    for src in reliable[:3]:
        name = src.get("name", "Unknown")
        rel = src.get("base_reliability", 0)
        print(f"  - {name}: {rel:.2f}")
    print()
    
    # 7. Topic-based Analysis
    print("--- Topic-based Analysis ---")
    topics = defaultdict(list)
    for resp in responses.data:
        topic = resp.get("topic", "unknown")
        trust = calculate_response_trust_score(resp)
        topics[topic].append(trust)
    
    for topic, scores in sorted(topics.items(), key=lambda x: -sum(x[1])/len(x[1])):
        avg = sum(scores) / len(scores)
        print(f"  {topic}: avg trust {avg:.3f} ({len(scores)} responses)")
    
    print("\n" + "=" * 60)
    print("Demo complete! Check RushDB dashboard to see the graph.")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    main()
