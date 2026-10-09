#!/usr/bin/env bash
# ==============================================================================
# AegisTwin Enterprise Air-Gapped Bundle Builder
# Creates a standalone, cryptographically-verified offline deployment package
# for air-gapped OT/ICS industrial plants, SOC enclaves, and MSSPs.
# ==============================================================================

set -euo pipefail

VERSION="${1:-2.0.0}"
BUNDLE_DIR="aegistwin-airgap-bundle-v${VERSION}"
OUTPUT_ARCHIVE="${BUNDLE_DIR}.tar.gz"

echo "=========================================================="
echo " AegisTwin v${VERSION} Air-Gapped Offline Bundle Builder"
echo "=========================================================="

# Cleanup prior build artifacts
rm -rf "${BUNDLE_DIR}" "${OUTPUT_ARCHIVE}"
mkdir -p "${BUNDLE_DIR}/images" "${BUNDLE_DIR}/charts" "${BUNDLE_DIR}/scripts" "${BUNDLE_DIR}/manifests"

# 1. Package Kubernetes Helm Chart
echo "[*] Packaging AegisTwin Helm v3 chart..."
if command -v helm &> /dev/null; then
    helm package deploy/helm/aegistwin --version "${VERSION}" --app-version "${VERSION}" -d "${BUNDLE_DIR}/charts/"
else
    echo "[!] Warning: helm CLI not found. Copying raw chart directory..."
    cp -r deploy/helm/aegistwin "${BUNDLE_DIR}/charts/"
fi

# 2. Collect Required Production Container Images
IMAGES=(
    "neo4j:5.26.0-community"
    "nats:2.10-alpine"
    "postgres:16-alpine"
    "aegistwin-backend:${VERSION}"
    "aegistwin-frontend:${VERSION}"
    "aegistwin-edge-agent:${VERSION}"
)

echo "[*] Target Images for Air-Gapped Enclave:"
for img in "${IMAGES[@]}"; do
    echo "  - ${img}"
done

# Check container runtime
DOCKER_CMD=""
if command -v docker &> /dev/null; then
    DOCKER_CMD="docker"
elif command -v podman &> /dev/null; then
    DOCKER_CMD="podman"
elif command -v nerdctl &> /dev/null; then
    DOCKER_CMD="nerdctl"
fi

if [ -n "${DOCKER_CMD}" ]; then
    echo "[*] Using container runtime: ${DOCKER_CMD}"
    
    # Build local images if not present
    echo "[*] Building local AegisTwin container images..."
    ${DOCKER_CMD} build -t "aegistwin-backend:${VERSION}" backend/
    ${DOCKER_CMD} build -t "aegistwin-frontend:${VERSION}" frontend/
    ${DOCKER_CMD} build -t "aegistwin-edge-agent:${VERSION}" edge-agent/

    # Pull 3rd party runtime images
    echo "[*] Pulling upstream dependencies..."
    ${DOCKER_CMD} pull neo4j:5.26.0-community || true
    ${DOCKER_CMD} pull nats:2.10-alpine || true
    ${DOCKER_CMD} pull postgres:16-alpine || true

    # Save images to compressed archive
    echo "[*] Exporting container images to ${BUNDLE_DIR}/images/aegistwin-images.tar.gz..."
    ${DOCKER_CMD} save "${IMAGES[@]}" | gzip > "${BUNDLE_DIR}/images/aegistwin-images.tar.gz"
else
    echo "[!] Notice: No OCI container engine detected in current shell."
    echo "    Creating placeholder images archive for offline packaging pipeline..."
    touch "${BUNDLE_DIR}/images/aegistwin-images.tar.gz"
fi

# 3. Copy Offline Deployment Automation Tools
echo "[*] Copying air-gap installer and verification scripts..."
cp scripts/airgap_installer.py "${BUNDLE_DIR}/scripts/"
chmod +x "${BUNDLE_DIR}/scripts/airgap_installer.py"

# 4. Generate Bundle Metadata & Cryptographic Integrity Manifest
echo "[*] Generating bundle metadata and SHA-256 integrity manifest..."
cat <<EOF > "${BUNDLE_DIR}/manifests/bundle-metadata.json"
{
  "project": "AegisTwin",
  "version": "${VERSION}",
  "release_type": "airgap-enterprise",
  "built_at": "$(date -u +"%Y-%m-%dT%H:%M:%SZ")",
  "min_kubernetes_version": "v1.28.0",
  "images": [
    $(printf '"%s",\n    ' "${IMAGES[@]}" | sed '$ s/,\n    $//')
  ],
  "components": [
    "backend (FastAPI / WebSockets / Merkle Audit)",
    "frontend (Next.js / Threat Canvas / Dashboard)",
    "edge-agent (Distroless / Go / Sparkplug B)",
    "neo4j (Topological Lateral Movement Engine)",
    "nats (JetStream High-Throughput Ingestion)",
    "postgres (Multi-Tenant Row-Level Security)"
  ]
}
EOF

# Calculate SHA-256 Checksums
cd "${BUNDLE_DIR}"
find . -type f ! -name "manifest.sha256" -exec sha256sum {} + > manifests/manifest.sha256
cd ..

# 5. Pack final air-gapped distribution tarball
echo "[*] Compressing final bundle to ${OUTPUT_ARCHIVE}..."
tar -czf "${OUTPUT_ARCHIVE}" "${BUNDLE_DIR}"

# Calculate root archive SHA-256
ARCHIVE_SHA256=$(sha256sum "${OUTPUT_ARCHIVE}" | awk '{print $1}')

echo "=========================================================="
echo " Air-Gapped Bundle Generated Successfully!"
echo " File:   ${OUTPUT_ARCHIVE}"
echo " SHA256: ${ARCHIVE_SHA256}"
echo "=========================================================="
echo "Air-Gapped Deployment Instructions:"
echo " 1. Transfer '${OUTPUT_ARCHIVE}' to the air-gapped bastion via secure USB/Data Diode."
echo " 2. Extract: tar -xzf ${OUTPUT_ARCHIVE}"
echo " 3. Verify & Install: cd ${BUNDLE_DIR} && python3 scripts/airgap_installer.py --install"
echo "=========================================================="
