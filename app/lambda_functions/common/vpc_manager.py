"""VPC Manager - Core logic for creating and managing VPCs using boto3"""

import logging
from datetime import datetime
from typing import Dict, List, Optional
import boto3
from botocore.exceptions import ClientError

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class VPCManager:
    def __init__(self, region: str = 'us-east-2'):
        self.ec2_client = boto3.client('ec2', region_name=region)
        self.ec2_resource = boto3.resource('ec2', region_name=region)
        self.region = region

    def create_vpc(self, name: str, cidr_block: str = '10.0.0.0/16',
                   request_id: Optional[str] = None) -> Dict:
        """Create VPC with 1 public and 1 private subnet"""
        logger.info(f"Creating VPC: {name} with CIDR: {cidr_block}")

        try:
            self._validate_cidr(cidr_block)

            vpc_response = self.ec2_client.create_vpc(
                CidrBlock=cidr_block,
                TagSpecifications=[{
                    'ResourceType': 'vpc',
                    'Tags': self._get_tags(name, 'vpc', request_id)
                }]
            )
            vpc_id = vpc_response['Vpc']['VpcId']
            logger.info(f"Created VPC: {vpc_id}")

            self.ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsHostnames={'Value': True})
            self.ec2_client.modify_vpc_attribute(VpcId=vpc_id, EnableDnsSupport={'Value': True})

            azs = self._get_availability_zones()
            primary_az = azs[0] if azs else None

            public_subnet = self._create_subnet(
                vpc_id=vpc_id,
                cidr_block=self._calculate_subnet_cidr(cidr_block, 1),
                availability_zone=primary_az,
                name=f"{name}-public-subnet",
                subnet_type='public',
                request_id=request_id
            )

            private_subnet = self._create_subnet(
                vpc_id=vpc_id,
                cidr_block=self._calculate_subnet_cidr(cidr_block, 2),
                availability_zone=primary_az,
                name=f"{name}-private-subnet",
                subnet_type='private',
                request_id=request_id
            )

            igw_id = self._create_internet_gateway(vpc_id, name, request_id)

            public_route_table_id = self._configure_public_routing(
                vpc_id=vpc_id,
                igw_id=igw_id,
                subnet_id=public_subnet['subnet_id'],
                name=name,
                request_id=request_id
            )

            vpc_details = {
                'vpc_id': vpc_id,
                'name': name,
                'cidr_block': cidr_block,
                'region': self.region,
                'subnets': [public_subnet, private_subnet],
                'internet_gateway_id': igw_id,
                'route_tables': {'public': public_route_table_id},
                'status': 'available',
                'created_at': datetime.utcnow().isoformat() + 'Z',
                'created_by': 'vpc-api'
            }

            logger.info(f"Successfully created VPC {vpc_id}")
            return vpc_details

        except ClientError as e:
            logger.error(f"AWS API error creating VPC: {str(e)}")
            if 'vpc_id' in locals():
                self._cleanup_failed_vpc(vpc_id)
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating VPC: {str(e)}")
            raise

    def delete_vpc(self, vpc_id: str) -> Dict:
        """Delete VPC and all associated resources"""
        logger.info(f"Deleting VPC: {vpc_id}")

        try:
            vpc = self.ec2_resource.Vpc(vpc_id)

            for subnet in vpc.subnets.all():
                logger.info(f"Deleting subnet: {subnet.id}")
                subnet.delete()

            for route_table in vpc.route_tables.all():
                if not self._is_main_route_table(route_table):
                    logger.info(f"Deleting route table: {route_table.id}")
                    route_table.delete()

            for igw in vpc.internet_gateways.all():
                logger.info(f"Detaching and deleting IGW: {igw.id}")
                vpc.detach_internet_gateway(InternetGatewayId=igw.id)
                igw.delete()

            vpc.delete()
            logger.info(f"Successfully deleted VPC: {vpc_id}")

            return {
                'vpc_id': vpc_id,
                'status': 'deleted',
                'deleted_at': datetime.utcnow().isoformat() + 'Z'
            }

        except ClientError as e:
            logger.error(f"Error deleting VPC {vpc_id}: {str(e)}")
            raise

    def describe_vpc(self, vpc_id: str) -> Optional[Dict]:
        """Get VPC details by ID"""
        try:
            response = self.ec2_client.describe_vpcs(VpcIds=[vpc_id])
            if response['Vpcs']:
                return response['Vpcs'][0]
            return None
        except ClientError as e:
            if e.response['Error']['Code'] == 'InvalidVpcID.NotFound':
                return None
            raise

    def _create_subnet(self, vpc_id: str, cidr_block: str, availability_zone: str,
                       name: str, subnet_type: str, request_id: Optional[str] = None) -> Dict:
        response = self.ec2_client.create_subnet(
            VpcId=vpc_id,
            CidrBlock=cidr_block,
            AvailabilityZone=availability_zone,
            TagSpecifications=[{
                'ResourceType': 'subnet',
                'Tags': self._get_tags(name, subnet_type, request_id)
            }]
        )

        subnet_id = response['Subnet']['SubnetId']

        if subnet_type == 'public':
            self.ec2_client.modify_subnet_attribute(
                SubnetId=subnet_id,
                MapPublicIpOnLaunch={'Value': True}
            )

        logger.info(f"Created {subnet_type} subnet: {subnet_id}")

        return {
            'subnet_id': subnet_id,
            'cidr_block': cidr_block,
            'availability_zone': availability_zone,
            'type': subnet_type
        }

    def _create_internet_gateway(self, vpc_id: str, name: str,
                                  request_id: Optional[str] = None) -> str:
        response = self.ec2_client.create_internet_gateway(
            TagSpecifications=[{
                'ResourceType': 'internet-gateway',
                'Tags': self._get_tags(f"{name}-igw", 'internet-gateway', request_id)
            }]
        )

        igw_id = response['InternetGateway']['InternetGatewayId']

        self.ec2_client.attach_internet_gateway(
            InternetGatewayId=igw_id,
            VpcId=vpc_id
        )

        logger.info(f"Created and attached Internet Gateway: {igw_id}")
        return igw_id

    def _configure_public_routing(self, vpc_id: str, igw_id: str, subnet_id: str,
                                   name: str, request_id: Optional[str] = None) -> str:
        response = self.ec2_client.create_route_table(
            VpcId=vpc_id,
            TagSpecifications=[{
                'ResourceType': 'route-table',
                'Tags': self._get_tags(f"{name}-public-rt", 'route-table', request_id)
            }]
        )

        route_table_id = response['RouteTable']['RouteTableId']

        self.ec2_client.create_route(
            RouteTableId=route_table_id,
            DestinationCidrBlock='0.0.0.0/0',
            GatewayId=igw_id
        )

        self.ec2_client.associate_route_table(
            RouteTableId=route_table_id,
            SubnetId=subnet_id
        )

        logger.info(f"Configured public route table: {route_table_id}")
        return route_table_id

    def _get_availability_zones(self) -> List[str]:
        response = self.ec2_client.describe_availability_zones(
            Filters=[{'Name': 'state', 'Values': ['available']}]
        )
        return [az['ZoneName'] for az in response['AvailabilityZones']]

    def _calculate_subnet_cidr(self, vpc_cidr: str, subnet_index: int) -> str:
        """Calculate subnet CIDR: 10.0.0.0/16 -> 10.0.{index}.0/24"""
        base_ip = vpc_cidr.split('/')[0]
        octets = base_ip.split('.')
        octets[2] = str(subnet_index)
        return f"{'.'.join(octets)}/24"

    def _validate_cidr(self, cidr_block: str) -> None:
        if '/' not in cidr_block:
            raise ValueError(f"Invalid CIDR block: {cidr_block}")

        ip, prefix = cidr_block.split('/')

        octets = ip.split('.')
        if len(octets) != 4:
            raise ValueError(f"Invalid IP address in CIDR: {ip}")

        try:
            prefix_int = int(prefix)
            if prefix_int < 16 or prefix_int > 28:
                raise ValueError(f"VPC CIDR prefix must be between /16 and /28, got /{prefix_int}")
        except ValueError:
            raise ValueError(f"Invalid CIDR prefix: {prefix}")

    def _get_tags(self, name: str, resource_type: str, request_id: Optional[str] = None) -> List[Dict]:
        tags = [
            {'Key': 'Name', 'Value': name},
            {'Key': 'ManagedBy', 'Value': 'vpc-api'},
            {'Key': 'ResourceType', 'Value': resource_type},
            {'Key': 'CreatedAt', 'Value': datetime.utcnow().isoformat()}
        ]
        if request_id:
            tags.append({'Key': 'RequestId', 'Value': request_id})
        return tags

    def _is_main_route_table(self, route_table) -> bool:
        for association in route_table.associations:
            if association.main:
                return True
        return False

    def _cleanup_failed_vpc(self, vpc_id: str) -> None:
        try:
            logger.warning(f"Attempting cleanup of failed VPC creation: {vpc_id}")
            self.delete_vpc(vpc_id)
        except Exception as e:
            logger.error(f"Failed to cleanup VPC {vpc_id}: {str(e)}")
