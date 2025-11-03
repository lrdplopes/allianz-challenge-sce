import re
from typing import Dict, Optional, Tuple


def validate_vpc_name(name: str) -> Tuple[bool, Optional[str]]:
    if not name:
        return False, "VPC name is required"

    if len(name) > 255:
        return False, "VPC name must be 255 characters or less"

    if len(name) < 1:
        return False, "VPC name must be at least 1 character"

    if not name[0].isalnum():
        return False, "VPC name must start with an alphanumeric character"

    if not re.match(r'^[a-zA-Z0-9][a-zA-Z0-9_-]*$', name):
        return False, "VPC name can only contain alphanumeric characters, hyphens, and underscores"

    return True, None


def validate_cidr_block(cidr: str) -> Tuple[bool, Optional[str]]:
    if not cidr:
        return False, "CIDR block is required"

    if '/' not in cidr:
        return False, "CIDR block must include a prefix (e.g., 10.0.0.0/16)"

    try:
        ip_part, prefix_part = cidr.split('/')

        octets = ip_part.split('.')
        if len(octets) != 4:
            return False, "CIDR block must have valid IPv4 address format"

        for octet in octets:
            octet_int = int(octet)
            if octet_int < 0 or octet_int > 255:
                return False, f"Invalid IP octet: {octet} (must be 0-255)"

        prefix = int(prefix_part)
        if prefix < 16 or prefix > 28:
            return False, "VPC CIDR prefix must be between /16 and /28"

        return True, None

    except ValueError as e:
        return False, f"Invalid CIDR block format: {str(e)}"


def validate_vpc_id(vpc_id: str) -> Tuple[bool, Optional[str]]:
    if not vpc_id:
        return False, "VPC ID is required"

    if not re.match(r'^vpc-[a-f0-9]{8,17}$', vpc_id):
        return False, "Invalid VPC ID format (expected: vpc-xxxxxxxx)"

    return True, None


def validate_create_vpc_request(body: Dict) -> Tuple[bool, Optional[str], Optional[Dict]]:
    if body is None:
        return False, "Request body is required", None

    name = body.get('name')
    is_valid, error = validate_vpc_name(name)
    if not is_valid:
        return False, error, None

    cidr_block = body.get('cidr_block', '10.0.0.0/16')
    is_valid, error = validate_cidr_block(cidr_block)
    if not is_valid:
        return False, error, None

    validated_data = {
        'name': name.strip(),
        'cidr_block': cidr_block.strip()
    }

    return True, None, validated_data
