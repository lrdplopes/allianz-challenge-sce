import json
import logging
import os
import uuid
from botocore.exceptions import ClientError

from common import (
    VPCManager,
    VPCMetadataStore,
    success_response,
    validation_error_response,
    internal_error_response,
    validate_create_vpc_request
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-2')


def handler(event, context):
    """Lambda handler for creating VPCs"""
    logger.info("Received CreateVPC request")
    logger.info(f"Event: {json.dumps(event)}")

    
    request_id = context.aws_request_id if context else str(uuid.uuid4())

    try:
        
        body = json.loads(event.get('body', '{}')) if isinstance(event.get('body'), str) else event.get('body', {})

        logger.info(f"Request body: {json.dumps(body)}")

        
        is_valid, error_message, validated_data = validate_create_vpc_request(body)
        if not is_valid:
            logger.warning(f"Validation failed: {error_message}")
            return validation_error_response(error_message)

        name = validated_data['name']
        cidr_block = validated_data['cidr_block']

        logger.info(f"Creating VPC: name={name}, cidr={cidr_block}, request_id={request_id}")

        
        vpc_manager = VPCManager(region=AWS_REGION)
        metadata_store = VPCMetadataStore()

        
        vpc_details = vpc_manager.create_vpc(
            name=name,
            cidr_block=cidr_block,
            request_id=request_id
        )

        logger.info(f"VPC created successfully: {vpc_details['vpc_id']}")

        
        metadata_store.save_vpc(vpc_details)

        logger.info(f"VPC metadata saved to DynamoDB: {vpc_details['vpc_id']}")

        
        return success_response(
            data=vpc_details,
            status_code=201,
            message=f"VPC '{name}' created successfully"
        )

    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON in request body: {str(e)}")
        return validation_error_response("Invalid JSON in request body")

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']

        logger.error(f"AWS API error: {error_code} - {error_message}")

        
        if error_code == 'VpcLimitExceeded':
            return validation_error_response(
                "VPC limit exceeded. Please delete unused VPCs or request a limit increase.",
                details={'aws_error': error_code}
            )
        elif error_code == 'InvalidVpcRange':
            return validation_error_response(
                f"Invalid CIDR block: {error_message}",
                details={'aws_error': error_code}
            )
        else:
            return internal_error_response(e)

    except ValueError as e:
        
        logger.error(f"Validation error: {str(e)}")
        return validation_error_response(str(e))

    except Exception as e:
        
        logger.exception("Unexpected error creating VPC")
        return internal_error_response(e)
