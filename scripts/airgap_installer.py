#!/usr/bin/env python3
"""
AegisTwin Enterprise Air-Gapped Offline Installer
Verifies cryptographic SHA-256 manifests, loads offline OCI container images,
tags/pushes to internal plant registries, and installs Kubernetes Helm charts.

Zero external dependencies - runs on any Python 3.8+ runtime.
"""

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class AirGapInstaller:
    """Enterprise Air-Gapped Deployment & Integrity Verification Engine."""

    def __init__(self, bundle_root: Path, namespace: str = "aegistwin", registry: Optional[str] = None):
        self.bundle_root = bundle_root.resolve()
        self.namespace = namespace
        self.registry = registry.rstrip("/") if registry else None
        self.container_runtime: Optional[str] = self._detect_container_runtime()
        self.helm_bin: Optional[str] = shutil.which("helm")
        self.kubectl_bin: Optional[str] = shutil.which("kubectl")

    def _detect_container_runtime(self) -> Optional[str]:
        """Detect available OCI runtime (docker, podman, nerdctl)."""
        for runtime in ["docker", "podman", "nerdctl"]:
            if shutil.which(runtime):
                return runtime
        return None

    def calculate_sha256(self, file_path: Path) -> str:
        """Stream-calculates SHA-256 hash without loading entire file into memory."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(65536):
                hasher.update(chunk)
        return hasher.hexdigest()

    def verify_manifest(self) -> bool:
        """
        Validates every artifact in the air-gapped bundle against manifests/manifest.sha256.
        Prevents supply chain tampering, bit rot, and incomplete transfers.
        """
        manifest_path = self.bundle_root / "manifests" / "manifest.sha256"
        if not manifest_path.exists():
            print(f"[!] Error: Integrity manifest not found at {manifest_path}")
            return False

        print(f"[*] Verifying cryptographic integrity via {manifest_path}...")
        all_passed = True
        verified_count = 0

        with open(manifest_path, "r", encoding="utf-8") as f:
            for line_no, line in enumerate(f, 1):
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split(maxsplit=1)
                if len(parts) != 2:
                    continue
                expected_hash, rel_file_path = parts
                rel_file_path = rel_file_path.lstrip("./").replace("\\", "/")
                target_file = self.bundle_root / rel_file_path

                if not target_file.exists():
                    print(f"  [FAIL] Missing file: {rel_file_path}")
                    all_passed = False
                    continue

                actual_hash = self.calculate_sha256(target_file)
                if actual_hash.lower() == expected_hash.lower():
                    verified_count += 1
                else:
                    print(f"  [CORRUPT] Hash mismatch on {rel_file_path}")
                    print(f"    Expected: {expected_hash}")
                    print(f"    Actual:   {actual_hash}")
                    all_passed = False

        if all_passed:
            print(f"[+] Cryptographic Integrity Verified: {verified_count} files intact (100% SHA-256 match).")
        else:
            print("[!] CRITICAL: Integrity verification failed! Aborting deployment.")
        return all_passed

    def load_container_images(self, images_archive: Path) -> bool:
        """Loads offline container images into local OCI runtime daemon."""
        if not self.container_runtime:
            print("[!] Warning: No container engine (docker/podman/nerdctl) found on PATH.")
            print("    Skipping local image import.")
            return False

        if not images_archive.exists():
            print(f"[!] Warning: Image archive not found at {images_archive}.")
            return False

        if images_archive.stat().st_size == 0:
            print("[*] Notice: Image archive is empty or placeholder. Skipping load.")
            return True

        print(f"[*] Loading container images via {self.container_runtime} from {images_archive}...")
        try:
            # ponytail: [ceiling: uses pipe/tar streaming; replace with skopeo copy for zero-daemon clusters]
            cmd = [self.container_runtime, "load", "-i", str(images_archive)]
            proc = subprocess.run(cmd, capture_output=True, text=True, check=True)
            print(f"[+] Container images loaded successfully:\n{proc.stdout.strip()}")
            return True
        except subprocess.CalledProcessError as err:
            print(f"[!] Failed to load container images: {err.stderr}")
            return False

    def push_to_private_registry(self, metadata_path: Path) -> bool:
        """Re-tags and pushes loaded images to internal air-gapped enterprise registry."""
        if not self.registry:
            return True

        if not metadata_path.exists():
            print(f"[!] Error: Bundle metadata not found at {metadata_path}")
            return False

        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)

        images = metadata.get("images", [])
        print(f"[*] Retagging and pushing {len(images)} images to internal registry: {self.registry}...")

        for img in images:
            img_name = img.split("/")[-1]
            target_tag = f"{self.registry}/{img_name}"
            print(f"  -> Tagging {img} as {target_tag}")
            try:
                subprocess.run([self.container_runtime, "tag", img, target_tag], check=True, capture_output=True)
                print(f"  -> Pushing {target_tag}...")
                subprocess.run([self.container_runtime, "push", target_tag], check=True, capture_output=True)
            except subprocess.CalledProcessError as err:
                print(f"[!] Failed pushing {target_tag}: {err.stderr}")
                return False

        print("[+] All container images pushed to internal registry.")
        return True

    def deploy_helm_chart(self, dry_run: bool = False, values_override: Optional[Path] = None) -> bool:
        """Deploys or upgrades the AegisTwin Helm chart in the target Kubernetes cluster."""
        if not self.helm_bin:
            print("[!] Error: 'helm' binary not found on PATH. Cannot deploy chart.")
            return False

        chart_dir = self.bundle_root / "charts"
        chart_pkg = None
        for item in chart_dir.glob("*.tgz"):
            chart_pkg = item
            break
        if not chart_pkg:
            # Fall back to unpacked chart directory
            raw_chart = chart_dir / "aegistwin"
            if raw_chart.is_dir():
                chart_pkg = raw_chart
            elif (self.bundle_root.parent / "deploy" / "helm" / "aegistwin").is_dir():
                chart_pkg = self.bundle_root.parent / "deploy" / "helm" / "aegistwin"

        if not chart_pkg:
            print(f"[!] Error: No Helm chart package or directory found under {chart_dir}")
            return False

        cmd = [
            self.helm_bin,
            "template" if dry_run else "upgrade",
            "aegistwin",
            str(chart_pkg),
            "--namespace",
            self.namespace,
        ]

        if not dry_run:
            cmd.extend(["--install", "--create-namespace"])

        if self.registry:
            cmd.extend(["--set", f"global.imageRegistry={self.registry}"])

        if values_override and values_override.exists():
            cmd.extend(["-f", str(values_override)])

        print(f"[*] Executing Helm command: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=True, capture_output=True, text=True)
            if dry_run:
                print("[+] Helm Dry-Run Simulation Successful:")
                print(result.stdout[:1000] + "... [truncated]")
            else:
                print(f"[+] AegisTwin deployed successfully to namespace '{self.namespace}'!")
                print(result.stdout.strip())
            return True
        except subprocess.CalledProcessError as err:
            print(f"[!] Helm execution failed:\n{err.stderr}")
            return False

    def check_cluster_status(self) -> None:
        """Prints live rollout status of AegisTwin pods."""
        if not self.kubectl_bin:
            print("[!] 'kubectl' not found. Skipping cluster rollout status check.")
            return

        print(f"[*] Querying cluster status in namespace '{self.namespace}'...")
        try:
            res = subprocess.run(
                [self.kubectl_bin, "get", "pods,services,pvc", "-n", self.namespace, "-o", "wide"],
                capture_output=True,
                text=True,
                check=True,
            )
            print(res.stdout)
        except subprocess.CalledProcessError as err:
            print(f"[!] Failed to query pods: {err.stderr}")


def main():
    parser = argparse.ArgumentParser(
        description="AegisTwin Enterprise Air-Gapped Offline Installer & Verifier",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument("--bundle-dir", default=".", help="Root path of the extracted air-gap bundle")
    parser.add_argument("--namespace", default="aegistwin", help="Target Kubernetes namespace")
    parser.add_argument("--registry", default=None, help="Air-gapped private OCI registry URL (e.g. harbor.plant.internal/aegistwin)")
    parser.add_argument("--verify-only", action="store_true", help="Perform cryptographic SHA-256 verification and exit")
    parser.add_argument("--skip-images", action="store_true", help="Skip container image import/push")
    parser.add_argument("--dry-run", action="store_true", help="Simulate Helm deployment without applying to cluster")
    parser.add_argument("--values", default=None, help="Path to custom values.yaml override")
    parser.add_argument("--install", action="store_true", help="Execute complete offline install workflow")

    args = parser.parse_args()
    bundle_path = Path(args.bundle_dir)

    installer = AirGapInstaller(
        bundle_root=bundle_path,
        namespace=args.namespace,
        registry=args.registry,
    )

    # Step 1: Mandatory SHA-256 Integrity Verification
    if not installer.verify_manifest():
        print("[!] Aborting due to verification failure.")
        sys.exit(1)

    if args.verify_only:
        print("[+] Manifest verification completed. Exiting.")
        sys.exit(0)

    # Step 2: Container Image Import
    if not args.skip_images:
        images_archive = bundle_path / "images" / "aegistwin-images.tar.gz"
        if images_archive.exists():
            installer.load_container_images(images_archive)

        if args.registry:
            metadata_path = bundle_path / "manifests" / "bundle-metadata.json"
            installer.push_to_private_registry(metadata_path)

    # Step 3: Helm Deployment
    if args.install or args.dry_run:
        values_path = Path(args.values) if args.values else None
        success = installer.deploy_helm_chart(dry_run=args.dry_run, values_override=values_path)
        if not success:
            sys.exit(2)

        if not args.dry_run:
            installer.check_cluster_status()


if __name__ == "__main__":
    main()
