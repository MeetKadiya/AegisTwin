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
            "criticality": 7.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["SSL-VPN/443", "IKE/500"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-46805",
                    "title": "Authentication Bypass in Web Management",
                    "cvss": 8.2,
                    "mitre": "T1190"
                }
            ],
            "credentials": ["vpn_service_token"]
        },

        # --- WEB TIER ---
        {
            "id": "web-app-01",
            "label": "Customer Portal App",
            "hostname": "web-app-01.internal",
            "ip": "10.0.2.20",
            "tier": "Web Tier",
            "type": "Web Server",
            "os": "Debian 11 (Bullseye)",
            "criticality": 7.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["Tomcat/8080", "SSH/22"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2021-44228",
                    "title": "Apache Log4j2 JNDI RCE (Log4Shell)",
                    "cvss": 10.0,
                    "mitre": "T1190"
                },
                {
                    "cve": "CVE-2022-22965",
                    "title": "Spring Framework RCE (Spring4Shell)",
                    "cvss": 9.8,
                    "mitre": "T1059"
                }
            ],
            "credentials": ["db_readonly_user"]
        },
        {
            "id": "api-gateway",
            "label": "Internal API Gateway",
            "hostname": "api.internal",
            "ip": "10.0.2.25",
            "tier": "Web Tier",
            "type": "API Gateway",
            "os": "Alpine Linux 3.18",
            "criticality": 7.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["Kong/8443", "gRPC/9090"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-22515",
                    "title": "Broken Access Control & Privilege Escalation",
                    "cvss": 9.8,
                    "mitre": "T1068"
                }
            ],
            "credentials": ["api_jwt_secret"]
        },

        # --- APPLICATION TIER ---
        {
            "id": "app-srv-01",
            "label": "Payment Processing Engine",
            "hostname": "payment-srv.internal",
            "ip": "10.0.3.30",
            "tier": "App Tier",
            "type": "Application Server",
            "os": "Red Hat Enterprise Linux 9",
            "criticality": 9.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["gRPC/50051", "Prometheus/9100"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-32315",
                    "title": "Openfire Remote Code Execution",
                    "cvss": 8.8,
                    "mitre": "T1059"
                }
            ],
            "credentials": ["db_master_connection_string", "stripe_live_key"]
        },
        {
            "id": "app-srv-02",
            "label": "CRM & Billing Service",
            "hostname": "crm-srv.internal",
            "ip": "10.0.3.31",
            "tier": "App Tier",
            "type": "Application Server",
            "os": "Ubuntu 22.04 LTS",
            "criticality": 8.0,
            "compromised": False,
            "compromise_step": None,
            "services": ["NodeJS/3000", "Redis-Client/6379"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2023-26159",
                    "title": "Prototype Pollution in Follow-Redirects",
                    "cvss": 7.5,
                    "mitre": "T1059"
                }
            ],
            "credentials": []
        },
        {
            "id": "ci-cd-runner",
            "label": "Jenkins CI/CD Build Node",
            "hostname": "build-runner-01.internal",
            "ip": "10.0.3.40",
            "tier": "App Tier",
            "type": "CI/CD Server",
            "os": "Ubuntu 20.04 LTS",
            "criticality": 8.5,
            "compromised": False,
            "compromise_step": None,
            "services": ["Jenkins/8080", "Docker-Socket/2375", "SSH/22"],
            "vulnerabilities": [
                {
                    "cve": "CVE-2024-23897",
                    "title": "Jenkins CLI Arbitrary File Read & Credential Stealing",
                    "cvss": 9.8,
                    "mitre": "T1552"
                }
            ],
            "credentials": ["aws_prod_credentials", "id_rsa_deploy_key"]
        },

        # --- DATABASE TIER ---
        {
            "id": "db-cluster-01",
            "label": "Customer PII Database",
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
    """Initializes or resets the digital twin topology in Neo4j and memory engine."""
    data = get_default_topology()
    graph_engine.set_memory_topology(data["nodes"], data["edges"])

    if graph_engine.is_neo4j_connected:
        try:
            logger.info("Executing Cypher seed script in Neo4j...")
            # Clean existing nodes
            graph_engine.run_cypher("MATCH (n) DETACH DELETE n")

            # Insert Hosts
            for n in data["nodes"]:
                graph_engine.run_cypher(
                    """
                    CREATE (h:Host {
                        id: $id,
                        label: $label,
                        hostname: $hostname,
                        ip: $ip,
                        tier: $tier,
                        type: $type,
                        os: $os,
                        criticality: $criticality,
                        compromised: $compromised,
                        services: $services,
                        credentials: $credentials
                    })
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

            # Insert Connections
            for e in data["edges"]:
                graph_engine.run_cypher(
                    """
                    MATCH (s:Host {id: $source}), (t:Host {id: $target})
                    CREATE (s)-[:CONNECTS_TO {id: $id, status: $status}]->(t)
                    """,
                    e
                )

            logger.info("Successfully seeded enterprise network into Neo4j.")
        except Exception as e:
            logger.error(f"Error seeding Neo4j: {e}")

    return {"status": "seeded", "node_count": len(data["nodes"]), "edge_count": len(data["edges"])}
