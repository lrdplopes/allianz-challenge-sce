import json
import logging
import os
from botocore.exceptions import ClientError

from common import (
    VPCMetadataStore,
    success_response,
    not_found_response,
    internal_error_response,
    validate_vpc_id
)

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    """Lambda handler for retrieving VPCs"""
    logger.info("Received GetVPCs request")
    logger.info(f"Event: {json.dumps(event)}")

    try:
        metadata_store = VPCMetadataStore()

        path_parameters = event.get('pathParameters') or {}
        vpc_id = path_parameters.get('vpc_id')

        if vpc_id:
            logger.info(f"Retrieving specific VPC: {vpc_id}")

            is_valid, error_message = validate_vpc_id(vpc_id)
            if not is_valid:
                from common import validation_error_response
                return validation_error_response(error_message)

            
            vpc_data = metadata_store.get_vpc(vpc_id)

            if not vpc_data:
                logger.info(f"VPC not found: {vpc_id}")
                return not_found_response('VPC', vpc_id)

            logger.info(f"Retrieved VPC: {vpc_id}")
            return success_response(data=vpc_data)

        else:
            
            logger.info("Listing all VPCs")

            query_params = event.get('queryStringParameters') or {}
            limit = int(query_params.get('limit', 100))

            
            vpcs = metadata_store.list_vpcs(limit=limit)

            logger.info(f"Retrieved {len(vpcs)} VPCs")

            return success_response(
                data={
                    'vpcs': vpcs,
                    'count': len(vpcs)
                }
            )

    except ValueError as e:
        logger.error(f"Validation error: {str(e)}")
        from common import validation_error_response
        return validation_error_response(str(e))

    except ClientError as e:
        error_code = e.response['Error']['Code']
        error_message = e.response['Error']['Message']

        logger.error(f"AWS API error: {error_code} - {error_message}")
        return internal_error_response(e)

    except Exception as e:
        logger.exception("Unexpected error retrieving VPCs")
        return internal_error_response(e)
