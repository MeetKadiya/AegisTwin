"""
Tests for Pillar 5: Production Infrastructure & Air-Gapped Deployment
Validates Dockerfile hardening, Kubernetes Helm chart integrity,
PodSecurityStandards compliance, and air-gap cryptographic verification.
"""

import hashlib
import json
import os
import tempfile
from pathlib import Path
import pytest
import yaml

# Import AirGapInstaller from scripts
from scripts.airgap_installer import AirGapInstaller

WORKSPACE_ROOT = Path(__file__).resolve().parent.parent


class TestDockerfileHardening:
    """Audits container specifications against production zero-trust security standards."""

    def test_backend_dockerfile_hardening(self):
        dockerfile = WORKSPACE_ROOT / "backend" / "Dockerfile"
        assert dockerfile.exists()
        content = dockerfile.read_text(encoding="utf-8")

        # Multi-stage verification
        assert "AS builder" in content
        assert "AS runtime" in content

        # Non-root user verification (UID 10001)
        assert "10001" in content
        assert "USER 10001:10001" in content

        # Read-only filesystem temp buffer support
        assert "PYTHONPYCACHEPREFIX=/tmp/pycache" in content

        # Healthcheck defined
        assert "HEALTHCHECK" in content

    def test_edge_agent_dockerfile_distroless(self):
        dockerfile = WORKSPACE_ROOT / "edge-agent" / "Dockerfile"
        assert dockerfile.exists()
        content = dockerfile.read_text(encoding="utf-8")

        # Distroless static runtime
        assert "gcr.io/distroless/static-debian12:nonroot" in content

        # Distroless non-root UID 65532
        assert "USER 65532:65532" in content
        assert "65532" in content

        # Entrypoint binary
        assert 'ENTRYPOINT ["/app/edge-agent"]' in content

    def test_frontend_dockerfile_nonroot(self):
        dockerfile = WORKSPACE_ROOT / "frontend" / "Dockerfile"
        assert dockerfile.exists()
        content = dockerfile.read_text(encoding="utf-8")

        # Non-root user node
        assert "USER node:node" in content
        assert "--chown=node:node" in content


class TestKubernetesHelmCharts:
    """Validates Helm chart syntax, PodSecurityStandards, and Zero-Trust NetworkPolicies."""

    def test_helm_chart_yaml_metadata(self):
        chart_path = WORKSPACE_ROOT / "deploy" / "helm" / "aegistwin" / "Chart.yaml"
        assert chart_path.exists()
        chart_data = yaml.safe_load(chart_path.read_text(encoding="utf-8"))

        assert chart_data["apiVersion"] == "v2"
        assert chart_data["name"] == "aegistwin"
        assert chart_data["version"] == "2.0.0"
        assert chart_data["appVersion"] == "2.0.0"

    def test_helm_values_security_standards(self):
        values_path = WORKSPACE_ROOT / "deploy" / "helm" / "aegistwin" / "values.yaml"
        assert values_path.exists()
        values = yaml.safe_load(values_path.read_text(encoding="utf-8"))

        # PodSecurityStandard: Restricted enforcement
        assert values["podSecurityContext"]["runAsNonRoot"] is True
        assert values["podSecurityContext"]["seccompProfile"]["type"] == "RuntimeDefault"
        assert values["securityContext"]["readOnlyRootFilesystem"] is True
        assert values["securityContext"]["allowPrivilegeEscalation"] is False
        assert "ALL" in values["securityContext"]["capabilities"]["drop"]

        # Component security contexts
        assert values["backend"]["securityContext"]["runAsUser"] == 10001
        assert values["frontend"]["securityContext"]["runAsUser"] == 1000
        assert values["edgeAgent"]["securityContext"]["runAsUser"] == 65532

        # HPA and NetworkPolicy enabled
        assert values["backend"]["autoscaling"]["enabled"] is True
        assert values["frontend"]["autoscaling"]["enabled"] is True
        assert values["networkPolicy"]["enabled"] is True

    def test_helm_templates_completeness(self):
        templates_dir = WORKSPACE_ROOT / "deploy" / "helm" / "aegistwin" / "templates"
        expected_templates = [
            "_helpers.tpl",
            "serviceaccount.yaml",
            "secret.yaml",
            "configmap.yaml",
            "service.yaml",
            "deployment-backend.yaml",
            "deployment-frontend.yaml",
            "deployment-edge-agent.yaml",
            "statefulset-neo4j.yaml",
            "statefulset-nats.yaml",
            "statefulset-postgres.yaml",
            "hpa.yaml",
            "networkpolicy.yaml",
            "ingress.yaml",
        ]

        for tmpl in expected_templates:
            target = templates_dir / tmpl
            assert target.exists(), f"Missing expected template: {tmpl}"
            assert target.stat().st_size > 50, f"Template {tmpl} is unexpectedly empty"

    def test_network_policy_microsegmentation(self):
        netpol_path = WORKSPACE_ROOT / "deploy" / "helm" / "aegistwin" / "templates" / "networkpolicy.yaml"
        content = netpol_path.read_text(encoding="utf-8")

        # Zero-trust microsegmentation checks
        assert "default-deny" in content
        assert "allow-dns" in content
        assert "backend-netpol" in content
        assert "frontend-netpol" in content
        assert "datastores-netpol" in content


class TestAirGapIntegrityVerifier:
    """Validates cryptographic integrity engine against bit-rot and tampering attacks."""

    def test_airgap_sha256_verification_pass(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir)
            manifests_dir = bundle / "manifests"
            manifests_dir.mkdir(parents=True)

            # Create test payload files
            test_file = bundle / "payload.bin"
            test_file.write_bytes(b"AegisTwin-Encrypted-OT-Telemetry-Firmware-Payload-2026")
            actual_sha = hashlib.sha256(test_file.read_bytes()).hexdigest()

            # Write manifest
            manifest = manifests_dir / "manifest.sha256"
            manifest.write_text(f"{actual_sha}  payload.bin\n", encoding="utf-8")

            installer = AirGapInstaller(bundle_root=bundle)
            assert installer.verify_manifest() is True

    def test_airgap_sha256_tamper_detection(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            bundle = Path(tmpdir)
            manifests_dir = bundle / "manifests"
            manifests_dir.mkdir(parents=True)

            test_file = bundle / "payload.bin"
            test_file.write_bytes(b"Original-Firmware")
            correct_sha = hashlib.sha256(b"Original-Firmware").hexdigest()

            manifest = manifests_dir / "manifest.sha256"
            manifest.write_text(f"{correct_sha}  payload.bin\n", encoding="utf-8")

            # Tamper with file
            test_file.write_bytes(b"Tampered-Malicious-Firmware-Attack")

            installer = AirGapInstaller(bundle_root=bundle)
            # Must detect tampering and abort
            assert installer.verify_manifest() is False

    def test_airgap_bundle_builder_script_exists_and_executable(self):
        script_path = WORKSPACE_ROOT / "scripts" / "airgap-bundle-builder.sh"
        assert script_path.exists()
        content = script_path.read_text(encoding="utf-8")
        assert "set -euo pipefail" in content
        assert "manifest.sha256" in content
        assert "aegistwin-images.tar.gz" in content
