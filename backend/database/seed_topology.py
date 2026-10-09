import logging
from typing import Dict, List, Any
try:
    from .neo4j_client import graph_engine
except (ImportError, ValueError):
    from database.neo4j_client import graph_engine


logger = logging.getLogger("seed_topology")


def get_default_topology() -> Dict[str, Any]:
    """Returns canonical enterprise network topology with multi-tier infrastructure."""
    nodes: List[Dict[str, Any]] = [
        # --- DMZ TIER ---
        {
            "id": "gw-external",
            "label": "External Gateway",
            "hostname": "gw-external.corp.net",
            "ip": "198.51.100.1",
            "tier": "DMZ",
            "type": "Gateway",
            "os": "VyOS Linux 1.4",
            "criticality": 6.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["BGP/179", "IPsec/500"],
            "vulnerabilities": [],
            "credentials": []
        },
        {
            "id": "web-dmz-01",
            "label": "Reverse Proxy DMZ",
            "hostname": "web-dmz-01.corp.net",
            "ip": "10.0.1.10",
            "tier": "DMZ",
            "type": "Proxy",
            "os": "Ubuntu 22.04 LTS",
            "criticality": 6.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["HTTP/80", "HTTPS/443"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-38606",
                    "title": "Nginx Request Smuggling & Header Injection",
                    "cvss": 7.5,
                    "mitre": "T1190"
                }
            ],
            "credentials": []
        },
        {
            "id": "vpn-gateway",
            "label": "Enterprise SSL VPN",
            "hostname": "vpn.corp.net",
            "ip": "10.0.1.15",
            "tier": "DMZ",
            "type": "VPN",
            "os": "FortiOS 7.0",
            "criticality": 8.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["HTTPS/443", "IKE/500"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-27997",
                    "title": "FortiOS SSL-VPN Heap Buffer Overflow RCE",
                    "cvss": 9.8,
                    "mitre": "T1190"
                }
            ],
            "credentials": []
        },

        # --- WEB TIER ---
        {
            "id": "web-app-01",
            "label": "Customer Portal Frontend",
            "hostname": "web-app-01.corp.internal",
            "ip": "10.0.2.20",
            "tier": "Web Tier",
            "type": "Web Server",
            "os": "Debian 12 Bookworm",
            "criticality": 7.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Node.js/3000", "Nginx/80"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2021-44228",
                    "title": "Log4Shell Remote Code Execution in Log4j",
                    "cvss": 10.0,
                    "mitre": "T1190"
                }
            ],
            "credentials": ["portal_api_token"]
        },
        {
            "id": "api-gateway",
            "label": "Internal API Gateway",
            "hostname": "api-gw.corp.internal",
            "ip": "10.0.2.30",
            "tier": "Web Tier",
            "type": "API Gateway",
            "os": "Alpine Linux 3.19",
            "criticality": 7.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["Kong/8000", "gRPC/9090"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-41053",
                    "title": "Redis Cache Invalidation Desync",
                    "cvss": 6.5,
                    "mitre": "T1562.001"
                }
            ],
            "credentials": ["service_account_token"]
        },

        # --- APP TIER ---
        {
            "id": "app-srv-01",
            "label": "Core Banking Application Server",
            "hostname": "app-srv-01.corp.internal",
            "ip": "10.0.3.10",
            "tier": "App Tier",
            "type": "Application Server",
            "os": "Red Hat Enterprise Linux 9",
            "criticality": 9.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Spring-Boot/8080", "JMX/1099"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2022-22965",
                    "title": "Spring4Shell: Remote Code Execution via Data Binding",
                    "cvss": 9.8,
                    "mitre": "T1190"
                }
            ],
            "credentials": ["app_to_db_svc_account", "jwt_signing_key"]
        },
        {
            "id": "app-srv-02",
            "label": "Payment Processing Backend",
            "hostname": "app-srv-02.corp.internal",
            "ip": "10.0.3.20",
            "tier": "App Tier",
            "type": "Application Server",
            "os": "Red Hat Enterprise Linux 9",
            "criticality": 9.2,
            "compromised": False,
            "compromise_step": None,
            "services": ["Golang-Microservice/8443"],
            "vulnerabilities": [],
            "credentials": ["pci_dss_encryption_key"]
        },
        {
            "id": "ci-cd-runner",
            "label": "GitLab CI/CD Build Runner",
            "hostname": "runner-01.corp.internal",
            "ip": "10.0.3.99",
            "tier": "App Tier",
            "type": "Build Server",
            "os": "Ubuntu 22.04 LTS",
            "criticality": 8.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Docker-Daemon/2375", "GitLab-Runner/8093"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2024-21626",
                    "title": "runc Container Escape via File Descriptor Leak",
                    "cvss": 8.6,
                    "mitre": "T1611"
                }
            ],
            "credentials": ["docker_hub_write_token", "k8s_deploy_sa"]
        },

        # --- DATABASE TIER ---
        {
            "id": "db-cluster-01",
            "label": "Primary PostgreSQL Cluster",
            "hostname": "pg-cluster-01.db.internal",
            "ip": "10.0.4.50",
            "tier": "DB Tier",
            "type": "Database",
            "os": "Rocky Linux 9",
            "criticality": 9.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["PostgreSQL/5432"],
            "vulnerabilities": [],
            "credentials": ["2.4M_customer_pii_records"]
        },
        {
            "id": "db-cluster-02",
            "label": "HashiCorp Vault Secrets Cluster",
            "hostname": "vault-01.sec.internal",
            "ip": "10.0.4.60",
            "tier": "DB Tier",
            "type": "Key Management",
            "os": "Hardened Linux",
            "criticality": 10.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Vault-API/8200"],
            "vulnerabilities": [],
            "credentials": ["root_ca_private_key", "enterprise_encryption_keys"]
        },

        # --- ACTIVE DIRECTORY / IDENTITY TIER ---
        {
            "id": "corp-dc-01",
            "label": "Primary Domain Controller",
            "hostname": "corp-dc-01.corp.ad",
            "ip": "10.0.5.100",
            "tier": "Active Directory",
            "type": "Domain Controller",
            "os": "Windows Server 2022 Datacenter",
            "criticality": 10.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Kerberos/88", "LDAP/389", "LDAPS/636", "SMB/445", "DNS/53"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2020-1472",
                    "title": "Zerologon: Netlogon Elevation of Privilege",
                    "cvss": 10.0,
                    "mitre": "T1068"
                }
            ],
            "credentials": ["NTDS.dit_hashes", "Domain_Admins_Group"]
        },
        {
            "id": "admin-workstation-01",
            "label": "Tier-1 Admin Jumpbox",
            "hostname": "admin-jump-01.corp.ad",
            "ip": "10.0.5.105",
            "tier": "Active Directory",
            "type": "Workstation",
            "os": "Windows 11 Enterprise",
            "criticality": 8.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["RDP/3389", "WinRM/5985"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2021-36934",
                    "title": "HiveNightmare / SeriousSAM SAM Database Read",
                    "cvss": 7.8,
                    "mitre": "T1003"
                }
            ],
            "credentials": ["cached_domain_admin_kerberos_ticket"]
        }
    ]

    edges: List[Dict[str, Any]] = [
        # Ingress from Gateway
        {"id": "e-gw-webdmz", "source": "gw-external", "target": "web-dmz-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-gw-vpn", "source": "gw-external", "target": "vpn-gateway", "relation": "CONNECTS_TO", "status": "active"},

        # DMZ to Web Tier
        {"id": "e-dmz-webapp", "source": "web-dmz-01", "target": "web-app-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-dmz-api", "source": "web-dmz-01", "target": "api-gateway", "relation": "CONNECTS_TO", "status": "active"},

        # VPN Gateway direct lateral routes
        {"id": "e-vpn-admin", "source": "vpn-gateway", "target": "admin-workstation-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-vpn-cicd", "source": "vpn-gateway", "target": "ci-cd-runner", "relation": "CONNECTS_TO", "status": "active"},

        # Web Tier to App Tier
        {"id": "e-webapp-appsrv1", "source": "web-app-01", "target": "app-srv-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-webapp-appsrv2", "source": "web-app-01", "target": "app-srv-02", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-api-appsrv1", "source": "api-gateway", "target": "app-srv-01", "relation": "CONNECTS_TO", "status": "active"},

        # App Tier to Database Tier
        {"id": "e-appsrv1-db1", "source": "app-srv-01", "target": "db-cluster-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-appsrv2-db1", "source": "app-srv-02", "target": "db-cluster-01", "relation": "CONNECTS_TO", "status": "active"},

        # CI/CD to App & Domain Controller
        {"id": "e-cicd-appsrv1", "source": "ci-cd-runner", "target": "app-srv-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-cicd-dc", "source": "ci-cd-runner", "target": "corp-dc-01", "relation": "CONNECTS_TO", "status": "active"},

        # Admin Jumpbox to Domain Controller & Vault
        {"id": "e-admin-dc", "source": "admin-workstation-01", "target": "corp-dc-01", "relation": "CONNECTS_TO", "status": "active"},
        {"id": "e-admin-vault", "source": "admin-workstation-01", "target": "db-cluster-02", "relation": "CONNECTS_TO", "status": "active"},

        # Domain Controller to Vault
        {"id": "e-dc-vault", "source": "corp-dc-01", "target": "db-cluster-02", "relation": "CONNECTS_TO", "status": "active"}
    ]

    return {"nodes": nodes, "edges": edges}


def seed_database():
    """Initializes or resets the digital twin topology in Neo4j idempotently with MERGE."""
    data = get_default_topology()
    graph_engine.set_memory_topology(data["nodes"], data["edges"])

    if graph_engine.is_neo4j_connected:
        try:
            # 1. Clean existing database first to eliminate any prior duplicates
            graph_engine.run_cypher("MATCH (n) DETACH DELETE n")

            # 2. Enforce uniqueness constraints (guaranteed clean baseline)
            try:
                graph_engine.run_cypher(
                    "CREATE CONSTRAINT host_id_unique IF NOT EXISTS FOR (h:Host) REQUIRE h.id IS UNIQUE"
                )
                graph_engine.run_cypher(
                    "CREATE CONSTRAINT vuln_cve_unique IF NOT EXISTS FOR (v:Vulnerability) REQUIRE v.cve IS UNIQUE"
                )
            except Exception as ce:
                logger.warning(f"Constraint creation notice: {ce}")

            # 3. Idempotently MERGE Hosts
            for n in data["nodes"]:
                graph_engine.run_cypher(
                    """
                    MERGE (h:Host {id: $id})
                    ON CREATE SET
                        h.label = $label,
                        h.hostname = $hostname,
                        h.ip = $ip,
                        h.tier = $tier,
                        h.type = $type,
                        h.os = $os,
                        h.criticality = $criticality,
                        h.compromised = $compromised,
                        h.compromise_step = $compromise_step,
                        h.services = $services,
                        h.credentials = $credentials
                    ON MATCH SET
                        h.compromised = $compromised,
                        h.compromise_step = $compromise_step
                    """,
                    n
                )
                # Link Vulnerabilities
                for v in n.get("vulnerabilities", []):
                    graph_engine.run_cypher(
                        """
                        MATCH (h:Host {id: $hid})
                        MERGE (vuln:Vulnerability {cve: $cve})
                        ON CREATE SET vuln.title = $title, vuln.cvss = $cvss, vuln.mitre = $mitre
                        MERGE (h)-[:HAS_VULN]->(vuln)
                        """,
                        {"hid": n["id"], **v}
                    )

            # 4. Idempotently MERGE Connections
            for e in data["edges"]:
                graph_engine.run_cypher(
                    """
                    MATCH (s:Host {id: $source}), (t:Host {id: $target})
                    MERGE (s)-[r:CONNECTS_TO {id: $id}]->(t)
                    ON CREATE SET r.status = $status
                    ON MATCH SET r.status = $status
                    """,
                    e
                )

            logger.info("Successfully seeded clean enterprise network into Neo4j (12 nodes, 15 edges).")
        except Exception as e:
            logger.error(f"Error seeding Neo4j: {e}")

    return {"status": "seeded", "node_count": len(data["nodes"]), "edge_count": len(data["edges"])}
