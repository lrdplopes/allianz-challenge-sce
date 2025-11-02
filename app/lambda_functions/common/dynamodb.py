import logging
import os
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class VPCMetadataStore:
    def __init__(self, table_name: Optional[str] = None):
        self.table_name = table_name or os.environ.get('VPC_TABLE_NAME', 'vpc-metadata')
        self.dynamodb = boto3.resource('dynamodb')
        self.table = self.dynamodb.Table(self.table_name)
        logger.info(f"Initialized DynamoDB store with table: {self.table_name}")

    def save_vpc(self, vpc_data: Dict) -> Dict:
        try:
            if 'vpc_id' not in vpc_data:
                raise ValueError("vpc_id is required")

            logger.info(f"Saving VPC metadata: {vpc_data['vpc_id']}")
            self.table.put_item(Item=vpc_data)
            logger.info(f"Successfully saved VPC metadata: {vpc_data['vpc_id']}")
            return vpc_data

        except ClientError as e:
            logger.error(f"Error saving VPC to DynamoDB: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error saving VPC: {str(e)}")
            raise

    def get_vpc(self, vpc_id: str) -> Optional[Dict]:
        try:
            logger.info(f"Retrieving VPC metadata: {vpc_id}")
            response = self.table.get_item(Key={'vpc_id': vpc_id})

            if 'Item' in response:
                logger.info(f"Found VPC metadata: {vpc_id}")
                return response['Item']
            else:
                logger.info(f"VPC not found in metadata store: {vpc_id}")
                return None

        except ClientError as e:
            logger.error(f"Error retrieving VPC from DynamoDB: {str(e)}")
            raise

    def list_vpcs(self, limit: int = 100) -> List[Dict]:
        try:
            logger.info("Listing all VPCs from metadata store")
            response = self.table.scan(Limit=limit)
            vpcs = response.get('Items', [])
            vpcs.sort(key=lambda x: x.get('created_at', ''), reverse=True)
            logger.info(f"Retrieved {len(vpcs)} VPCs from metadata store")
            return vpcs

        except ClientError as e:
            logger.error(f"Error listing VPCs from DynamoDB: {str(e)}")
            raise

    def delete_vpc(self, vpc_id: str) -> bool:
        try:
            logger.info(f"Deleting VPC metadata: {vpc_id}")

            existing = self.get_vpc(vpc_id)
            if not existing:
                logger.info(f"VPC not found in metadata store: {vpc_id}")
                return False

            self.table.delete_item(Key={'vpc_id': vpc_id})

            logger.info(f"Successfully deleted VPC metadata: {vpc_id}")
            return True

        except ClientError as e:
            logger.error(f"Error deleting VPC from DynamoDB: {str(e)}")
            raise

    def update_vpc_status(self, vpc_id: str, status: str) -> bool:
        try:
            logger.info(f"Updating VPC status: {vpc_id} -> {status}")

            response = self.table.update_item(
                Key={'vpc_id': vpc_id},
                UpdateExpression='SET #status = :status',
                ExpressionAttributeNames={'#status': 'status'},
                ExpressionAttributeValues={':status': status},
                ReturnValues='UPDATED_NEW'
            )

            logger.info(f"Successfully updated VPC status: {vpc_id}")
            return True

        except ClientError as e:
            if e.response['Error']['Code'] == 'ConditionalCheckFailedException':
                logger.info(f"VPC not found for status update: {vpc_id}")
                return False
            logger.error(f"Error updating VPC status in DynamoDB: {str(e)}")
            raise
