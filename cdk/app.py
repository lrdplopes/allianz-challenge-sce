#!/usr/bin/env python3

import os
import aws_cdk as cdk
from vpc_api_stack import VPCAPIStack

account = os.environ.get("CDK_DEFAULT_ACCOUNT")
region = os.environ.get("CDK_DEFAULT_REGION", "us-east-2")

app = cdk.App()

VPCAPIStack(
    app,
    "VPCAPIStack",
    description="VPC Management API - Serverless API for creating and managing AWS VPCs",
    env=cdk.Environment(account=account, region=region),
    tags={
        "Project": "VPC-API",
        "ManagedBy": "CDK",
        "Purpose": "Allianz-Senior-Cloud-Engineer",
    },
)

app.synth()
