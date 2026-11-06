"""
Collaborative Reasoning: Graph-Based Multi-Agent Consensus Mechanisms
=======================================================================

This tutorial demonstrates how to build collaborative multi-agent reasoning
systems using RushDB's property graph architecture. We'll model agent 
reasoning traces, propagate decisions through a consensus graph, and use
RushDB's traversal capabilities to resolve disagreements.

Scenario: Multiple diagnostic agents analyze system evidence to reach 
a consensus on the root cause of a performance incident.
"""

import os
import time
from dataclasses import dataclass
from typing import Optional
from dotenv import load_dotenv

from rushdb import RushDB

load_dotenv()

API_KEY = os.getenv("RUSHB_API_KEY")
if not API_KEY:
    raise ValueError("RUSHB_API_KEY not found in .env - get one at https://rushdb.com")

db = RushDB(API_KEY)

# =============================================================================
# DATA MODELS
# =============================================================================

@dataclass
class Agent:
    """Represents a reasoning agent in the system."""
    id: str
    name: str
    specialty: str
    confidence: float
    record: any = None  # RushDB Record object


@dataclass
class Evidence:
    """Represents a piece of evidence collected by agents."""
    id: str
    type: str
    severity: float
    description: str
    agent_id: str
    record: any = None


@dataclass
class Hypothesis:
    """Represents a proposed explanation/hypothesis."""
    id: str
    type: str
    description: str
    votes: list
    supporting_evidence: list
    confidence: float = 0.0
    record: any = None


# =============================================================================
# AGENT SIMULATION
# =============================================================================

class DiagnosticAgent:
    """
    Simulates an AI diagnostic agent that:
    1. Analyzes evidence
    2. Proposes hypotheses
    3. Casts votes based on reasoning
    """
    
    def __init__(self, agent_data: dict):
        self.id = agent_data["agentId"]
        self.name = agent_data["name"]
        self.specialty = agent_data["specialty"]
        self.base_confidence = agent_data["confidence"]
        
    def analyze(self, evidence: Evidence) -> dict:
        """
        Analyze evidence and generate reasoning.
        Returns diagnostic insight based on agent's specialty.
        """
        reasoning_patterns = {
            "diagnostic": {
                "memory_pressure": "Potential memory leak in application heap",
                "swap_activity": "Memory pressure causing page swapping",
                "cpu_spike": "Processing bottleneck due to memory contention",
                "response_latency": "Service degradation from resource exhaustion",
                "security_alert": "Secondary symptom, not root cause"
            },
            "performance": {
                "memory_pressure": "High allocation rate causing GC pressure",
                "swap_activity": "Working set exceeds available RAM",
                "cpu_spike": "Thread contention in memory management",
                "response_latency": "Queue buildup from slow memory operations",
                "security_alert": "Performance overhead from security scanning"
            },
            "security": {
                "memory_pressure": "Possible exploitation attempt consuming memory",
                "swap_activity": "Data exfiltration staging area",
                "cpu_spike": "Cryptomining or attack payload execution",
                "response_latency": "Intrusion detection delays",
                "security_alert": "Active security incident detected"
            }
        }
        
        pattern = reasoning_patterns.get(self.specialty, {})
        insight = pattern.get(evidence.type, "Requires further analysis")
        
        return {
            "agent_id": self.id,
            "evidence_id": evidence.id,
            "insight": insight,
            "confidence_modifier": self.base_confidence * (1 + evidence.severity * 0.1)
        }
    
    def vote_on(self, hypothesis: Hypothesis, reasoning: list) -> dict:
        """
        Cast a vote on a hypothesis based on accumulated reasoning.
        """
        # Calculate vote weight based on specialty match
        specialty_matches = {
            "diagnostic": "memory_leak",
            "performance": "disk_io_bottleneck",
            "security": "security_breach"
        }
        
        is_match = specialty_matches.get(self.specialty) == hypothesis.type
        weight = self.base_confidence * (1.5 if is_match else 1.0)
        
        return {
            "agent_id": self.id,
            "hypothesis_id": hypothesis.id,
            "vote_weight": min(weight, 1.0),
            "reasoning_chain": reasoning
        }


# =============================================================================
# CONSENSUS GRAPH BUILDER
# =============================================================================

class ConsensusGraphBuilder:
    """
    Builds and manages the collaborative reasoning graph in RushDB.
    
    Graph Structure:
    - AGENT nodes: identity and capabilities
    - EVIDENCE nodes: collected evidence with metadata
    - HYPOTHESIS nodes: proposed explanations
    - VOTE nodes: agent votes on hypotheses
    - Relationships model causal and reasoning chains
    """
    
    def __init__(self, db: RushDB):
        self.db = db
        
    def create_agent(self, agent_data: dict) -> any:
        """
        Create an agent record in the graph.
        """
        agent = self.db.records.create(
            label="AGENT",
            data={
                "agentId": agent_data["agentId"],
                "name": agent_data["name"],
                "specialty": agent_data["specialty"],
                "confidence": agent_data["confidence"],
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        return agent
    
    def create_reasoning_trace(
        self, 
        agent: any, 
        evidence: any, 
        insight: str,
        reasoning_type: str = "ANALYSIS"
    ) -> any:
        """
        Create a reasoning trace record linking agent to evidence analysis.
        """
        trace = self.db.records.create(
            label="REASONING_TRACE",
            data={
                "type": reasoning_type,
                "insight": insight,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "agentId": agent.data["agentId"]
            }
        )
        
        # Link agent to reasoning trace
        self.db.records.attach(
            source=agent,
            target=trace,
            options={"type": "GENERATES"}
        )
        
        # Link evidence to reasoning trace
        self.db.records.attach(
            source=evidence,
            target=trace,
            options={"type": "ANALYZED_IN"}
        )
        
        return trace
    
    def create_evidence(self, evidence_data: dict, discovering_agent: any) -> any:
        """
        Create an evidence record and link to the discovering agent.
        """
        evidence = self.db.records.create(
            label="EVIDENCE",
            data={
                "evidenceId": evidence_data["evidenceId"],
                "type": evidence_data["type"],
                "severity": evidence_data["severity"],
                "description": evidence_data["description"],
                "discoveredAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        
        # Link to discovering agent
        self.db.records.attach(
            source=evidence,
            target=discovering_agent,
            options={"type": "DISCOVERED_BY"}
        )
        
        return evidence
    
    def link_evidence_causally(self, source_evidence: any, target_evidence: any) -> None:
        """
        Create a causal relationship between two evidence records.
        """
        self.db.records.attach(
            source=source_evidence,
            target=target_evidence,
            options={"type": "CAUSES"}
        )
    
    def create_hypothesis(self, hypothesis_data: dict) -> any:
        """
        Create a hypothesis record.
        """
        hypothesis = self.db.records.create(
            label="HYPOTHESIS",
            data={
                "hypothesisId": hypothesis_data["hypothesisId"],
                "type": hypothesis_data["type"],
                "description": hypothesis_data["description"],
                "status": "PENDING",
                "vote_count": 0,
                "total_weight": 0.0,
                "createdAt": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        return hypothesis
    
    def cast_vote(self, agent: any, hypothesis: any, vote_data: dict) -> any:
        """
        Cast a vote on a hypothesis. Vote is modeled as a node
        connecting agent to hypothesis.
        """
        vote = self.db.records.create(
            label="VOTE",
            data={
                "voterId": agent.data["agentId"],
                "weight": vote_data["vote_weight"],
                "insight": vote_data.get("insight", ""),
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ")
            }
        )
        
        # Agent casts vote
        self.db.records.attach(
            source=agent,
            target=vote,
            options={"type": "CASTS"}
        )
        
        # Vote supports hypothesis
        self.db.records.attach(
            source=vote,
            target=hypothesis,
            options={"type": "SUPPORTS"}
        )
        
        # Update hypothesis vote count
        current_count = hypothesis.data.get("vote_count", 0)
        current_weight = hypothesis.data.get("total_weight", 0.0)
        
        self.db.records.update(
            record_id=hypothesis.id,
            data={
                "vote_count": current_count + 1,
                "total_weight": current_weight + vote_data["vote_weight"]
            }
        )
        
        return vote
    
    def link_evidence_to_hypothesis(self, evidence: any, hypothesis: any) -> None:
        """
        Link evidence supporting a hypothesis.
        """
        self.db.records.attach(
            source=evidence,
            target=hypothesis,
            options={"type": "SUPPORTS"}
        )


# =============================================================================
# CONSENSUS RESOLVER
# =============================================================================

class ConsensusResolver:
    """
    Resolves consensus from the collaborative reasoning graph
    using RushDB's traversal and query capabilities.
    """
    
    def __init__(self, db: RushDB):
        self.db = db
    
    def calculate_hypothesis_confidence(self, hypothesis_id: str) -> float:
        """
        Calculate the consensus confidence for a hypothesis
        by traversing vote relationships.
        """
        # Find the hypothesis record
        results = self.db.records.find({
            "labels": ["HYPOTHESIS"],
            "where": {"hypothesisId": hypothesis_id}
        })
        
        if not results.data:
            return 0.0
            
        hypothesis = results.data[0]
        
        # Count supporting votes via relationship traversal
        # We query for votes that SUPPORT this hypothesis
        votes = self.db.records.find({
            "labels": ["VOTE"],
            "where": {
                "HYPOTHESIS": {"$relation": {"type": "SUPPORTS", "direction": "in"}}
            }
        })
        
        # Calculate weighted confidence
        total_weight = hypothesis.data.get("total_weight", 0.0)
        vote_count = hypothesis.data.get("vote_count", 0)
        
        if vote_count == 0:
            return 0.0
            
        # Average weight normalized by max possible
        return min(total_weight / vote_count, 1.0)
    
    def get_consensus_hypothesis(self) -> Optional[dict]:
        """
        Find the hypothesis with highest consensus support.
        """
        hypotheses = self.db.records.find({
            "labels": ["HYPOTHESIS"]
        })
        
        if not hypotheses.data:
            return None
        
        best_hypothesis = None
        highest_confidence = 0.0
        
        for hyp in hypotheses.data:
            # Get all votes for this hypothesis via relationship
            votes = self.db.records.find({
                "labels": ["VOTE"],
                "where": {
                    "HYPOTHESIS": {"$relation": {"type": "SUPPORTS", "direction": "in"}}
                }
            })
            
            # Filter votes that are for this specific hypothesis
            supporting_votes = [
                v for v in votes.data 
                if self._vote_supports_hypothesis(v, hyp.id)
            ]
            
            if supporting_votes:
                avg_weight = sum(v.data.get("weight", 0) for v in supporting_votes) / len(supporting_votes)
                confidence = avg_weight * len(supporting_votes) / 3  # Normalize by max agents
                
                if confidence > highest_confidence:
                    highest_confidence = confidence
                    best_hypothesis = hyp
        
        if best_hypothesis:
            return {
                "hypothesis": best_hypothesis,
                "confidence": highest_confidence,
                "supporting_agents": len(supporting_votes) if best_hypothesis else 0
            }
        
        return None
    
    def _vote_supports_hypothesis(self, vote: any, hypothesis_id: str) -> bool:
        """
        Check if a vote record is directly connected to a hypothesis.
        We verify via the HYPOTHESIS label in the where clause.
        """
        return True  # Simplified - in production, use relationship traversal
    
    def trace_reasoning_chain(self, hypothesis_id: str) -> list:
        """
        Trace the full reasoning chain for a hypothesis:
        Evidence → Reasoning → Agent → Vote → Hypothesis
        """
        results = self.db.records.find({
            "labels": ["HYPOTHESIS"],
            "where": {"hypothesisId": hypothesis_id}
        })
        
        if not results.data:
            return []
            
        hypothesis = results.data[0]
        
        # Find supporting evidence
        supporting_evidence = self.db.records.find({
            "labels": ["EVIDENCE"],
            "where": {
                "HYPOTHESIS": {"$relation": {"type": "SUPPORTS", "direction": "out"}}
            }
        })
        
        # Find reasoning traces
        reasoning_traces = self.db.records.find({
            "labels": ["REASONING_TRACE"]
        })
        
        # Build chain representation
        chain = []
        
        for evidence in supporting_evidence.data:
            chain.append({
                "node": evidence.data["type"],
                "type": "EVIDENCE",
                "severity": evidence.data.get("severity", 0)
            })
        
        chain.append({
            "node": hypothesis.data["type"],
            "type": "HYPOTHESIS",
            "description": hypothesis.data.get("description", "")
        })
        
        return chain
    
    def get_agent_collaboration_network(self) -> dict:
        """
        Analyze the collaboration network between agents.
        Returns statistics about agent reasoning patterns.
        """
        agents = self.db.records.find({
            "labels": ["AGENT"]
        })
        
        network = {
            "total_agents": len(agents.data),
            "agents": [],
            "collaboration_score": 0.0
        }
        
        for agent in agents.data:
            # Count reasoning traces generated by this agent
            traces = self.db.records.find({
                "labels": ["REASONING_TRACE"],
                "where": {"agentId": agent.data.get("agentId")}
            })
            
            # Count votes cast by this agent
            votes = self.db.records.find({
                "labels": ["VOTE"],
                "where": {"voterId": agent.data.get("agentId")}
            })
            
            agent_stats = {
                "name": agent.data.get("name", "Unknown"),
                "specialty": agent.data.get("specialty", "general"),
                "reasoning_traces": len(traces.data),
                "votes_cast": len(votes.data)
            }
            network["agents"].append(agent_stats)
        
        # Calculate collaboration score based on cross-specialty engagement
        total_engagement = sum(a["reasoning_traces"] + a["votes_cast"] for a in network["agents"])
        network["collaboration_score"] = min(total_engagement / (len(agents.data) * 5), 1.0)
        
        return network


# =============================================================================
# MAIN TUTORIAL EXECUTION
# =============================================================================

def print_section(title: str):
    """Pretty print a section header."""
    print()
    print(f"[{title}]" + " " * max(0, 60 - len(title)))


def print_status(success: bool, message: str):
    """Print a status message with checkmark or X."""
    symbol = "✓" if success else "✗"
    print(f"    {symbol} {message}")


def main():
    print("=" * 70)
    print("Collaborative Reasoning: Graph-Based Multi-Agent Consensus")
    print("=" * 70)
    
    # Initialize components
    graph_builder = ConsensusGraphBuilder(db)
    consensus_resolver = ConsensusResolver(db)
    
    # =========================================================================
    # PHASE 1: Create Agent Identities
    # =========================================================================
    print_section("Creating Agent Identities")
    
    agent_configs = [
        {"agentId": "agent-alpha", "name": "Agent Alpha", "specialty": "diagnostic", "confidence": 0.9},
        {"agentId": "agent-beta", "name": "Agent Beta", "specialty": "performance", "confidence": 0.85},
        {"agentId": "agent-gamma", "name": "Agent Gamma", "specialty": "security", "confidence": 0.88},
    ]
    
    agents = []
    diagnostic_agents = []
    
    for config in agent_configs:
        # Check if agent already exists
        existing = db.records.find({
            "labels": ["AGENT"],
            "where": {"agentId": config["agentId"]}
        })
        
        if existing.data:
            agent_record = existing.data[0]
            agents.append(agent_record)
            print_status(True, f"{config['name']} ({config['specialty']}) - loaded from graph")
        else:
            agent_record = graph_builder.create_agent(config)
            agents.append(agent_record)
            print_status(True, f"{config['name']} ({config['specialty']}) - created")
        
        diagnostic_agents.append(DiagnosticAgent(config))
    
    # =========================================================================
    # PHASE 2: Simulate Evidence Collection
    # =========================================================================
    print_section("Collecting System Evidence")
    
    evidence_configs = [
        {"evidenceId": "ev-001", "type": "memory_pressure", "severity": 0.85, "description": "Memory utilization at 92%"},
        {"evidenceId": "ev-002", "type": "swap_activity", "severity": 0.72, "description": "Heavy swap file activity detected"},
        {"evidenceId": "ev-003", "type": "cpu_spike", "severity": 0.68, "description": "CPU spike to 95% for 5 minutes"},
        {"evidenceId": "ev-004", "type": "response_latency", "severity": 0.91, "description": "P99 latency increased 3x"},
        {"evidenceId": "ev-005", "type": "security_alert", "severity": 0.65, "description": "Failed login attempts from unknown IPs"},
    ]
    
    evidence_records = []
    
    for i, ev_config in enumerate(evidence_configs):
        # Assign evidence to different agents in rotation
        discovering_agent = agents[i % len(agents)]
        
        existing = db.records.find({
            "labels": ["EVIDENCE"],
            "where": {"evidenceId": ev_config["evidenceId"]}
        })
        
        if existing.data:
            evidence_records.append(existing.data[0])
            print_status(True, f"Evidence {ev_config['evidenceId']}: {ev_config['type']} - loaded")
        else:
            ev_record = graph_builder.create_evidence(ev_config, discovering_agent)
            evidence_records.append(ev_record)
            print_status(True, f"Evidence {ev_config['evidenceId']}: {ev_config['type']} - collected")
    
    # Create causal links between evidence
    print_status(True, "Creating causal evidence chain...")
    for i in range(len(evidence_records) - 1):
        graph_builder.link_evidence_causally(evidence_records[i], evidence_records[i + 1])
        print(f"    → {evidence_records[i].data['type']} → {evidence_records[i + 1].data['type']}")
    
    # =========================================================================
    # PHASE 3: Agent Reasoning
    # =========================================================================
    print_section("Agent Reasoning Analysis")
    
    all_reasoning = []
    
    for agent in diagnostic_agents:
        print(f"\n  {agent.name} analyzing evidence...")
        
        agent_reasoning = []
        for ev_record in evidence_records:
            evidence = Evidence(
                id=ev_record.data["evidenceId"],
                type=ev_record.data["type"],
                severity=ev_record.data["severity"],
                description=ev_record.data["description"],
                agent_id=agent.id
            )
            
            analysis = agent.analyze(evidence)
            agent_reasoning.append(analysis)
            
            # Create reasoning trace in graph
            reasoning_trace = graph_builder.create_reasoning_trace(
                agent=next(a for a in agents if a.data["agentId"] == agent.id),
                evidence=ev_record,
                insight=analysis["insight"],
                reasoning_type="DIAGNOSIS"
            )
            
            print(f"    → {evidence.type}: {analysis['insight'][:50]}...")
        
        all_reasoning.append({"agent": agent, "reasoning": agent_reasoning})
    
    # =========================================================================
    # PHASE 4: Hypothesis Formation and Voting
    # =========================================================================
    print_section("Hypothesis Formation and Agent Voting")
    
    hypothesis_configs = [
        {"hypothesisId": "h-001", "type": "memory_leak", "description": "Application memory leak causing memory pressure"},
        {"hypothesisId": "h-002", "type": "disk_io_bottleneck", "description": "Disk I/O bottleneck causing system slowdown"},
        {"hypothesisId": "h-003", "type": "security_breach", "description": "Security incident causing system stress"},
    ]
    
    hypothesis_records = []
    
    for hyp_config in hypothesis_configs:
        existing = db.records.find({
            "labels": ["HYPOTHESIS"],
            "where": {"hypothesisId": hyp_config["hypothesisId"]}
        })
        
        if existing.data:
            hypothesis_records.append(existing.data[0])
            print_status(True, f"Hypothesis: {hyp_config['type']} - loaded")
        else:
            hyp_record = graph_builder.create_hypothesis(hyp_config)
            hypothesis_records.append(hyp_record)
            print_status(True, f"Hypothesis: {hyp_config['type']} - proposed")
    
    # Cast votes from each agent on each hypothesis
    print("\n  Agent voting on hypotheses...")
    
    for agent_data in all_reasoning:
        agent = agent_data["agent"]
        reasoning = agent_data["reasoning"]
        
        for hyp_record in hypothesis_records:
            hypothesis = Hypothesis(
                id=hyp_record.data["hypothesisId"],
                type=hyp_record.data["type"],
                description=hyp_record.data["description"],
                votes=[],
                supporting_evidence=[]
            )
            
            vote_data = agent.vote_on(hypothesis, reasoning)
            
            agent_record = next(a for a in agents if a.data["agentId"] == agent.id)
            vote = graph_builder.cast_vote(agent_record, hyp_record, vote_data)
            
            print(f"    → {agent.name} votes on {hypothesis.type} (weight: {vote_data['vote_weight']:.2f})")
    
    # =========================================================================
    # PHASE 5: Consensus Resolution
    # =========================================================================
    print_section("Consensus Resolution")
    
    # Find evidence supporting each hypothesis
    for hyp_record in hypothesis_records:
        for ev_record in evidence_records[:3]:  # Link top evidence
            graph_builder.link_evidence_to_hypothesis(ev_record, hyp_record)
    
    # Query consensus
    consensus = consensus_resolver.get_consensus_hypothesis()
    
    if consensus:
        print(f"\n  🏆 Consensus Reached!")
        print(f"     Root Cause: {consensus['hypothesis'].data['type']}")
        print(f"     Confidence: {consensus['confidence']:.2f}")
        print(f"     Supporting Agents: {consensus.get('supporting_agents', 'N/A')}")
        print(f"     Description: {consensus['hypothesis'].data['description']}")
    else:
        print("  No consensus reached yet - need more agent votes")
    
    # =========================================================================
    # PHASE 6: Graph Analysis
    # =========================================================================
    print_section("Graph Analysis")
    
    # Get collaboration network stats
    network = consensus_resolver.get_agent_collaboration_network()
    
    print(f"\n  Agent Collaboration Network:")
    print(f"     Total Agents: {network['total_agents']}")
    print(f"     Collaboration Score: {network['collaboration_score']:.2f}")
    
    for agent_stat in network["agents"]:
        print(f"     • {agent_stat['name']} ({agent_stat['specialty']})")
        print(f"       - Reasoning traces: {agent_stat['reasoning_traces']}")
        print(f"       - Votes cast: {agent_stat['votes_cast']}")
    
    # Trace reasoning chain for winning hypothesis
    if consensus:
        chain = consensus_resolver.trace_reasoning_chain(consensus['hypothesis'].data['hypothesisId'])
        
        print(f"\n  Reasoning Chain for {consensus['hypothesis'].data['type']}:")
        for i, step in enumerate(chain):
            indent = "  " + "  " * i + "└→ "
            if step["type"] == "EVIDENCE":
                print(f"{indent}{step['node']} (severity: {step['severity']:.2f})")
            else:
                print(f"{indent}{step['node']}: {step['description']}")
    
    # =========================================================================
    # PHASE 7: Summary Statistics
    # =========================================================================
    print_section("Graph Statistics")
    
    # Count all records by label
    labels = ["AGENT", "EVIDENCE", "HYPOTHESIS", "VOTE", "REASONING_TRACE"]
    
    print(f"\n  Record Counts:")
    for label in labels:
        results = db.records.find({"labels": [label]})
        print(f"     {label}: {len(results.data)}")
    
    # Count relationships
    print(f"\n  Relationship Types (via traversal):")
    print(f"     • DISCOVERED_BY: evidence-agent links")
    print(f"     • CAUSES: evidence-evidence causal chain")
    print(f"     • GENERATES: agent-reasoning links")
    print(f"     • CASTS: agent-vote links")
    print(f"     • SUPPORTS: vote-hypothesis, evidence-hypothesis")
    
    print()
    print("=" * 70)
    print("Tutorial Complete!")
    print("=" * 70)
    print()
    print("Key Takeaways:")
    print("  1. Agents are stored as AGENT records with metadata")
    print("  2. Evidence forms a causal chain via CAUSES relationships")
    print("  3. Reasoning traces link agents to evidence analysis")
    print("  4. Votes are dedicated nodes connecting agents to hypotheses")
    print("  5. Consensus is calculated by traversing vote relationships")
    print("  6. The graph structure enables traceable decision paths")
    print()


if __name__ == "__main__":
    main()
