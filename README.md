# AWS VPC Management API

Serverless API for automated VPC creation and management using AWS Lambda, API Gateway, and DynamoDB.

**Components:**

- **API Gateway**: REST API with API Key authentication
- **Lambda**: Python functions for VPC operations
- **DynamoDB**: Metadata storage for created VPCs
- **AWS CDK**: Infrastructure as Code deployment

**Each VPC includes:**

- 1 Public subnet with Internet Gateway
- 1 Private subnet
- Configured route tables and resource tagging

---

## Prerequisites

- AWS Account with configured credentials (`aws configure`)
- Python 3.11+
- Node.js 18+ and npm
- AWS CDK CLI: `npm install -g aws-cdk`

---

## Setup

### 1. Install Dependencies

```bash
cd cdk
pip3 install -r requirements.txt
```

### 2. Bootstrap CDK (first-time only)

```bash
cdk bootstrap
```

### 3. Deploy

```bash
cdk deploy
```

**Outputs:**

```bash
APIEndpoint = https://xxxxx.execute-api.us-east-2.amazonaws.com/prod/
APIKeyID = xxxxx
DynamoDBTableName = vpc-metadata
```

### 4. Retrieve API Key

```bash
aws apigateway get-api-key --api-key <APIKeyID> --include-value --query 'value' --output text
```

---

## API Usage

### Authentication

All requests require the `x-api-key` header:

```bash
curl -H "x-api-key: your-api-key" ...
```

### Create VPC

```bash
curl -X POST "https://your-api/vpc" \
  -H "x-api-key: your-key" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "my-vpc",
    "cidr_block": "10.0.0.0/16"
  }'
```

### List VPCs

```bash
curl -X GET "https://your-api/vpc" \
  -H "x-api-key: your-key"
```

### Get Specific VPC

```bash
curl -X GET "https://your-api/vpc/vpc-xxxxx" \
  -H "x-api-key: your-key"
```

### Delete VPC

```bash
curl -X DELETE "https://your-api/vpc/vpc-xxxxx" \
  -H "x-api-key: your-key"
```

---

## Cleanup

```bash
Delete all VPCs first:

```bash
# List VPCs
curl -X GET "https://your-api/vpc" -H "x-api-key: your-key"

# Delete each VPC
curl -X DELETE "https://your-api/vpc/vpc-xxxxx" -H "x-api-key: your-key"
```

Then destroy the stack:

```bash
cd cdk
cdk destroy
```

---

## Deployment and Testing Evidence

This section documents the complete deployment and testing process executed on **November 3, 2025** using AWS account `544483685087` in region `us-east-2`.

### 1. Environment Verification

**Check AWS credentials:**

```bash
aws sts get-caller-identity
```

**Output:**

```json
{
    "UserId": "AIDAX5ROBWLP7IGDWWSPK",
    "Account": "544483685087",
    "Arn": "arn:aws:iam::544483685087:user/llopes-allianz"
}
```

**Verify dependencies:**

```bash
python3 --version && node --version && cdk --version
```

**Output:**

```bash
Python 3.12.3
v22.21.1
2.1031.1 (build a560d1e)
```

---

### 2. Install Python Dependencies

```bash
cd cdk
pip3 install -r requirements.txt
```

**Output:** Successfully installed 14 packages including `aws-cdk-lib-2.221.1`, `constructs-10.4.2`, and dependencies.

---

### 3. CDK Bootstrap (One-Time Setup)

```bash
cd cdk
env TMPDIR=/tmp cdk bootstrap
```

**Output:**

```bash
Environment aws://544483685087/us-east-2 bootstrapped.
```

**Resources created:**

- S3 bucket: `cdk-hnb659fds-assets-544483685087-us-east-2`
- ECR repository: `cdk-hnb659fds-container-assets-544483685087-us-east-2`
- IAM roles: CloudFormationExecutionRole, DeploymentActionRole, FilePublishingRole, ImagePublishingRole, LookupRole
- SSM parameter: `/cdk-bootstrap/hnb659fds/version` (value: 29)

**Validation:**

```bash
aws cloudformation describe-stack-resources --stack-name CDKToolkit --region us-east-2
```

Confirmed: 11 resources with status `CREATE_COMPLETE`

---

### 4. Deploy CDK Stack

**Configuration:**

```bash
cd cdk
env TMPDIR=/tmp cdk deploy --require-approval never
```

**Output:**

```bash
VPCAPIStack: deploying... [1/1]
VPCAPIStack: creating CloudFormation changeset...

VPCAPIStack | 40/40 | CREATE_COMPLETE | AWS::CloudFormation::Stack | VPCAPIStack

VPCAPIStack

Outputs:
VPCAPIStack.APIEndpoint = https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/
VPCAPIStack.APIKeyID = uzo3wntl1d
VPCAPIStack.DynamoDBTableName = vpc-metadata
VPCAPIStack.Region = us-east-2
```

**Resources created:**

- 1 DynamoDB table (`vpc-metadata`)
- 1 Lambda Layer (common utilities)
- 3 Lambda functions (create, get, delete)
- 1 API Gateway REST API with 4 methods
- 1 API Key + Usage Plan
- 3 CloudWatch Log Groups
- IAM roles and policies

---

### 5. Retrieve API Key

```bash
aws apigateway get-api-key --api-key xxx --include-value --region us-east-2 --query 'value' --output text
```

**Output:**

```bash
EPxxxBU
```

**API Credentials:**

- Endpoint: `https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/`
- API Key: `EPxxxBU`

---

### 6. API Testing

#### Test 1: Create VPC

**Request:**

```bash
curl -X POST https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/vpc \
  -H "x-api-key: EPxxxBU" \
  -H "Content-Type: application/json" \
  -d '{"name": "test-vpc-1", "cidr_block": "10.0.0.0/16"}'
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vpc_id": "vpc-0485de4224ae10c4e",
        "name": "test-vpc-1",
        "cidr_block": "10.0.0.0/16",
        "region": "us-east-2",
        "subnets": [
            {
                "subnet_id": "subnet-09a89b5f23bdb1c7e",
                "cidr_block": "10.0.1.0/24",
                "availability_zone": "us-east-2a",
                "type": "public"
            },
            {
                "subnet_id": "subnet-04b98c01cc12bb100",
                "cidr_block": "10.0.2.0/24",
                "availability_zone": "us-east-2a",
                "type": "private"
            }
        ],
        "internet_gateway_id": "igw-0ce3e68b37375eb08",
        "route_tables": {
            "public": "rtb-01db1b59418ce87eb"
        },
        "status": "available",
        "created_at": "2025-11-03T14:27:32.726632Z",
        "created_by": "vpc-api"
    },
    "message": "VPC 'test-vpc-1' created successfully"
}
```

**Result:** VPC created with 1 public subnet, 1 private subnet, Internet Gateway, and route tables.

---

#### Test 2: List All VPCs

**Request:**
```bash
curl -X GET https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/vpc \
  -H "x-api-key: EPxxxBU"
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vpcs": [
            {
                "vpc_id": "vpc-0485de4224ae10c4e",
                "name": "test-vpc-1",
                "cidr_block": "10.0.0.0/16",
                "region": "us-east-2",
                "subnets": [
                    {
                        "subnet_id": "subnet-09a89b5f23bdb1c7e",
                        "cidr_block": "10.0.1.0/24",
                        "availability_zone": "us-east-2a",
                        "type": "public"
                    },
                    {
                        "subnet_id": "subnet-04b98c01cc12bb100",
                        "cidr_block": "10.0.2.0/24",
                        "availability_zone": "us-east-2a",
                        "type": "private"
                    }
                ],
                "internet_gateway_id": "igw-0ce3e68b37375eb08",
                "route_tables": {
                    "public": "rtb-01db1b59418ce87eb"
                },
                "status": "available",
                "created_at": "2025-11-03T14:27:32.726632Z",
                "created_by": "vpc-api"
            }
        ],
        "count": 1
    }
}
```

**Result:** Successfully retrieved all VPCs from DynamoDB.

---

#### Test 3: Get Specific VPC

**Request:**

```bash
curl -X GET https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/vpc/vpc-0485de4224ae10c4e \
  -H "x-api-key: EPxxxBU"
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vpc_id": "vpc-0485de4224ae10c4e",
        "name": "test-vpc-1",
        "cidr_block": "10.0.0.0/16",
        "region": "us-east-2",
        "subnets": [
            {
                "subnet_id": "subnet-09a89b5f23bdb1c7e",
                "cidr_block": "10.0.1.0/24",
                "availability_zone": "us-east-2a",
                "type": "public"
            },
            {
                "subnet_id": "subnet-04b98c01cc12bb100",
                "cidr_block": "10.0.2.0/24",
                "availability_zone": "us-east-2a",
                "type": "private"
            }
        ],
        "internet_gateway_id": "igw-0ce3e68b37375eb08",
        "route_tables": {
            "public": "rtb-01db1b59418ce87eb"
        },
        "status": "available",
        "created_at": "2025-11-03T14:27:32.726632Z",
        "created_by": "vpc-api"
    }
}
```

**Result:** Successfully retrieved specific VPC by ID.

---

#### Test 4: Delete VPC

**Request:**

```bash
curl -X DELETE https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/vpc/vpc-0485de4224ae10c4e \
  -H "x-api-key: EPxxxBU"
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vpc_id": "vpc-0485de4224ae10c4e",
        "status": "deleted",
        "deleted_at": "2025-11-03T14:30:07.096576Z"
    },
    "message": "VPC 'vpc-0485de4224ae10c4e' and all associated resources deleted successfully"
}
```

**Result:** VPC and all associated resources (subnets, IGW, route tables) deleted successfully.

---

#### Test 5: Verify Deletion

**Request:**

```bash
curl -X GET https://pycciwfbda.execute-api.us-east-2.amazonaws.com/prod/vpc \
  -H "x-api-key: EPxxxBU"
```

**Response:**

```json
{
    "success": true,
    "data": {
        "vpcs": [],
        "count": 0
    }
}
```

**Result:** Confirmed VPC deletion - no VPCs remaining in DynamoDB.

---

### 7. CloudWatch Logs Verification

**Check Lambda execution logs:**

```bash
aws logs tail /aws/lambda/vpc-api-create-vpc --region us-east-2 --since 5m --format short
```

**Sample Output:**
```
2025-11-03T14:27:32 [INFO] Received CreateVPC request
2025-11-03T14:27:32 [INFO] Creating VPC: test-vpc-1 with CIDR: 10.0.0.0/16
2025-11-03T14:27:33 [INFO] VPC created: vpc-0485de4224ae10c4e
2025-11-03T14:27:33 [INFO] Creating public subnet in us-east-2a
2025-11-03T14:27:34 [INFO] Creating private subnet in us-east-2a
2025-11-03T14:27:35 [INFO] Configuring Internet Gateway
2025-11-03T14:27:36 [INFO] VPC metadata saved to DynamoDB
```

**Result:** All operations logged correctly with 3-day retention.

---

### 8. Resource Cleanup

**Destroy CDK stack:**

```bash
cd cdk
env TMPDIR=/tmp cdk destroy --force
```

**Output:**

```bash
VPCAPIStack: destroying... [1/1]

VPCAPIStack | 36/36 | DELETE_COMPLETE | AWS::DynamoDB::Table | VPCMetadataTable

VPCAPIStack: destroyed
```

**Result:** All 40 resources successfully deleted.

**Verification:**

```bash
aws cloudformation describe-stacks --stack-name VPCAPIStack --region us-east-2
```

**Output:** Stack not found (confirmed deletion).

---

### 9. Test Summary

| Test | Endpoint |
|------|--------- |
| Create VPC | `POST /vpc` |
| List VPCs | `GET /vpc` |
| Get VPC by ID | `GET /vpc/{id}` |
| Delete VPC | `DELETE /vpc/{id}` |
| Verify Deletion | `GET /vpc` |
