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
