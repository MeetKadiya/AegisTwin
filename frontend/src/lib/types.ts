export interface Vulnerability {
  cve: string;
  title: string;
  cvss: number;
  mitre: string;
  description?: string;
}

export interface NodeMetrics {
  temperature?: number; // in Celsius (e.g., 42.5°C)
  voltage?: number;     // in Volts (e.g., 230.2V or 12.1V)
  packetDropRate?: number; // percentage (e.g., 0.08%)
  cpuLoad?: number;     // percentage (e.g., 48%)
  memoryUsage?: number; // percentage (e.g., 62%)
  latencyMs?: number;   // ms (e.g., 4.2ms)
  throughputMbps?: number;
}

export interface TopologyNode {
  id: string;
  label: string;
  hostname?: string;
  ip: string;
  tier: "DMZ" | "Web Tier" | "App Tier" | "DB Tier" | "Active Directory" | "OT/ICS Zone" | string;
  type: string;
  os?: string;
  criticality: number;
  compromised?: boolean;
  compromise_step?: number | null;
  isolated?: boolean;
  services?: string[];
  vulnerabilities?: Vulnerability[];
  credentials?: string[];
  metrics?: NodeMetrics;
  lastSeen?: string;
  tags?: string[];
  isBlastRadius?: boolean;
  blastHops?: number;
  onSelectNode?: (node: TopologyNode) => void;
}

export interface TopologyEdge {
  id?: string;
  source: string;
  target: string;
  type?: string;
  port?: number | string;
  protocol?: string;
  status?: "normal" | "blocked" | "traversed" | "quarantined";
  encrypted?: boolean;
}

export interface RiskSummary {
  overall_score: number;
  level: "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
  total_hosts: number;
  compromised_count: number;
  vulnerability_count: number;
  crown_jewels_at_risk?: number;
  network_health_index?: number;
  throughput_mbps?: number;
}

export interface SimulationStep {
  step_number: number;
  tactic: string;
  technique_id: string;
  technique_name: string;
  source_node: string;
  source_name?: string;
  target_node: string;
  target_name?: string;
  target_ip?: string;
  action_description: string;
  credentials_harvested?: string[];
  timestamp?: string;
  severity?: "INFO" | "WARN" | "CRITICAL";
}

export interface RemediationSuggestion {
  id: string;
  title: string;
  action_type: string;
  target_id: string;
  details?: any;
  category: string;
  priority: "P0 - CRITICAL" | "P1 - HIGH" | "P2 - MEDIUM" | "P3 - LOW" | string;
  predicted_risk_reduction: number;
  mitre_reference: string;
  description: string;
}

export interface TelemetryLogEvent {
  id: string;
  timestamp: string;
  level: "INFO" | "WARN" | "CRITICAL";
  channel: "TOPOLOGY" | "SIMULATION" | "TELEMETRY" | "SECURITY" | "SOAR";
  source: string;
  ip?: string;
  message: string;
  mitre?: string;
  details?: Record<string, any>;
}

export interface BlastRadiusResponse {
  origin_node: TopologyNode;
  reachable_nodes: TopologyNode[];
  total_nodes: number;
  blast_radius_count: number;
  hop_distances: Record<string, number>;
  critical_assets_reached: TopologyNode[];
  vulnerabilities_exposed: number;
  exfiltration_risk_score: number;
}

export interface ComplianceStandard {
  id: string;
  name: string;
  version: string;
  score: number;
  level: "PASS" | "WARN" | "FAIL";
  passedControls: number;
  totalControls: number;
  keyControls: {
    controlId: string;
    title: string;
    status: "COMPLIANT" | "NON_COMPLIANT" | "PARTIAL";
    remediationTarget?: string;
  }[];
}

export interface AuditRecord {
  block_index: number;
  timestamp: string;
  event_type: string;
  tenant_id: string;
  actor: string;
  action: string;
  target_resource: string;
  previous_hash: string;
  block_hash: string;
  is_valid: boolean;
}
