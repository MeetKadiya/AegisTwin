from typing import Dict, Any, Optional

MITRE_TECHNIQUES: Dict[str, Dict[str, Any]] = {
    "T1190": {
        "id": "T1190",
        "name": "Exploit Public-Facing Application",
        "tactic": "Initial Access",
        "subtechnique": None,
        "description": "Adversaries may attempt to exploit a weakness in an Internet-facing computer or program using software, system, or service bugs to gain initial access.",
        "detection": "Monitor application logs for unexpected input parameters, directory traversal strings, or unexpected child processes spawned by web server daemons (e.g. bash or powershell under w3wp.exe or httpd).",
        "mitigation": "M1051 (Update Software), M1050 (Exploit Protection), M1042 (Web Application Firewall), M1030 (Network Segmentation)."
    },
    "T1059": {
        "id": "T1059",
        "name": "Command and Scripting Interpreter",
        "tactic": "Execution",
        "subtechnique": "T1059.004 / Unix Shell, T1059.001 / PowerShell",
        "description": "Adversaries may abuse command and script interpreters to execute arbitrary commands, scripts, or binaries.",
        "detection": "Enable process command-line logging via auditd or Sysmon (Event ID 1). Watch for encoded commands (e.g. base64 in bash/powershell).",
        "mitigation": "M1038 (Execution Prevention), M1026 (Privileged Account Management), M1042 (Disable or Restrict Interpreters)."
    },
    "T1078": {
        "id": "T1078",
        "name": "Valid Accounts",
        "tactic": "Defense Evasion, Persistence, Privilege Escalation, Initial Access",
        "subtechnique": "T1078.002 / Domain Accounts",
        "description": "Adversaries may obtain and abuse credentials of existing accounts as a means of gaining Initial Access, Persistence, Privilege Escalation, or Defense Evasion.",
        "detection": "Correlate authentication logs (Windows Event 4624) with abnormal logon times, novel source IPs, or unusual user-agent strings.",
        "mitigation": "M1032 (Multi-factor Authentication), M1027 (Password Policies), M1018 (User Account Management)."
    },
    "T1003": {
        "id": "T1003",
        "name": "OS Credential Dumping",
        "tactic": "Credential Access",
        "subtechnique": "T1003.001 / LSASS Memory, T1003.002 / Security Account Manager (SAM)",
        "description": "Adversaries may attempt to dump credentials to obtain account login and credential material, normally in the form of a hash or a clear text password, from the operating system and software.",
        "detection": "Monitor for unexpected access to lsass.exe process handle (Sysmon Event ID 10) and unauthorized read operations targeting SAM registry hives.",
        "mitigation": "M1043 (Credential Protection - Credential Guard), M1026 (Privileged Process Integrity)."
    },
    "T1021.002": {
        "id": "T1021.002",
        "name": "Remote Services: SMB/Windows Admin Shares",
        "tactic": "Lateral Movement",
        "subtechnique": "T1021.002",
        "description": "Adversaries may use Valid Accounts to interact with remote SMB services to execute code, transfer files, or authenticate across network zones.",
        "detection": "Monitor network traffic on TCP 445. Inspect Windows Event 5140 / 5145 for ADMIN$ or C$ share accesses.",
        "mitigation": "M1035 (Limit Software Installation), M1030 (Network Segmentation / Disable SMBv1/v2 between user workstations)."
    },
    "T1021.001": {
        "id": "T1021.001",
        "name": "Remote Services: Remote Desktop Protocol",
        "tactic": "Lateral Movement",
        "subtechnique": "T1021.001",
        "description": "Adversaries may use Valid Accounts to log into a computer using the Remote Desktop Protocol (RDP).",
        "detection": "Monitor Windows Event ID 4624 Logon Type 10 (RemoteInteractive) and Event 4778.",
        "mitigation": "M1032 (MFA for RDP), M1037 (Filter Network Traffic - restrict port 3389 to bastion jump hosts)."
    },
    "T1068": {
        "id": "T1068",
        "name": "Exploitation for Privilege Escalation",
        "tactic": "Privilege Escalation",
        "subtechnique": None,
        "description": "Adversaries may exploit software vulnerabilities in an attempt to elevate privileges from low-privilege service accounts to root or SYSTEM.",
        "detection": "Track unusual privilege token adjustments, new driver registrations, or unexpected child processes running with NT AUTHORITY\\SYSTEM or UID 0.",
        "mitigation": "M1051 (Update Software), M1026 (Privileged Account Management), M1028 (Operating System Configuration)."
    },
    "T1046": {
        "id": "T1046",
        "name": "Network Service Discovery",
        "tactic": "Discovery",
        "subtechnique": None,
        "description": "Adversaries may attempt to get a listing of services running on hosts across the network (e.g. nmap, port sweeps).",
        "detection": "Inspect network intrusion detection (IDS/IPS) for rapid syn sweeps or unusual internal port scan activity.",
        "mitigation": "M1030 (Network Segmentation), M1037 (Filter Network Traffic)."
    },
    "T1552": {
        "id": "T1552",
        "name": "Unsecured Credentials",
        "tactic": "Credential Access",
        "subtechnique": "T1552.001 / Credentials In Files",
        "description": "Adversaries may search local file systems and remote file shares for unsecured credentials in plain text files (e.g. id_rsa, config.json, .env).",
        "detection": "Detect file reads accessing sensitive paths (.ssh/, /etc/shadow, *.kdbx, .aws/credentials) from unusual binary contexts.",
        "mitigation": "M1027 (Password Policies), M1052 (User Training), M1041 (Encrypt Sensitive Information)."
    },
    "T1486": {
        "id": "T1486",
        "name": "Data Encrypted for Impact",
        "tactic": "Impact",
        "subtechnique": None,
        "description": "Adversaries may encrypt data on target systems or large numbers of systems in a network to interrupt availability to system and network resources (Ransomware).",
        "detection": "Monitor high disk I/O rates, bulk file modifications, mass file renames with new extensions, and deletion of shadow copies (vssadmin).",
        "mitigation": "M1053 (Data Backup), M1030 (Network Segmentation), M1040 (Behavior Prevention)."
    },
    "T1567": {
        "id": "T1567",
        "name": "Exfiltration Over Web Service",
        "tactic": "Exfiltration",
        "subtechnique": "T1567.002 / Exfiltration to Cloud Storage",
        "description": "Adversaries may use an existing, legitimate external Web service, such as an API or cloud storage, to exfiltrate data.",
        "detection": "Inspect egress web proxy logs for large POST requests or unusual outbound transfers to cloud storage providers (S3, Dropbox, Mega).",
        "mitigation": "M1037 (Filter Network Traffic - Restrict outbound egress to authorized endpoints only)."
    },
    # --- MITRE ATT&CK FOR ICS (Industrial Control Systems / OT) ---
    "T0855": {
        "id": "T0855",
        "name": "Unauthorized Command Message",
        "tactic": "Impair Process Control, Execution",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may send unauthorized commands to control equipment (e.g. Modbus/DNP3/OPC UA write commands) to disrupt physical industrial processes.",
        "detection": "Establish baselines of command message frequencies and monitor for unauthorized setpoint changes originating from non-HMI/engineering workstations.",
        "mitigation": "M0930 (Network Segmentation - Enforce Purdue Model L1/L2 firewalls), M0937 (Filter Network Traffic - Inspect industrial protocol commands)."
    },
    "T0836": {
        "id": "T0836",
        "name": "Modify Parameter",
        "tactic": "Impair Process Control",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may modify system parameters (e.g. turbine vibration limits, safety trip thresholds, thermal envelopes) to cause physical stress or prevent safety trips.",
        "detection": "Implement change detection on PLC memory tags and compare live PLC configuration against golden baseline project files.",
        "mitigation": "M0938 (Execution Prevention - Hardware write-protect key switches), M0926 (Privileged Account Management)."
    },
    "T0814": {
        "id": "T0814",
        "name": "Denial of Control",
        "tactic": "Impact",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may degrade, disable, or destroy physical control functions by overwhelming control communications or crashing safety controllers.",
        "detection": "Monitor network device health and look for unacknowledged command frames, sudden loss of RTU polling, or watchdog timeout alarms.",
        "mitigation": "M0953 (Redundancy / Diversity of Control Paths), M0930 (Network Segmentation)."
    },
    "T0843": {
        "id": "T0843",
        "name": "Program Download",
        "tactic": "Inhibit Response Function, Persistence",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may upload malicious ladder logic or firmware directly onto a programmable logic controller (PLC).",
        "detection": "Monitor engineering workstation session logs and capture unauthorized upload/download protocol functions (e.g. CIP Class 0x64).",
        "mitigation": "M0938 (Hardware Key Switches in RUN Mode), M0942 (Code Signing of PLC Firmware)."
    },
    "T0887": {
        "id": "T0887",
        "name": "Wireless / Industrial Protocol Sniffing",
        "tactic": "Discovery",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may sniff network traffic to identify industrial protocols, field controller IP addresses, register maps, and unencrypted credentials.",
        "detection": "Deploy network security monitoring (NSM) to identify unauthorized network taps, promiscuous mode interfaces, or rogue MAC addresses on OT networks.",
        "mitigation": "M0941 (Encrypt Industrial Communications with mTLS / IPsec), M0930 (Network Segmentation)."
    },
    "T0879": {
        "id": "T0879",
        "name": "Damage to Property",
        "tactic": "Impact",
        "subtechnique": None,
        "matrix": "ICS",
        "description": "Adversaries may cause physical destruction of equipment, environmental contamination, or safety hazards by forcing industrial machinery beyond physical limits.",
        "detection": "Cross-validate cyber telemetry with independent physical sensors (independent vibration, pressure, and thermal safety relays).",
        "mitigation": "M0927 (Hardwired Physical Interlocks / Relief Valves not controlled by software)."
    }
}

CVE_MITRE_MAP: Dict[str, str] = {
    # Enterprise CVEs
    "CVE-2021-44228": "T1190",   # Log4Shell
    "CVE-2022-22965": "T1059",   # Spring4Shell
    "CVE-2020-1472": "T1068",    # ZeroLogon
    "CVE-2023-38606": "T1190",   # Nginx request smuggling
    "CVE-2023-46805": "T1190",   # FortiOS / Ivanti auth bypass
    "CVE-2023-22515": "T1068",   # Confluence broken access
    "CVE-2023-32315": "T1059",   # Openfire RCE
    "CVE-2023-26159": "T1059",   # Prototype pollution
    "CVE-2024-23897": "T1552",   # Jenkins CLI file read
    "CVE-2021-36934": "T1003",   # HiveNightmare SAM read
    # ICS / OT CVEs
    "CVE-2022-29951": "T0855",   # Schneider Modicon PLC Unauthorized Command
    "CVE-2021-32998": "T0836",   # Siemens S7 PLC Parameter Tampering
    "CVE-2023-3595":  "T0843",   # Rockwell ControlLogix Firmware Download
    "CVE-2020-10644": "T0814",   # Advantech WebAccess SCADA Denial of Control
}


def get_technique_details(technique_id: str) -> Dict[str, Any]:
    """Retrieve full MITRE metadata for a technique identifier."""
    return MITRE_TECHNIQUES.get(
        technique_id,
        {
            "id": technique_id,
            "name": "General Adversary Technique",
            "tactic": "Lateral Movement",
            "subtechnique": None,
            "description": "Adversarial network traversal technique.",
            "detection": "Monitor internal network anomaly baselines.",
            "mitigation": "M1030 (Network Segmentation)."
        }
    )


def map_cve_to_mitre(cve_id: str) -> Dict[str, Any]:
    """Maps CVE identifier to corresponding MITRE ATT&CK technique."""
    tech_id = CVE_MITRE_MAP.get(cve_id, "T1190")
    return get_technique_details(tech_id)
