"""
Metadata extraction and generation utilities (raw version)
"""

from PIL import Image
from typing import Dict, Any
import datetime


def extract_metadata(image_file: str) -> Dict[str, Any]:
    """
    Extract raw metadata from image EXIF/XMP data without parsing or formatting
    
    Args:
        image_file: Path to image file
        
    Returns:
        Dictionary containing raw metadata
    """
    metadata = {}

    try:
        with Image.open(image_file) as img:
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format

            # Get EXIF data (unparsed)
            exif_data = img._getexif()

            if exif_data:
                # Just store the raw EXIF dictionary
                metadata["exif"] = {str(k): str(v) for k, v in exif_data.items()}
            else:
                metadata.update(generate_synthetic_metadata(img.width, img.height))

    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
        try:
            with Image.open(image_file) as img:
                metadata = generate_synthetic_metadata(img.width, img.height)
        except:
            metadata = generate_synthetic_metadata(0, 0)
    #print(metadata)
    return metadata


def generate_synthetic_metadata(width: int, height: int) -> Dict[str, Any]:
    """
    Generate minimal synthetic metadata when no EXIF data is available
    """
    return {
        "width": width,
        "height": height,
        "format": "Unknown",
        "datetime_generated": datetime.datetime.now().isoformat(),
        "source": "synthetic"
    }
