import uuid
import string

def generate_license_key():
    """
    Generate a 16-digit license key in the format WLB-xxxx-xxxx-xxxx-xxxx
    where each x is a random alphanumeric character (uppercase letters and digits)
    """
    # Generate a UUID and convert to uppercase alphanumeric string
    uuid_obj = uuid.uuid4()
    uuid_str = str(uuid_obj).replace('-', '').upper()

    # Take first 16 characters and format as WLB-xxxx-xxxx-xxxx-xxxx
    license_part = uuid_str[:16]

    # Format as WLB-xxxx-xxxx-xxxx-xxxx
    formatted_key = f"WLB-{license_part[:4]}-{license_part[4:8]}-{license_part[8:12]}-{license_part[12:16]}"

    return formatted_key

if __name__ == "__main__":
    # Test the function
    key = generate_license_key()
    print(f"Generated License Key: {key}")
    print(f"Length: {len(key)}")
    print(f"Format check: {key.startswith('WLB-') and len(key.replace('-', '')) == 19}")