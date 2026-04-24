# Security Evidence: Supply Chain

## Controls

- Build artifacts generated from source in CI.
- Artifact checksums generated and verified.
- CycloneDX SBOM generated for each build run.
- Build provenance attestation generated in GitHub Actions.

## Workflow

- `.github/workflows/supply-chain.yml`

## Verification

- `scripts/verify-release-artifacts.py`
- `dist/SHA256SUMS`
- `dist/sbom.cdx.json`
