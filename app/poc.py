from PIL import Image, ImageDraw, ImageFont, ExifTags
from geopy.geocoders import Nominatim
CHANGE_LATER_GEOCODER_USER_AGENT = "demo20241109"

def get_exif_data(image):
    """Extract EXIF data and GPS information from an image file."""
    exif_data = {}
    gps_data = {}
    exif_info = image._getexif() or {}

    for tag, value in exif_info.items():
        tag_name = ExifTags.TAGS.get(tag, str(tag))
        if tag_name == "GPSInfo":
            gps_data.update({ExifTags.GPSTAGS.get(k, str(k)): v for k, v in value.items()})
        else:
            exif_data[tag_name] = value

    return exif_data, gps_data

def get_decimal_from_dms(dms, ref):
    """Convert GPS coordinates from degrees, minutes, seconds to decimal format."""
    degrees, minutes, seconds = dms
    decimal = degrees + (minutes / 60) + (seconds / 3600)
    return -decimal if ref in ['S', 'W'] else decimal

def get_lat_lon(gps_data):
    """Extract latitude and longitude from GPS data if available."""
    try:
        lat = get_decimal_from_dms(gps_data['GPSLatitude'], gps_data['GPSLatitudeRef'])
        lon = get_decimal_from_dms(gps_data['GPSLongitude'], gps_data['GPSLongitudeRef'])
        return lat, lon
    except KeyError:
        return None, None

def reverse_geocode(lat, lon):
    """Get city name from latitude and longitude using geopy."""
    geolocator = Nominatim(user_agent=CHANGE_LATER_GEOCODER_USER_AGENT)
    location = geolocator.reverse((lat, lon), language='en')
    if location:
        address = location.raw.get('address', {})
        return address.get('city', address.get('town', address.get('village', 'City not found')))
    return "City not found"

def correct_image_orientation(img):
    """Correct image orientation based on EXIF data.
    """

    try: # Fix me
        for orientation in ExifTags.TAGS:
            if ExifTags.TAGS[orientation] == 'Orientation':
                orient = img._getexif().get(orientation)
                if orient == 3:
                    img = img.rotate(180, expand=True)
                elif orient == 6:
                    img = img.rotate(270, expand=True)
                elif orient == 8:
                    img = img.rotate(90, expand=True)
                break
    except (AttributeError, KeyError):
        pass
    return img

def add_stamp(image_path, text, output_path):
    """Add a text stamp to an image and save to an output path."""
    with Image.open(image_path) as img:
        img = correct_image_orientation(img).convert('RGB')
        draw = ImageDraw.Draw(img)
        font = ImageFont.truetype("arial.ttf", 100)
        text_width, text_height = draw.textsize(text, font=font)
        text_position = (img.width - text_width - 10, img.height - text_height - 10)  # Position text at bottom right
        draw.text(text_position, text, font=font, fill=(252, 204, 116))  # Old-school yellow
        img.save(output_path, 'JPEG')

if __name__ == "__main__":
    image_path = 'input.jpg'
    output_path = "output.jpg"

    with Image.open(image_path) as img:
        exif_data, gps_data = get_exif_data(img)
        date_taken = exif_data.get('DateTimeOriginal', 'Date not found').split()[0]
        latitude, longitude = get_lat_lon(gps_data)

        if latitude and longitude:
            city = reverse_geocode(latitude, longitude)
            text = f"{city}\n{date_taken}"
        else:
            text = date_taken

        add_stamp(image_path, text, output_path)
