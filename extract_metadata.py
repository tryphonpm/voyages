import os
import json
import requests
import mimetypes
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS
from datetime import datetime
from geopy.geocoders import Nominatim
from geopy.exc import GeocoderTimedOut

IMAGE_DIR = r"E:\202507_Lres"
OUTPUT_FILE = "images_metadata.json"
# Define base URL for Vercel Blob storage
BLOB_BASE_URL = "https://voyages-wc84-4cx9ouza0-tryphonpms-projects.vercel.app" # Or direct blob URL if known
# Actually, for public blobs it's usually https://[store-id].public.blob.vercel-storage.com/path
# However, the user mentioned the deployment URL and that images are in '2025-07' subfolder.
# If they are served via the app's public directory, that's different. 
# But "associated Vercel Blob... contains images in a subfolder" implies Blob storage.
# Standard Vercel Blob public URLs look like:
# https://[store-id].public.blob.vercel-storage.com/[path/to/file]
# Without the store ID, we can't construct the exact URL easily unless we know it.
# BUT, the user said "associated with blob 'voyages'".
# Let's assume for now we construct the URL based on the likely path in the blob store.
# If we don't know the store ID, we might need to ask or assume a pattern.
# Wait, if they are already uploaded, maybe we just need to reference them.
# User said: "blob vercel 'voyages' qui contient déja les images dans un sous-dossier '2025-07'"
# Usually the URL is: https://[store-id].public.blob.vercel-storage.com/2025-07/[filename]
# We need that Store ID (the part before .public.blob...).
# The deployment URL "voyages-wc84..." doesn't necessarily give the blob store ID directly.
# Let's search or just define a placeholder and ask user, or use a relative path if the app proxies it?
# No, the app is python/flask, it probably doesn't proxy blob automatically unless configured.
# Let's try to find the Store ID from the previous error message? 
# Error message was generic 403.
# Let's look at the user's query again.
# "le déploiement vercel ... est associé au blob vercel 'voyages'"
# It's possible the user expects us to use the deployment URL? 
# No, Vercel Blob is a separate storage.
# Let's hardcode the base URL structure and ask user for the specific domain if this fails, 
# OR, since the user provided the deployment URL, maybe they serve them via a rewrite?
# "vercel.json" rewrites can map /images to blob.
# Let's assume the user wants us to use the standard Blob URL format.
# To keep it simple and safe, I will update the script to NOT upload, and instead
# construct the URL assuming a standard format if I can find the ID, or just 
# use a configurable base URL.
# Actually, looking at the user's previous error, we don't have the ID.
# I'll disable upload and try to construct the URL.
# Since I don't have the blob store domain, I will use a placeholder or ask the user to provide the full public URL prefix.
# Better yet, I will modify the script to take a BLOB_BASE_URL variable, and default to a placeholder
# that the user can easily change.
# Wait, the user provided the Deployment URL. Maybe they want to access images via that?
# If they have a rewrite rule `source: "/images/:path*"` -> `destination: "blob-url/:path*"`
# Then we could use `https://voyages-wc84.../images/2025-07/filename`.
# This is a common pattern.
# Let's assume the user wants to link to the files that are ALREADY there.
# I will remove the upload logic.
# I will set the URL to `https://[store-id].public.blob.vercel-storage.com/2025-07/{filename}`
# AND I will ask the user for the Store ID (the random string part of the blob URL).
# OR, I can use the deployment URL if they have a proxy.
# Let's stick to removing the upload first.

# RE-READING user query carefully:
# "L'utilisation du TOKEN ... n'est plus nécessaire" -> Remove upload code.
# "blob vercel 'voyages' ... sous-dossier '2025-07'" -> Images are at `2025-07/filename`.

# I'll modify the script to generate metadata with a placeholder URL that the user needs to fill, 
# or I can try to guess.
# Actually, the most robust way is to just generate the metadata with the filename, 
# and let the frontend handle the base URL? 
# The frontend currently does `img.url || /images/img.label`.
# If I put the full blob URL in `img.url`, it works.
# I will add a constant `BLOB_BASE_URL` at the top of the script.
# I'll set it to a placeholder like "REPLACE_WITH_YOUR_BLOB_STORE_URL/2025-07" 
# and instruct the user to update it.
# This is safer than guessing.

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

    # URL de base pour les images hébergées sur Vercel Blob
    # À REMPLACER par l'URL réelle de votre store.
    # Format typique: https://<store-id>.public.blob.vercel-storage.com/2025-07/
    # Pour l'instant, on utilise un placeholder ou l'URL de déploiement si configuré via proxy.
    # Mais comme les fichiers sont dans un sous-dossier '2025-07', on l'ajoute au chemin.
    
    # NOTE UTILISATEUR: Remplacez cette URL par l'URL publique de votre dossier '2025-07' dans le Blob Store.
    # Vous pouvez la trouver en cliquant sur un fichier dans le dashboard Vercel Storage.
    BLOB_BASE_URL = "https://voyages-wc84-4cx9ouza0-tryphonpms-projects.vercel.app/images_proxy_or_blob_url_here/2025-07"

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
                    creation_date = exif.get("DateTimeOriginal") or exif.get("DateTime")
                    
                    if not creation_date:
                        ctime = os.path.getctime(filepath)
                        creation_date = datetime.fromtimestamp(ctime).strftime('%Y:%m:%d %H:%M:%S')

                    date_part = "N/A"
                    time_part = "N/A"
                    if creation_date and " " in creation_date:
                        try:
                            raw_date, time_part = creation_date.split(" ", 1)
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

                    # Construction de l'URL Blob (sans upload)
                    # On suppose que le nom du fichier est le même sur le blob
                    blob_url = f"{BLOB_BASE_URL}/{filename}"
                    
                    metadata = {
                        "label": filename,
                        "url": blob_url, 
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
    print(f"IMPORTANT: Please verify the 'url' fields in {OUTPUT_FILE} match your Vercel Blob public URLs.")

if __name__ == "__main__":
    extract_metadata()
