import geoip2.database
from ipaddress import ip_address, IPv4Address
from .models import RequestLog
import logging

# Setup logging for debugging
logger = logging.getLogger(__name__)

# Define the path to the GeoLite directory (adjust paths as needed)
GEOLITE_DIR = "/home/lofa/Desktop/XXXXXXXXXXXXXXXX/GeoLite"  # Update this path as needed

# Paths to GeoLite2 databases (relative to the project root)
ASN_DB_PATH = f"{GEOLITE_DIR}/GeoLite2-ASN.mmdb"
CITY_DB_PATH = f"{GEOLITE_DIR}/GeoLite2-City.mmdb"

def update_request_log_with_location_data(request_log):
    """
    Update a RequestLog instance with country, city, and ASN information
    using the GeoLite2 databases.

    Args:
        request_log (RequestLog): An instance of the RequestLog model.
    """
    # Check if IP address is a loopback address (e.g., 127.0.0.1)
    ip = ip_address(request_log.ip_address)
    if isinstance(ip, IPv4Address) and ip.is_loopback:
        # Skip lookup for loopback addresses and set default values
        request_log.country = 'Localhost'
        request_log.city = 'Localhost'
        request_log.autonomous_system_number = None
        request_log.autonomous_system_organization = None
        request_log.save()
        return

    try:
        # Open GeoLite2 database readers
        asn_reader = geoip2.database.Reader(ASN_DB_PATH)
        city_reader = geoip2.database.Reader(CITY_DB_PATH)

        # Lookup ASN information
        asn_response = asn_reader.asn(request_log.ip_address)
        request_log.autonomous_system_number = asn_response.autonomous_system_number
        request_log.autonomous_system_organization = asn_response.autonomous_system_organization

        # Lookup city and country information
        city_response = city_reader.city(request_log.ip_address)
        request_log.country = city_response.country.name
        request_log.city = city_response.city.name

        # Save the updated request log entry
        request_log.save()

        # Close the database readers
        asn_reader.close()
        city_reader.close()

    except Exception as e:
        logger.error(f"Failed to update location data for IP {request_log.ip_address}: {e}")
        request_log.country = 'Unknown'
        request_log.city = 'Unknown'
        request_log.autonomous_system_number = None
        request_log.autonomous_system_organization = None
        request_log.save()
