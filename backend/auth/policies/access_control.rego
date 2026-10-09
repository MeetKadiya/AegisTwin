package aegistwin.authz

import future.keywords.in

default allow = false

# 1. Superadmin has universal access
allow {
    input.user.role == "superadmin"
}

# 2. Strict Tenant Boundary Isolation
tenant_match {
    not input.resource.tenant_id
}
tenant_match {
    input.user.tenant_id == input.resource.tenant_id
}

# 3. Read Operations (Topology, Telemetry, Blast Radius, Suggestions)
read_actions := {
    "view_topology",
    "view_telemetry",
    "calculate_blast_radius",
    "view_history",
    "view_suggestions"
}

allow {
    tenant_match
    input.action in read_actions
    input.user.role in {"tenant_admin", "operator", "analyst", "auditor"}
}

# 4. State Mutation Operations (Run Simulation, Step Adversary, Remediate)
mutation_actions := {
    "run_simulation",
    "step_adversary",
    "reset_simulation",
    "apply_remediation",
    "isolate_node",
    "patch_vulnerability",
    "modify_setpoint"
}

allow {
    tenant_match
    input.action in mutation_actions
    input.user.role in {"tenant_admin", "operator"}
    has_clearance
}

# 5. Administrative Operations (User & Tenant Configuration)
admin_actions := {
    "manage_users",
    "manage_tenant",
    "configure_integrations"
}

allow {
    tenant_match
    input.action in admin_actions
    input.user.role == "tenant_admin"
}

# 6. Audit & Regulatory Compliance Operations
audit_actions := {
    "view_audit_logs",
    "generate_compliance_report"
}

allow {
    tenant_match
    input.action in audit_actions
    input.user.role in {"tenant_admin", "auditor"}
}

# 7. Asset Classification Clearance Verification
default has_clearance = true

has_clearance = false {
    input.resource.classification == "CRITICAL_OT"
    not "CRITICAL_OT" in input.user.clearance
    input.user.role != "tenant_admin"
}

has_clearance = false {
    input.resource.classification == "SECRET"
    not "SECRET" in input.user.clearance
    input.user.role != "tenant_admin"
}
