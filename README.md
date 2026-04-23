# Xiaomi "marble" Local Manifest

This repository provides a local manifest (`aio.xml`) for the Xiaomi "marble" (Redmi Note 12 Turbo / Poco F5). It is designed to be used with the `repo` tool to fetch all necessary device trees, vendor blobs, and kernel sources required for building Android ROMs (specifically Evolution X).

## Features
- **Evolution-X-Devices:** Tracks official device trees and kernel for Evolution X.
- **Verified Repositories:** Includes a Python verification script to ensure all upstream repos are accessible.
- **Default Branches:** configured to use default branches to maintain compatibility with the main ROM manifest.

## Usage
1. Place `aio.xml` into your ROM's `.repo/local_manifests/` directory.
2. Run `repo sync`.

For more detailed build instructions and development conventions, please refer to the internal documentation.

## Repository Verification
You can verify the accessibility of all repositories in the manifest by running:
```bash
python3 verify_repos.py
```
