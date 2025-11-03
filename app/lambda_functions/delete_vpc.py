import json
import logging
import os
from botocore.exceptions import ClientError

from common import (
    VPCManager,
    VPCMetadataStore,
    success_response,
    not_found_response,
    validation_error_response,
    internal_error_response,
    validate_vpc_id
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)

AWS_REGION = os.environ.get('AWS_REGION', 'us-east-2')


def handler(event, context):
    """Lambda handler for deleting VPCs"""
    logger.info("Received DeleteVPC request")
    logger.info(f"Event: {json.dumps(event)}")

    try:
        
        path_parameters = event.get('pathParameters') or {}
        vpc_id = path_parameters.get('vpc_id')

        if not vpc_id:
            logger.warning("VPC ID not provided in path parameters")
            return validation_error_response("VPC ID is required")

        logger.info(f"Deleting VPC: {vpc_id}")

        
        is_valid, error_message = validate_vpc_id(vpc_id)
        if not is_valid:
            logger.warning(f"Invalid VPC ID format: {vpc_id}")
            return validation_error_response(error_message)

        
        vpc_manager = VPCManager(region=AWS_REGION)
        metadata_store = VPCMetadataStore()

        
        vpc_data = metadata_store.get_vpc(vpc_id)
        if not vpc_data:
            logger.info(f"VPC not found in metadata store: {vpc_id}")
            return not_found_response('VPC', vpc_id)

        
        metadata_store.update_vpc_status(vpc_id, 'deleting')
        logger.info(f"Updated VPC status to 'deleting': {vpc_id}")

        
        try:
            deletion_result = vpc_manager.delete_vpc(vpc_id)
            logger.info(f"VPC deleted from AWS: {vpc_id}")
        except ClientError as e:
            
            if e.response['Error']['Code'] == 'InvalidVpcID.NotFound':
                logger.warning(f"VPC not found in AWS (already deleted): {vpc_id}")
                deletion_result = {
                    'vpc_id': vpc_id,
                    'status': 'deleted',
                    'note': 'VPC was not found in AWS (may have been manually deleted)'
                }
            else:
                raise

        
        metadata_store.delete_vpc(vpc_id)
        logger.info(f"VPC metadata deleted from DynamoDB: {vpc_id}")

        
        return success_response(
            data=deletion_result,
            status_code=200,
            message=f"VPC '{vpc_id}' and all associated resources deleted successfully"
        )

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']

        logger.error(f"AWS API error: {error_code} - {error_message}")

        
        if error_code == 'DependencyViolation':
            return validation_error_response(
                "Cannot delete VPC due to existing dependencies. "
                "Please ensure all resources (EC2 instances, RDS, etc.) are deleted first.",
                details={'aws_error': error_code}
            )
        else:
            return internal_error_response(e)

    except Exception as e:
        
        logger.exception("Unexpected error deleting VPC")
        return internal_error_response(e)
