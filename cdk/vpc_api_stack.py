from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_lambda as lambda_,
    aws_apigateway as apigw,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_logs as logs,
)
from constructs import Construct
import os


class VPCAPIStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        vpc_table = dynamodb.Table(
            self,
            "VPCMetadataTable",
            table_name="vpc-metadata",
            partition_key=dynamodb.Attribute(
                name="vpc_id",
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            point_in_time_recovery=False,
        )

        lambda_role = iam.Role(
            self,
            "VPCAPILambdaRole",
            assumed_by=iam.ServicePrincipal("lambda.amazonaws.com"),
            description="Execution role for VPC API Lambda functions",
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name(
                    "service-role/AWSLambdaBasicExecutionRole"
                ),
            ],
        )

        lambda_role.add_to_policy(
            iam.PolicyStatement(
                effect=iam.Effect.ALLOW,
                actions=[
                    "ec2:CreateVpc", "ec2:DeleteVpc", "ec2:DescribeVpcs", "ec2:ModifyVpcAttribute",
                    "ec2:CreateSubnet", "ec2:DeleteSubnet", "ec2:DescribeSubnets", "ec2:ModifySubnetAttribute",
                    "ec2:CreateInternetGateway", "ec2:DeleteInternetGateway",
                    "ec2:AttachInternetGateway", "ec2:DetachInternetGateway", "ec2:DescribeInternetGateways",
                    "ec2:CreateRouteTable", "ec2:DeleteRouteTable", "ec2:DescribeRouteTables",
                    "ec2:CreateRoute", "ec2:DeleteRoute",
                    "ec2:AssociateRouteTable", "ec2:DisassociateRouteTable",
                    "ec2:DescribeAvailabilityZones", "ec2:CreateTags",
                ],
                resources=["*"],
            )
        )

        vpc_table.grant_read_write_data(lambda_role)

        lambda_dir = os.path.join(os.path.dirname(__file__), "..", "app", "lambda_functions")

        common_layer = lambda_.LayerVersion(
            self,
            "CommonUtilitiesLayer",
            code=lambda_.Code.from_asset(lambda_dir),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_11],
            description="Common utilities for VPC API",
        )

        lambda_config = {
            "runtime": lambda_.Runtime.PYTHON_3_11,
            "timeout": Duration.seconds(60),
            "memory_size": 512,
            "role": lambda_role,
            "layers": [common_layer],
            "environment": {
                "VPC_TABLE_NAME": vpc_table.table_name,
                "LOG_LEVEL": "INFO",
            },
            "log_retention": logs.RetentionDays.THREE_DAYS,
        }

        create_vpc_lambda = lambda_.Function(
            self, "CreateVPCFunction",
            function_name="vpc-api-create-vpc",
            code=lambda_.Code.from_asset(lambda_dir),
            handler="create_vpc.handler",
            description="Creates VPC with subnets",
            **lambda_config,
        )

        get_vpcs_lambda = lambda_.Function(
            self, "GetVPCsFunction",
            function_name="vpc-api-get-vpcs",
            code=lambda_.Code.from_asset(lambda_dir),
            handler="get_vpcs.handler",
            description="Retrieves VPC metadata",
            **lambda_config,
        )

        delete_vpc_lambda = lambda_.Function(
            self, "DeleteVPCFunction",
            function_name="vpc-api-delete-vpc",
            code=lambda_.Code.from_asset(lambda_dir),
            handler="delete_vpc.handler",
            description="Deletes VPC and resources",
            **lambda_config,
        )

        api = apigw.RestApi(
            self, "VPCAPI",
            rest_api_name="VPC Management API",
            description="API for creating and managing VPCs",
            deploy_options=apigw.StageOptions(
                stage_name="prod",
                throttling_rate_limit=100,
                throttling_burst_limit=200,
                logging_level=apigw.MethodLoggingLevel.INFO,
                data_trace_enabled=True,
                metrics_enabled=True,
            ),
            default_cors_preflight_options=apigw.CorsOptions(
                allow_origins=apigw.Cors.ALL_ORIGINS,
                allow_methods=apigw.Cors.ALL_METHODS,
                allow_headers=["Content-Type", "X-Api-Key", "Authorization"],
            ),
        )

        api_key = api.add_api_key("VPCAPIKey", api_key_name="vpc-api-key",
                                   description="API Key for VPC Management API")

        usage_plan = api.add_usage_plan(
            "VPCAPIUsagePlan", name="vpc-api-usage-plan",
            description="Usage plan for VPC API",
            throttle=apigw.ThrottleSettings(rate_limit=100, burst_limit=200),
            quota=apigw.QuotaSettings(limit=10000, period=apigw.Period.DAY),
        )

        usage_plan.add_api_key(api_key)
        usage_plan.add_api_stage(stage=api.deployment_stage)

        vpc_resource = api.root.add_resource("vpc")

        vpc_resource.add_method(
            "POST",
            apigw.LambdaIntegration(create_vpc_lambda, proxy=True),
            api_key_required=True,
        )
        vpc_resource.add_method("GET", apigw.LambdaIntegration(get_vpcs_lambda, proxy=True),
                                 api_key_required=True)

        vpc_id_resource = vpc_resource.add_resource("{vpc_id}")
        vpc_id_resource.add_method("GET", apigw.LambdaIntegration(get_vpcs_lambda, proxy=True),
                                    api_key_required=True)
        vpc_id_resource.add_method("DELETE", apigw.LambdaIntegration(delete_vpc_lambda, proxy=True),
                                    api_key_required=True)

        CfnOutput(self, "APIEndpoint", value=api.url,
                  description="API Gateway endpoint URL", export_name="VPCAPIEndpoint")

        CfnOutput(self, "APIKeyID", value=api_key.key_id,
                  description="API Key ID", export_name="VPCAPIKeyID")

        CfnOutput(self, "DynamoDBTableName", value=vpc_table.table_name,
                  description="DynamoDB table name", export_name="VPCMetadataTableName")

        CfnOutput(self, "Region", value=self.region,
                  description="AWS Region", export_name="VPCAPIRegion")
