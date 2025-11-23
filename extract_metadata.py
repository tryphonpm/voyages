import os
import json
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

IMAGE_DIR = r"E:\202507_Lres"
OUTPUT_FILE = "images_metadata.json"

def get_location_name(lat, lon):
    try:
        geolocator = Nominatim(user_agent="image_metadata_extractor_v1")
        location = geolocator.reverse(f"{lat}, {lon}", exactly_one=True, language='fr')
        if location:
            address = location.raw.get('address', {})
            city = address.get('city') or address.get('town') or address.get('village') or address.get('hamlet') or address.get('county')
            return city
    except (GeocoderTimedOut, Exception) as e:
        print(f"Geocoding error: {e}")
    return None

def get_exif_data(image):
    exif_data = {}
    info = image._getexif()
    if info:
        for tag, value in info.items():
            decoded = TAGS.get(tag, tag)
            if decoded == "GPSInfo":
                gps_data = {}
                for t in value:
                    sub_decoded = GPSTAGS.get(t, t)
                    gps_data[sub_decoded] = value[t]
                exif_data[decoded] = gps_data
            else:
                exif_data[decoded] = value
    return exif_data

def convert_to_degrees(value):
    d = float(value[0])
    m = float(value[1])
    s = float(value[2])
    return d + (m / 60.0) + (s / 3600.0)

def get_lat_lon(exif_data):
    lat = None
    lon = None
    if "GPSInfo" in exif_data:
        gps_info = exif_data["GPSInfo"]
        gps_latitude = gps_info.get("GPSLatitude")
        gps_latitude_ref = gps_info.get("GPSLatitudeRef")
        gps_longitude = gps_info.get("GPSLongitude")
        gps_longitude_ref = gps_info.get("GPSLongitudeRef")

        if gps_latitude and gps_latitude_ref and gps_longitude and gps_longitude_ref:
            lat = convert_to_degrees(gps_latitude)
            if gps_latitude_ref != "N":
                lat = -lat
            lon = convert_to_degrees(gps_longitude)
            if gps_longitude_ref != "E":
                lon = -lon
    return lat, lon

def format_size(size_bytes):
    if size_bytes == 0:
        return "0 B"
    size_name = ("B", "KB", "MB", "GB", "TB")
    i = 0
    p = size_bytes
    while p >= 1024 and i < len(size_name) - 1:
        p /= 1024.0
        i += 1
    return f"{p:.2f} {size_name[i]}"

def extract_metadata():
    results = []
    
    if not os.path.exists(IMAGE_DIR):
        print(f"Directory not found: {IMAGE_DIR}")
        return

    for filename in os.listdir(IMAGE_DIR):
        if filename.lower().endswith(('.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.gif')):
            filepath = os.path.join(IMAGE_DIR, filename)
            try:
                with Image.open(filepath) as img:
                    width, height = img.size
                    file_size = os.path.getsize(filepath)
                    
                    exif = get_exif_data(img)
                    lat, lon = get_lat_lon(exif)
                    
                    # Resolution (DPI)
                    dpi = img.info.get('dpi')
                    resolution = f"{int(dpi[0])}x{int(dpi[1])} dpi" if dpi else "N/A"

                    # Creation date
                    # Try DateTimeOriginal first, then DateTime, then file creation time
                    creation_date = exif.get("DateTimeOriginal") or exif.get("DateTime")
                    
                    if not creation_date:
                        # Fallback to file creation time
                        ctime = os.path.getctime(filepath)
                        creation_date = datetime.fromtimestamp(ctime).strftime('%Y:%m:%d %H:%M:%S')

                    # Clean up date format if needed (Exif is typically YYYY:MM:DD HH:MM:SS)
                    
                    date_part = "N/A"
                    time_part = "N/A"
                    if creation_date and " " in creation_date:
                        try:
                            raw_date, time_part = creation_date.split(" ", 1)
                            # Convert YYYY:MM:DD to DD/MM/YYYY
                            if ":" in raw_date:
                                parts = raw_date.split(":")
                                if len(parts) == 3:
                                    date_part = f"{parts[2]}/{parts[1]}/{parts[0]}"
                                else:
                                    date_part = raw_date
                            else:
                                date_part = raw_date
                        except ValueError:
                            pass

                    gps_position = None
                    location_name = None
                    if lat is not None and lon is not None:
                        gps_position = {"lat": lat, "lon": lon}
                        location_name = get_location_name(lat, lon)

                    formatted_size = format_size(file_size)

                    metadata = {
                        "label": filename,
                        "largeur": width,
                        "hauteur": height,
                        "résolution": resolution,
                        "taille": formatted_size,
                        "position GPS": gps_position,
                        "lieu": location_name,
                        "horodatage de création": creation_date,
                        "date": date_part,
                        "heure": time_part
                    }
                    results.append(metadata)
            except Exception as e:
                print(f"Error processing {filename}: {e}")

    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=4, ensure_ascii=False)
    
    print(f"Metadata extracted to {OUTPUT_FILE}")

if __name__ == "__main__":
    extract_metadata()

