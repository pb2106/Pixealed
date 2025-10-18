# **Pixealed — Decentralized Tamper-Proof Image Format (.pxl)**

![Pixealed Logo](docs/logo.png) *(optional)*

**Project Objective:**
Pixealed is a Python-based system for generating self-contained, tamper-evident image files (`.pxl`) with embedded camera metadata, chunk-based integrity verification, Merkle tree protection, and cryptographically verifiable signatures. It supports **universal device provenance**, enabling traceability to the original device using hardware-backed keys or deterministic fallbacks.

---

## **Table of Contents**

1. [Features](#features)
2. [Folder Structure](#folder-structure)
3. [Installation](#installation)
4. [Usage](#usage)
5. [File Format (.pxl)](#file-format-pxl)
6. [Device-backed Signing & Provenance](#device-backed-signing--provenance)
7. [Module Overview](#module-overview)
8. [Future Enhancements](#future-enhancements)
9. [License](#license)

---

## **Features**

* **Tamper-evident**: Any modification of the image or metadata invalidates the signature.
* **Chunked Merkle Tree Integrity**: Split image into 256 KB chunks, hash each chunk using BLAKE3, and compute a Merkle root.
* **Offline Verification**: `.pxl` files can be verified on any device without contacting a central server.
* **Automatic Camera Metadata Extraction**: Extracts EXIF/XMP fields such as Make, Model, DateTimeOriginal, GPSInfo, and FocalLength.
* **Universal Device Provenance**:

  * Hardware-backed keys (TPM, Secure Enclave, Android Keystore) when available.
  * Deterministic fallback using device ID + app secret for devices without hardware keys.
  * Device fingerprint (`SHA256(public_key)`) and trust tier (`High` / `Medium`) stored in manifest.
* **Compact & Efficient**: No padding, minimal metadata, and optional packaging in ZIP with public key.
* **Cross-Platform**: Supports Linux, Windows, macOS, Android, iOS, and embedded devices.

---

## **Folder Structure**

```
Pixealed/
├── modules/
│   ├── __init__.py
│   ├── converter.py   # Core packing, reading, verification
│   ├── crypto.py      # Key generation, signing, verification, device provenance
│   ├── merkle.py      # Chunk hashing and Merkle tree utilities
│   ├── metadata.py    # Camera metadata extraction or synthetic metadata
│   └── utils.py       # Chunking, canonical JSON, and helper functions
├── input.jpg          # Example input image
├── input.zip          # Optional input package
├── run.py             # CLI for converting images to .pxl
├── view.py            # CLI for reading and displaying .pxl images
└── .gitignore
```

---

## **Installation**

1. Clone the repository:

```bash
git clone https://github.com/yourusername/pixealed.git
cd pixealed
```

2. Install dependencies:

```bash
pip install -r requirements.txt
# Required libraries: Pillow, blake3, pynacl, cryptography
```

3. Optional: create a `keys/` directory to store signing keys:

```bash
mkdir keys
```

---

## **Usage**

### **Command-line Conversion**

```bash
python run.py input.jpg
```

**Options:**

```text
-o, --output        Output .zip file (default: <input>.zip)
-k, --signing-key   Path to signing key file (auto-generated if omitted)
-p, --public-key    Path to public key file (auto-generated if omitted)
--generate-keys     Generate new keypair before conversion
--verify            Verify .pxl file after creation
```

**Example:**

```bash
# Generate new keys and convert image to .pxl
python run.py input.jpg --generate-keys --verify
```

### **Viewing a .pxl File**

```bash
python view.py input.pxl
```

* Reads image, metadata, device fingerprint, and trust tier.
* Verifies integrity and signature.

---

## **File Format (.pxl)**

| Section      | Size / Notes                                                                                  |
| ------------ | --------------------------------------------------------------------------------------------- |
| MAGIC        | 4 bytes: `"PXL!"`                                                                             |
| VERSION      | 1 byte: `0x01`                                                                                |
| IMAGE_CHUNKS | 256 KB each (last chunk may be smaller)                                                       |
| MANIFEST     | Canonical JSON including metadata, chunk hashes, Merkle root, device fingerprint, trust level |
| SIGNATURE    | Ed25519 signature of the manifest                                                             |
| FOOTER       | 4 bytes: `"END!"`                                                                             |

**Manifest Fields Example:**

```json
{
  "metadata": {
    "Make": "Canon",
    "Model": "EOS R5",
    "DateTimeOriginal": "2025-10-17T15:00:00",
    "GPSInfo": "46.8182 N, 8.2275 E",
    "FocalLength": "35mm"
  },
  "chunk_hashes": ["abcd1234...", "ef567890..."],
  "merkle_root": "deadbeef...",
  "device_fingerprint": "fae123456789...",
  "trust_level": "High"
}
```

---

## **Device-backed Signing & Provenance**

1. **Hardware-backed keys** (High-trust):

   * TPM (Windows/Linux), Secure Enclave (macOS/iOS), Android Keystore / StrongBox.
   * Private keys never leave hardware.
   * Attestation evidence can be optionally uploaded to the server.

2. **Deterministic fallback** (Medium-trust):

   * Derive Ed25519 seed from stable device ID + app secret using HKDF-SHA256.
   * Ensures reproducible key across reinstalls.
   * Lower-trust than hardware-backed keys but still traceable.

3. **Fingerprint & Trust Tier**:

   * `device_fingerprint = SHA256(public_key)`
   * `trust_level = "High"` (hardware) or `"Medium"` (fallback)

4. **Signing & Verification**:

   * Manifest is signed using Ed25519.
   * Verification can be performed offline using the public key.
   * Devices can be uniquely identified without exposing private keys.

---

## **Module Overview**

| Module         | Responsibilities                                                                                    |
| -------------- | --------------------------------------------------------------------------------------------------- |
| `converter.py` | Pack/unpack `.pxl` files, orchestrate chunking, hashing, manifest creation, and signing.            |
| `crypto.py`    | Key generation, deterministic seed fallback, signing, verification, device fingerprint, trust tier. |
| `merkle.py`    | Compute BLAKE3 hashes, build Merkle trees for chunk verification.                                   |
| `metadata.py`  | Extract EXIF/XMP camera metadata or generate synthetic metadata.                                    |
| `utils.py`     | Chunking, canonical JSON formatting, helper functions for file I/O.                                 |

---

## **Future Enhancements**

* Multi-party or multi-signer `.pxl` files.
* Support additional formats: WebP, PNG.
* Thumbnails or previews in manifest.
* Optional compression or encryption.
* Partial chunk verification for streaming/large images.
* Device trust-aware verification policies.
* Integration with attestation servers for high-trust devices.

---

## **License**

MIT License — see `LICENSE` file for details.

---

This README provides a **full project overview**, **installation instructions**, **usage examples**, **file structure explanation**, and the **universal device-backed signing workflow** we discussed.

---

I can also produce a **version with flow diagrams** showing:

1. `.pxl` packing workflow
2. Device-backed key provisioning + attestation
3. Verification flow

This makes it easier for developers or reviewers to understand the system at a glance.
