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
            if float(n.get("criticality") or 0) >= 8.5
        ]

        total_criticality = sum(float(n.get("criticality") or 0) for n in reachable_nodes)
        max_possible_criticality = sum(float(n.get("criticality") or 0) for n in self.nodes.values()) or 1.0

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

    def calculate_attack_paths(
        self,
        start_node_id: str,
        target_node_id: Optional[str] = None,
        max_depth: int = 5,
    ) -> Dict[str, Any]:
        """
        Calculates topological attack propagation paths through active edges
        from a start node to designated targets or all critical crown-jewel assets.
        Identifies chokepoints / bottleneck nodes for proactive segmentation.
        """
        adj: Dict[str, List[str]] = {}
        for edge in self.edges:
            if edge.get("status", "active") == "active":
                adj.setdefault(edge["source"], []).append(edge["target"])

        start_node = self.nodes.get(start_node_id)
        if not start_node:
            return {"error": f"Origin node '{start_node_id}' not found"}

        # Target selection: specific target or all nodes with criticality >= 8.5
        target_ids = set()
        if target_node_id:
            if target_node_id in self.nodes:
                target_ids.add(target_node_id)
        else:
            target_ids = {
                nid for nid, n in self.nodes.items()
                if float(n.get("criticality") or 0) >= 8.5 and nid != start_node_id
            }

        # Find all paths via DFS up to max_depth
        all_paths: List[List[str]] = []

        def dfs(current: str, path: List[str]):
            if len(path) > max_depth + 1:
                return
            if current in target_ids and len(path) > 1:
                all_paths.append(list(path))
            for neighbor in adj.get(current, []):
                if neighbor not in path:
                    dfs(neighbor, path + [neighbor])

        dfs(start_node_id, [start_node_id])

        # Evaluate risk score & MITRE techniques per path
        evaluated_paths = []
        node_path_frequency: Dict[str, int] = {}

        for p in all_paths:
            nodes_in_path = [self.nodes[nid] for nid in p if nid in self.nodes]
            dest_node = nodes_in_path[-1]
            dest_crit = float(dest_node.get("criticality") or 5.0)

            # Cumulative exploit score
            path_vulns = []
            mitre_chain = []
            for n in nodes_in_path:
                for v in n.get("vulnerabilities", []):
                    path_vulns.append(v)
                    mitre_chain.append(v.get("mitre", "T1059"))

            # Calculate choke points (intermediate nodes)
            for nid in p[1:-1]:
                node_path_frequency[nid] = node_path_frequency.get(nid, 0) + 1

            path_risk = min(100.0, (dest_crit * 7.0) + (len(path_vulns) * 4.0) + max(0, 30.0 - (len(p) * 4.0)))

            evaluated_paths.append({
                "path_ids": p,
                "hop_count": len(p) - 1,
                "destination_asset": dest_node.get("label") or dest_node.get("id"),
                "destination_tier": dest_node.get("tier"),
                "destination_criticality": dest_crit,
                "vulnerabilities_on_path": len(path_vulns),
                "mitre_chain": list(dict.fromkeys(mitre_chain)),
                "path_risk_score": round(path_risk, 1),
            })

        # Sort paths by risk score descending
        evaluated_paths.sort(key=lambda x: x["path_risk_score"], reverse=True)

        # Chokepoint analysis: node appearing on most attack paths
        chokepoint_id = None
        chokepoint_coverage = 0.0
        if node_path_frequency and evaluated_paths:
            chokepoint_id = max(node_path_frequency, key=node_path_frequency.get)
            chokepoint_coverage = round((node_path_frequency[chokepoint_id] / len(evaluated_paths)) * 100.0, 1)

        return {
            "origin_node": start_node,
            "total_attack_paths_found": len(evaluated_paths),
            "target_critical_assets_exposed": len({p["path_ids"][-1] for p in evaluated_paths}),
            "highest_risk_path_score": evaluated_paths[0]["path_risk_score"] if evaluated_paths else 0.0,
            "top_chokepoint_node": {
                "node_id": chokepoint_id,
                "paths_mitigated_percentage": chokepoint_coverage,
                "recommendation": f"Segment or isolate '{chokepoint_id}' to eliminate {chokepoint_coverage}% of lateral movement attack paths.",
            } if chokepoint_id else None,
            "attack_paths": evaluated_paths[:15],
        }

    def apply_remediation(self, action_type: str, target_id: str, details: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Mutates graph to apply remediation:
        - 'patch_cve': removes specified CVE from node
        - 'isolate_node': severs all incoming/outgoing edges of a node
        - 'block_edge': blocks specific network connection
        - 'revoke_credential': removes credential from host node
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
                if (source and target and edge["source"] == source and edge["target"] == target) or (target_edge_id and edge.get("id") == target_edge_id):
                    edge["status"] = "blocked"
                    source = source or edge["source"]
                    target = target or edge["target"]
                    modified = True
            if self.is_neo4j_connected and source and target:
                self.run_cypher(
                    "MATCH (s {id: $s})-[r:CONNECTS_TO]->(t {id: $t}) SET r.status = 'blocked'",
                    {"s": source, "t": target}
                )

        elif action_type == "revoke_credential":
            cred_id = details.get("credential_id") or details.get("cred_id")
            host_id = target_id if target_id in self.nodes else None
            if not host_id and not cred_id:
                cred_id = target_id

            for node in self.nodes.values():
                if host_id and node["id"] != host_id:
                    continue
                if cred_id and "credentials" in node and cred_id in node["credentials"]:
                    node["credentials"] = [c for c in node["credentials"] if c != cred_id]
                    modified = True
                    if self.is_neo4j_connected:
                        self.run_cypher(
                            "MATCH (h:Host {id: $hid}) SET h.credentials = [c IN h.credentials WHERE c <> $cred]",
                            {"hid": node["id"], "cred": cred_id}
                        )

        return {"success": modified, "action": action_type, "target": target_id}


# Singleton instance
graph_engine = GraphEngine()
