import os
import logging
from typing import Dict, List, Any, Optional
from collections import deque

logger = logging.getLogger("neo4j_client")
logging.basicConfig(level=logging.INFO)

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "aegistwin2026")


class GraphEngine:
    """
    Unified Graph Engine supporting Neo4j with seamless in-memory fallback.
    Provides graph persistence, attack traversal, blast radius computation,
    and remediation mutations.
    """

    def __init__(self):
        self.driver = None
        self.is_neo4j_connected = False
        # Memory fallback store
        self.nodes: Dict[str, Dict[str, Any]] = {}
        self.edges: List[Dict[str, Any]] = []
        self._init_driver()

    def _init_driver(self):
        try:
            from neo4j import GraphDatabase
            self.driver = GraphDatabase.driver(
                NEO4J_URI,
                auth=(NEO4J_USER, NEO4J_PASSWORD)
            )
            # Verify connectivity
            with self.driver.session() as session:
                session.run("RETURN 1 AS test")
            self.is_neo4j_connected = True
            logger.info(f"Connected to Neo4j database at {NEO4J_URI}")
        except Exception as e:
            self.is_neo4j_connected = False
            # ponytail: in-memory graph fallback keeps POC completely operational without live Neo4j daemon
            logger.warning(f"Neo4j connection failed ({e}). Falling back to high-performance in-memory graph engine.")

    def close(self):
        if self.driver:
            self.driver.close()

    def run_cypher(self, query: str, parameters: Dict[str, Any] = None) -> List[Dict[str, Any]]:
        """Run cypher if connected to Neo4j, else return empty list."""
        if not self.is_neo4j_connected or not self.driver:
            return []
        try:
            with self.driver.session() as session:
                result = session.run(query, parameters or {})
                return [record.data() for record in result]
        except Exception as e:
            logger.error(f"Cypher query error: {e}")
            return []

    def set_memory_topology(self, nodes: List[Dict[str, Any]], edges: List[Dict[str, Any]]):
        """Populate the in-memory fallback store."""
        self.nodes = {n["id"]: dict(n) for n in nodes}
        self.edges = [dict(e) for e in edges]

    def get_topology(self) -> Dict[str, Any]:
        """Fetch all nodes and relationships."""
        if self.is_neo4j_connected:
            try:
                node_query = """
                MATCH (h:Host)
                OPTIONAL MATCH (h)-[:HAS_VULN]->(v:Vulnerability)
                WITH h, collect(properties(v)) AS vulns
                RETURN h.id AS id, properties(h) AS props, vulns
                """
                edge_query = """
                MATCH (s:Host)-[r:CONNECTS_TO]->(t:Host)
                RETURN s.id AS source, t.id AS target, type(r) AS relation, properties(r) AS props
                """
                node_records = self.run_cypher(node_query)
                edge_records = self.run_cypher(edge_query)
                if node_records:
                    nodes = []
                    for r in node_records:
                        p = dict(r["props"])
                        p["id"] = r["id"]
                        p["type"] = "Host"
                        p["vulnerabilities"] = r.get("vulns", [])
                        nodes.append(p)
                    edges = [
                        {
                            "source": r["source"],
                            "target": r["target"],
                            "relation": r["relation"],
                            **r["props"]
                        }
                        for r in edge_records
                    ]
                    # ponytail: sync local store from authoritative Neo4j state
                    self.nodes = {n["id"]: dict(n) for n in nodes}
                    self.edges = [dict(e) for e in edges]
                    return {"nodes": nodes, "edges": edges}
            except Exception as e:
                logger.warning(f"Failed querying Neo4j topology, using memory: {e}")

        # In-memory return
        return {
            "nodes": list(self.nodes.values()),
            "edges": list(self.edges)
        }

    def get_node(self, node_id: str) -> Optional[Dict[str, Any]]:
        if self.is_neo4j_connected:
            res = self.run_cypher(
                """
                MATCH (h:Host {id: $id})
                OPTIONAL MATCH (h)-[:HAS_VULN]->(v:Vulnerability)
                WITH h, collect(properties(v)) AS vulns
                RETURN properties(h) AS props, vulns
                """,
                {"id": node_id}
            )
            if res:
                p = dict(res[0]["props"])
                p["vulnerabilities"] = res[0].get("vulns", [])
                return p
        return self.nodes.get(node_id)

    def set_compromised(self, node_id: str, compromised: bool = True, step: Optional[int] = None):
        """Mark a host node as compromised."""
        if self.is_neo4j_connected:
            self.run_cypher(
                "MATCH (n {id: $id}) SET n.compromised = $comp, n.compromise_step = $step",
                {"id": node_id, "comp": compromised, "step": step}
            )
        if node_id in self.nodes:
            self.nodes[node_id]["compromised"] = compromised
            self.nodes[node_id]["compromise_step"] = step

    def reset_compromises(self):
        """Reset all compromise flags in graph."""
        if self.is_neo4j_connected:
            self.run_cypher("MATCH (n) SET n.compromised = false, n.compromise_step = null")
        for node in self.nodes.values():
            node["compromised"] = False
            node["compromise_step"] = None

    def calculate_blast_radius(self, node_id: str) -> Dict[str, Any]:
        """
        Calculates reachable downstream nodes, critical assets exposed,
        and exfiltration risk score for a compromised node.
        """
        # Build adjacency graph
        adj: Dict[str, List[str]] = {}
        for edge in self.edges:
            # Active connections only
            if edge.get("status", "active") == "active":
                s = edge["source"]
                t = edge["target"]
                adj.setdefault(s, []).append(t)

        start_node = self.nodes.get(node_id)
        if not start_node:
            return {"error": "Node not found"}

        # BFS for reachable nodes
        visited = {node_id: 0}  # node -> hop count
        queue = deque([(node_id, 0)])

        while queue:
            curr, hops = queue.popleft()
            for neighbor in adj.get(curr, []):
                if neighbor not in visited:
                    visited[neighbor] = hops + 1
                    queue.append((neighbor, hops + 1))

        reachable_node_ids = list(visited.keys())
        reachable_nodes = [self.nodes[nid] for nid in reachable_node_ids if nid in self.nodes]

        # Calculate metrics
        critical_assets_hit = [
            n for n in reachable_nodes
            if n.get("criticality", 0) >= 8.5
        ]

        total_criticality = sum(n.get("criticality", 0) for n in reachable_nodes)
        max_possible_criticality = sum(n.get("criticality", 0) for n in self.nodes.values()) or 1.0

        # Vulnerabilities exposed along downstream path
        total_vulns = sum(len(n.get("vulnerabilities", [])) for n in reachable_nodes)
        
        # Risk score formula (0-100)
        # Ratio of network reach + critical asset multiplier + vuln density
        reach_ratio = len(reachable_node_ids) / max(len(self.nodes), 1)
        crit_ratio = total_criticality / max_possible_criticality
        crit_bonus = 25.0 if any(n.get("tier") == "Active Directory" for n in critical_assets_hit) else 0.0
        
        raw_risk = (reach_ratio * 40.0) + (crit_ratio * 35.0) + crit_bonus + min(total_vulns * 3.0, 15.0)
        risk_score = round(min(100.0, max(0.0, raw_risk)), 1)

        # Classify risk level
        if risk_score >= 80:
            risk_level = "CRITICAL"
        elif risk_score >= 60:
            risk_level = "HIGH"
        elif risk_score >= 35:
            risk_level = "MEDIUM"
        else:
            risk_level = "LOW"

        return {
            "origin_node": start_node,
            "blast_radius_count": len(reachable_node_ids),
            "total_nodes": len(self.nodes),
            "reachable_nodes": reachable_nodes,
            "hop_distances": visited,
            "critical_assets_reached": critical_assets_hit,
            "exfiltration_risk_score": risk_score,
            "risk_level": risk_level,
            "vulnerabilities_exposed": total_vulns
        }

    def apply_remediation(self, action_type: str, target_id: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mutates graph to apply remediation:
        - 'patch_cve': removes specified CVE from node
        - 'isolate_node': severs all incoming/outgoing edges of a node
        - 'block_edge': blocks specific network connection
        - 'revoke_credential': removes credential node or access relationship
        """
        details = details or {}
        modified = False

        if action_type == "patch_cve":
            cve_id = details.get("cve_id")
            node = self.nodes.get(target_id)
            if node and "vulnerabilities" in node:
                initial_count = len(node["vulnerabilities"])
                node["vulnerabilities"] = [v for v in node["vulnerabilities"] if v.get("cve") != cve_id]
                modified = len(node["vulnerabilities"]) < initial_count
                if self.is_neo4j_connected:
                    self.run_cypher(
                        "MATCH (h:Host {id: $hid})-[r:HAS_VULN]->(v:Vulnerability {cve: $cve}) DELETE r",
                        {"hid": target_id, "cve": cve_id}
                    )

        elif action_type == "isolate_node":
            # Set status to isolated
            if target_id in self.nodes:
                self.nodes[target_id]["isolated"] = True
            for edge in self.edges:
                if edge["source"] == target_id or edge["target"] == target_id:
                    edge["status"] = "blocked"
            modified = True
            if self.is_neo4j_connected:
                self.run_cypher(
                    "MATCH (n {id: $id})-[r]-() SET r.status = 'blocked', n.isolated = true",
                    {"id": target_id}
                )

        elif action_type == "block_edge":
            target_edge_id = details.get("target_edge")
            source = details.get("source")
            target = details.get("target")
            for edge in self.edges:
                if (source and target and edge["source"] == source and edge["target"] == target) or edge.get("id") == target_edge_id:
                    edge["status"] = "blocked"
                    modified = True
            if self.is_neo4j_connected and source and target:
                self.run_cypher(
                    "MATCH (s {id: $s})-[r:CONNECTS_TO]->(t {id: $t}) SET r.status = 'blocked'",
                    {"s": source, "t": target}
                )

        elif action_type == "revoke_credential":
            cred_id = target_id
            for edge in self.edges:
                if edge["target"] == cred_id or edge["source"] == cred_id:
                    edge["status"] = "revoked"
                    modified = True

        return {"success": modified, "action": action_type, "target": target_id}


# Singleton instance
graph_engine = GraphEngine()
