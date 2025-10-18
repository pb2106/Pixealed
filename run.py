"""
Pixealed .pxl Converter - Command Line Interface

Usage:
    python convert.py <input_image> [options]

Examples:
    python convert.py photo.jpg
    python convert.py photo.jpg -o encrypted.zip
    python convert.py photo.jpg -k ./keys/signing_key.bin
"""

import os
import argparse
import zipfile
from datetime import datetime
from modules.converter import pack_image, verify_pxl
from modules.crypto import generate_keypair


def main():
    parser = argparse.ArgumentParser(
        description='Convert images to tamper-proof .pxl format (packaged in .zip)',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python convert.py photo.jpg
  python convert.py photo.jpg -o encrypted.zip
  python convert.py photo.jpg -k ./keys/signing_key.bin -p ./keys/public_key.bin
        """
    )
    
    parser.add_argument(
        'input',
        help='Input image file (jpg, png, etc.)'
    )
    
    parser.add_argument(
        '-o', '--output',
        help='Output .zip file (default: <input>.zip)',
        default=None
    )
    
    parser.add_argument(
        '-k', '--signing-key',
        help='Path to signing key file (default: auto-generate with timestamp)',
        default=None
    )
    
    parser.add_argument(
        '-p', '--public-key',
        help='Path to public key file (default: auto-generate with timestamp)',
        default=None
    )
    
    parser.add_argument(
        '--generate-keys',
        action='store_true',
        help='Generate new keypair before conversion'
    )
    
    parser.add_argument(
        '--verify',
        action='store_true',
        help='Verify the .pxl file after creation'
    )
    
    args = parser.parse_args()
    
    # Check if input file exists
    if not os.path.exists(args.input):
        print(f"❌ Error: Input file '{args.input}' not found!")
        return 1
    
    # Determine output filename (always .zip)
    if args.output is None:
        base_name = os.path.splitext(args.input)[0]
        args.output = f"{base_name}.zip"
    elif not args.output.endswith('.zip'):
        args.output = f"{args.output}.zip"
    
    # Generate timestamp-based key names if not specified
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    if args.signing_key is None:
        args.signing_key = f"./keys/signing_key_{timestamp}.bin"
    
    if args.public_key is None:
        args.public_key = f"./keys/public_key_{timestamp}.bin"
    
    # Temporary .pxl file (will be packaged in zip)
    temp_pxl = f"temp_{timestamp}.pxl"
    
    print("=== Pixealed .pxl Converter ===\n")
    print(f"📁 Input:  {args.input}")
    print(f"📦 Output: {args.output}\n")
    
    # Generate or load keys
    if args.generate_keys or not os.path.exists(args.signing_key):
        print("🔑 Generating new Ed25519 keypair...")
        signing_key, public_key = generate_keypair()
        
        # Create keys directory if it doesn't exist
        os.makedirs(os.path.dirname(args.signing_key) or '.', exist_ok=True)
        
        # Save keys
        with open(args.signing_key, "wb") as f:
            f.write(signing_key)
        with open(args.public_key, "wb") as f:
            f.write(public_key)
        
        print(f"   ✓ Signing key saved to: {args.signing_key}")
        print(f"   ✓ Public key saved to:  {args.public_key}\n")
    else:
        # Load existing keys
        if not os.path.exists(args.signing_key):
            print(f"❌ Error: Signing key not found at '{args.signing_key}'")
            print("   Use --generate-keys to create new keys\n")
            return 1
        
        print(f"🔑 Loading signing key from: {args.signing_key}")
        with open(args.signing_key, "rb") as f:
            signing_key = f.read()
        
        if os.path.exists(args.public_key):
            with open(args.public_key, "rb") as f:
                public_key = f.read()
            print(f"   Public key loaded from: {args.public_key}\n")
        else:
            public_key = None
            print(f"   ⚠ Warning: Public key not found at '{args.public_key}'\n")
    
    # Convert image to .pxl
    print("🔒 Converting to encrypted .pxl format...")
    try:
        pack_image(args.input, temp_pxl, signing_key)
        print(f"   ✓ Successfully created temporary .pxl file")
        
        # Show file sizes
        original_size = os.path.getsize(args.input)
        pxl_size = os.path.getsize(temp_pxl)
        overhead = pxl_size - original_size
        
        print(f"\n📊 File Statistics:")
        print(f"   Original size: {format_bytes(original_size)}")
        print(f"   .pxl size:     {format_bytes(pxl_size)}")
        print(f"   Overhead:      {format_bytes(overhead)} ({overhead/original_size*100:.1f}%)\n")
        
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        if os.path.exists(temp_pxl):
            os.remove(temp_pxl)
        return 1
    
    # Verify if requested
    if args.verify:
        if public_key is None:
            print("⚠ Warning: Cannot verify without public key\n")
        else:
            print("🔍 Verifying .pxl file integrity...")
            is_valid = verify_pxl(temp_pxl, public_key)
            
            if is_valid:
                print("   ✓ Verification PASSED - File is authentic!\n")
            else:
                print("   ❌ Verification FAILED - File may be corrupted!\n")
                if os.path.exists(temp_pxl):
                    os.remove(temp_pxl)
                return 1
    
    # Package into zip file
    print("📦 Packaging .pxl and public key into .zip...")
    try:
        with zipfile.ZipFile(args.output, 'w', zipfile.ZIP_DEFLATED) as zipf:
            # Add .pxl file
            base_pxl_name = os.path.splitext(os.path.basename(args.input))[0] + ".pxl"
            zipf.write(temp_pxl, base_pxl_name)
            
            # Add public key
            zipf.write(args.public_key, "public_key.bin")
        
        # Get final zip size
        zip_size = os.path.getsize(args.output)
        print(f"   ✓ Successfully created '{args.output}'")
        print(f"   Zip size: {format_bytes(zip_size)}\n")
        
    except Exception as e:
        print(f"   ❌ Error creating zip: {e}\n")
        if os.path.exists(temp_pxl):
            os.remove(temp_pxl)
        return 1
    finally:
        # Clean up temporary .pxl file
        if os.path.exists(temp_pxl):
            os.remove(temp_pxl)
    
    print("✅ Conversion complete!")
    print(f"\nTo view the image:")
    print(f"   python view.py\n")
    print(f"Package contents:")
    print(f"   📦 {args.output}")
    print(f"      ├── {base_pxl_name}")
    print(f"      └── public_key.bin")
    print(f"\nKeys stored separately:")
    print(f"   🔑 Signing key: {args.signing_key}")
    print(f"   🔑 Public key:  {args.public_key}")
    
    return 0


def format_bytes(bytes_val):
    """Format bytes as human-readable string"""
    if bytes_val < 1024:
        return f"{bytes_val} B"
    elif bytes_val < 1024 * 1024:
        return f"{bytes_val / 1024:.2f} KB"
    else:
        return f"{bytes_val / (1024 * 1024):.2f} MB"


if __name__ == "__main__":
    exit(main())