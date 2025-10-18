"""
Metadata extraction and generation utilities
"""

from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from typing import Dict, Any
import datetime


def extract_metadata(image_file: str) -> Dict[str, Any]:
    """
    Extract camera metadata from image EXIF/XMP data
    
    Args:
        image_file: Path to image file
        
    Returns:
        Dictionary containing metadata
    """
    metadata = {}
    
    try:
        with Image.open(image_file) as img:
            # Get image dimensions
            metadata["width"] = img.width
            metadata["height"] = img.height
            metadata["format"] = img.format
            
            # Extract EXIF data
            exif_data = img._getexif()
            
            if exif_data:
                # Extract relevant EXIF fields
                for tag_id, value in exif_data.items():
                    tag = TAGS.get(tag_id, tag_id)
                    
                    # Camera make and model
                    if tag == "Make":
                        metadata["make"] = str(value).strip()
                    elif tag == "Model":
                        metadata["model"] = str(value).strip()
                    
                    # Date and time
                    elif tag == "DateTimeOriginal":
                        metadata["datetime_original"] = str(value)
                    elif tag == "DateTime":
                        if "datetime_original" not in metadata:
                            metadata["datetime_original"] = str(value)
                    
                    # Focal length
                    elif tag == "FocalLength":
                        if isinstance(value, tuple):
                            metadata["focal_length"] = f"{value[0]/value[1]:.1f}mm"
                        else:
                            metadata["focal_length"] = f"{value}mm"
                    
                    # ISO
                    elif tag == "ISOSpeedRatings":
                        metadata["iso"] = value
                    
                    # GPS information
                    elif tag == "GPSInfo":
                        gps_data = {}
                        for gps_tag_id in value:
                            gps_tag = GPSTAGS.get(gps_tag_id, gps_tag_id)
                            gps_data[gps_tag] = value[gps_tag_id]
                        
                        # Convert GPS coordinates to readable format
                        if "GPSLatitude" in gps_data and "GPSLongitude" in gps_data:
                            lat = _convert_gps_coordinate(
                                gps_data["GPSLatitude"],
                                gps_data.get("GPSLatitudeRef", "N")
                            )
                            lon = _convert_gps_coordinate(
                                gps_data["GPSLongitude"],
                                gps_data.get("GPSLongitudeRef", "E")
                            )
                            metadata["gps_info"] = f"{lat}, {lon}"
                    
                    # Exposure time
                    elif tag == "ExposureTime":
                        if isinstance(value, tuple):
                            metadata["exposure_time"] = f"{value[0]}/{value[1]}s"
                        else:
                            metadata["exposure_time"] = f"{value}s"
                    
                    # F-number
                    elif tag == "FNumber":
                        if isinstance(value, tuple):
                            metadata["f_number"] = f"f/{value[0]/value[1]:.1f}"
                        else:
                            metadata["f_number"] = f"f/{value}"
            
            # If no EXIF data found, generate synthetic metadata
            if not exif_data or len(metadata) <= 3:  # Only has width, height, format
                metadata.update(generate_synthetic_metadata(img.width, img.height))
    
    except Exception as e:
        print(f"Warning: Could not extract metadata: {e}")
        # Generate synthetic metadata as fallback
        try:
            with Image.open(image_file) as img:
                metadata = generate_synthetic_metadata(img.width, img.height)
        except:
            metadata = generate_synthetic_metadata(0, 0)
    
    return metadata


def generate_synthetic_metadata(width: int, height: int) -> Dict[str, Any]:
    """
    Generate synthetic metadata when camera info is unavailable
    
    Args:
        width: Image width in pixels
        height: Image height in pixels
        
    Returns:
        Dictionary containing synthetic metadata
    """
    return {
        "width": width,
        "height": height,
        "format": "Unknown",
        "make": "Unknown",
        "model": "Unknown",
        "datetime_original": datetime.datetime.now().isoformat(),
        "source": "synthetic"
    }


def _convert_gps_coordinate(coord: tuple, ref: str) -> str:
    """
    Convert GPS coordinate from EXIF format to decimal degrees
    
    Args:
        coord: Tuple of (degrees, minutes, seconds)
        ref: Reference (N/S for latitude, E/W for longitude)
        
    Returns:
        Formatted coordinate string
    """
    try:
        degrees = coord[0][0] / coord[0][1]
        minutes = coord[1][0] / coord[1][1]
        seconds = coord[2][0] / coord[2][1]
        
        decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
        
        if ref in ["S", "W"]:
            decimal = -decimal
        
        return f"{decimal:.6f} {ref}"
    except:
        return f"Unknown {ref}"