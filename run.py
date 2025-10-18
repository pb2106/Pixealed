"""
Example usage of the Pixealed .pxl converter

This script demonstrates:
1. Generating a keypair
2. Converting an image to .pxl format
3. Verifying the .pxl file
4. Reading and displaying the image
"""

import os
from modules.converter import pack_image, read_pxl, verify_pxl
from modules.crypto import generate_keypair
from PIL import Image
import io


def main():
    print("=== Pixealed .pxl Converter Demo ===\n")
    
    # Step 1: Generate keypair
    print("1. Generating Ed25519 keypair...")
    signing_key, public_key = generate_keypair()
    print(f"   Signing key: {signing_key.hex()[:32]}...")
    print(f"   Public key: {public_key.hex()[:32]}...")
    
    # Save keys for later use (in production, store these securely!)
    with open("signing_key.bin", "wb") as f:
        f.write(signing_key)
    with open("public_key.bin", "wb") as f:
        f.write(public_key)
    print("   Keys saved to signing_key.bin and public_key.bin\n")
    
    # Step 2: Convert image to .pxl
    input_image = "input.jpg"  # Change this to your image file
    output_pxl = "output.pxl"
    
    # Check if input file exists
    if not os.path.exists(input_image):
        print(f"Error: Input file '{input_image}' not found!")
        print("Please provide an image file (jpg, png, etc.) named 'input.jpg'")
        print("Or modify the 'input_image' variable in this script.\n")
        
        # Create a sample image for testing
        print("Creating a sample test image...")
        create_sample_image("input.jpg")
        print("Sample image 'input.jpg' created!\n")
    
    print(f"2. Converting '{input_image}' to .pxl format...")
    try:
        pack_image(input_image, output_pxl, signing_key)
        print(f"   ✓ Successfully created '{output_pxl}'")
        
        # Show file sizes
        original_size = os.path.getsize(input_image)
        pxl_size = os.path.getsize(output_pxl)
        overhead = pxl_size - original_size
        print(f"   Original size: {original_size:,} bytes")
        print(f"   .pxl size: {pxl_size:,} bytes")
        print(f"   Overhead: {overhead:,} bytes ({overhead/original_size*100:.1f}%)\n")
    except Exception as e:
        print(f"   ✗ Error: {e}\n")
        return
    
    # Step 3: Verify the .pxl file
    print("3. Verifying .pxl file integrity...")
    is_valid = verify_pxl(output_pxl, public_key)
    
    if is_valid:
        print("   ✓ Verification PASSED - File is authentic and unmodified!\n")
    else:
        print("   ✗ Verification FAILED - File may be tampered!\n")
        return
    
    # Step 4: Read and display metadata
    print("4. Reading .pxl file...")
    try:
        image_bytes, manifest = read_pxl(output_pxl)
        print(f"   ✓ Successfully read {len(image_bytes):,} bytes")
        
        print("\n   Metadata:")
        for key, value in manifest.get("metadata", {}).items():
            print(f"      {key}: {value}")
        
        print(f"\n   Integrity info:")
        print(f"      Chunks: {manifest['num_chunks']}")
        print(f"      Chunk size: {manifest['chunk_size']:,} bytes")
        print(f"      Merkle root: {manifest['merkle_root'][:16]}...")
        
    except Exception as e:
        print(f"   ✗ Error reading file: {e}\n")
        return
    
    # Step 5: Display the image
    print("\n5. Displaying original image...")
    try:
        image = Image.open(io.BytesIO(image_bytes))
        print(f"   Image size: {image.width}x{image.height}")
        print(f"   Format: {image.format}")
        image.show()
        print("   ✓ Image displayed successfully!\n")
    except Exception as e:
        print(f"   ✗ Error displaying image: {e}\n")
    
    # Step 6: Demonstrate tamper detection
    print("6. Testing tamper detection...")
    print("   Modifying .pxl file...")
    
    # Create a tampered copy
    tampered_file = "tampered.pxl"
    with open(output_pxl, "rb") as f:
        data = bytearray(f.read())
    
    # Modify a byte in the middle of the image data
    data[100] ^= 0xFF  # Flip bits
    
    with open(tampered_file, "wb") as f:
        f.write(data)
    
    print(f"   Verifying tampered file...")
    is_valid_tampered = verify_pxl(tampered_file, public_key)
    
    if not is_valid_tampered:
        print("   ✓ Tamper detected successfully!\n")
    else:
        print("   ✗ Warning: Tamper not detected!\n")
    
    # Cleanup
    if os.path.exists(tampered_file):
        os.remove(tampered_file)
    
    print("=== Demo Complete ===")
    print(f"\nYour files:")
    print(f"  - Original image: {input_image}")
    print(f"  - Packaged .pxl: {output_pxl}")
    print(f"  - Signing key: signing_key.bin")
    print(f"  - Public key: public_key.bin")


def create_sample_image(filename: str):
    """Create a sample image for testing"""
    from PIL import Image, ImageDraw, ImageFont
    
    # Create a colorful gradient image
    img = Image.new('RGB', (800, 600))
    draw = ImageDraw.Draw(img)
    
    # Draw gradient
    for y in range(600):
        r = int(255 * (y / 600))
        g = int(255 * (1 - y / 600))
        b = 128
        draw.rectangle([(0, y), (800, y+1)], fill=(r, g, b))
    
    # Add text
    try:
        draw.text((50, 250), "Pixealed Test Image", fill=(255, 255, 255))
        draw.text((50, 300), "Tamper-Proof Format", fill=(255, 255, 255))
    except:
        pass  # Skip text if font not available
    
    img.save(filename, "JPEG", quality=95)


if __name__ == "__main__":
    main()