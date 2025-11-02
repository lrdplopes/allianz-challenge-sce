import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'app', 'lambda_functions'))

from common.validation import (
    validate_vpc_name,
    validate_cidr_block,
    validate_vpc_id,
    validate_create_vpc_request
)


class TestVPCNameValidation:
    def test_valid_names(self):
        """Test valid VPC names"""
        valid_names = [
            "my-vpc",
            "vpc123",
            "test_vpc",
            "VPC-Test-123",
            "a",
            "a" * 255
        ]

        for name in valid_names:
            is_valid, error = validate_vpc_name(name)
            assert is_valid, f"Expected '{name}' to be valid, got error: {error}"
            assert error is None

    def test_invalid_names(self):
        """Test invalid VPC names"""
        invalid_names = [
            ("", "VPC name is required"),
            ("-starts-with-hyphen", "must start with an alphanumeric character"),
            ("_starts_with_underscore", "must start with an alphanumeric character"),
            ("a" * 256, "must be 255 characters or less"),
            ("has space", "can only contain alphanumeric characters"),
            ("has@special", "can only contain alphanumeric characters"),
        ]

        for name, expected_error_fragment in invalid_names:
            is_valid, error = validate_vpc_name(name)
            assert not is_valid, f"Expected '{name}' to be invalid"
            assert error is not None
            assert expected_error_fragment.lower() in error.lower(), \
                f"Expected error containing '{expected_error_fragment}', got '{error}'"


class TestCIDRValidation:
    """Test CIDR block validation"""

    def test_valid_cidr_blocks(self):
        """Test valid CIDR blocks"""
        valid_cidrs = [
            "10.0.0.0/16",
            "172.16.0.0/20",
            "192.168.0.0/24",
            "10.10.10.0/28",
        ]

        for cidr in valid_cidrs:
            is_valid, error = validate_cidr_block(cidr)
            assert is_valid, f"Expected '{cidr}' to be valid, got error: {error}"
            assert error is None

    def test_invalid_cidr_blocks(self):
        """Test invalid CIDR blocks"""
        invalid_cidrs = [
            ("", "CIDR block is required"),
            ("10.0.0.0", "must include a prefix"),
            ("10.0.0.0/15", "must be between /16 and /28"),
            ("10.0.0.0/29", "must be between /16 and /28"),
            ("256.0.0.0/16", "must be 0-255"),
            ("10.0.0/16", "must have valid IPv4"),
            ("invalid/16", "CIDR block must have valid IPv4"),
        ]

        for cidr, expected_error_fragment in invalid_cidrs:
            is_valid, error = validate_cidr_block(cidr)
            assert not is_valid, f"Expected '{cidr}' to be invalid"
            assert error is not None
            assert expected_error_fragment.lower() in error.lower(), \
                f"Expected error containing '{expected_error_fragment}', got '{error}'"


class TestVPCIDValidation:
    """Test VPC ID validation"""

    def test_valid_vpc_ids(self):
        """Test valid VPC IDs"""
        valid_ids = [
            "vpc-12345678",
            "vpc-1234567890abcdef",
            "vpc-abcdef12",
        ]

        for vpc_id in valid_ids:
            is_valid, error = validate_vpc_id(vpc_id)
            assert is_valid, f"Expected '{vpc_id}' to be valid, got error: {error}"
            assert error is None

    def test_invalid_vpc_ids(self):
        """Test invalid VPC IDs"""
        invalid_ids = [
            ("", "VPC ID is required"),
            ("vpc-", "Invalid VPC ID format"),
            ("vpc-ABCDEF12", "Invalid VPC ID format"),
            ("vpc-12345", "Invalid VPC ID format"),
            ("invalid", "Invalid VPC ID format"),
        ]

        for vpc_id, expected_error_fragment in invalid_ids:
            is_valid, error = validate_vpc_id(vpc_id)
            assert not is_valid, f"Expected '{vpc_id}' to be invalid"
            assert error is not None
            assert expected_error_fragment in error, \
                f"Expected error containing '{expected_error_fragment}', got '{error}'"


class TestCreateVPCRequestValidation:
    """Test create VPC request validation"""

    def test_valid_requests(self):
        """Test valid create VPC requests"""
        valid_requests = [
            {"name": "my-vpc", "cidr_block": "10.0.0.0/16"},
            {"name": "test-vpc"},
            {"name": "vpc123", "cidr_block": "172.16.0.0/20"},
        ]

        for request in valid_requests:
            is_valid, error, validated = validate_create_vpc_request(request)
            assert is_valid, f"Expected request to be valid, got error: {error}"
            assert error is None
            assert validated is not None
            assert "name" in validated
            assert "cidr_block" in validated

    def test_invalid_requests(self):
        """Test invalid create VPC requests"""
        invalid_requests = [
            (None, "Request body is required"),
            ({}, "VPC name is required"),
            ({"name": ""}, "VPC name is required"),
            ({"name": "test", "cidr_block": "invalid"}, "must include a prefix"),
            ({"name": "-invalid"}, "must start with an alphanumeric"),
        ]

        for request, expected_error_fragment in invalid_requests:
            is_valid, error, validated = validate_create_vpc_request(request)
            assert not is_valid, f"Expected request to be invalid: {request}"
            assert error is not None
            assert expected_error_fragment.lower() in error.lower(), \
                f"Expected error containing '{expected_error_fragment}', got '{error}'"
            assert validated is None


if __name__ == "__main__":
    import traceback

    test_classes = [
        TestVPCNameValidation,
        TestCIDRValidation,
        TestVPCIDValidation,
        TestCreateVPCRequestValidation,
    ]

    total_tests = 0
    passed_tests = 0
    failed_tests = 0

    for test_class in test_classes:
        print(f"\nRunning {test_class.__name__}...")
        test_instance = test_class()

        for method_name in dir(test_instance):
            if method_name.startswith("test_"):
                total_tests += 1
                try:
                    method = getattr(test_instance, method_name)
                    method()
                    print(f"  ✓ {method_name}")
                    passed_tests += 1
                except AssertionError as e:
                    print(f"  ✗ {method_name}: {str(e)}")
                    failed_tests += 1
                except Exception as e:
                    print(f"  ✗ {method_name}: {type(e).__name__}: {str(e)}")
                    traceback.print_exc()
                    failed_tests += 1

    print(f"\n{'='*60}")
    print(f"Total: {total_tests} | Passed: {passed_tests} | Failed: {failed_tests}")
    print(f"{'='*60}")

    if failed_tests == 0:
        print("✓ All tests passed!")
        exit(0)
    else:
        print(f"✗ {failed_tests} test(s) failed")
        exit(1)
