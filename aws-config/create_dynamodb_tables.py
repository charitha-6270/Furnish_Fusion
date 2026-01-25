"""
Create DynamoDB Tables for Furnish Fusion
Run this script to create all required DynamoDB tables in us-east-1
"""

import boto3
from botocore.exceptions import ClientError

# Region
REGION = 'us-east-1'
dynamodb = boto3.client('dynamodb', region_name=REGION)

# Table definitions
TABLES = [
    {
        'TableName': 'FF_Users',
        'KeySchema': [
            {'AttributeName': 'user_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'user_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'FF_Products',
        'KeySchema': [
            {'AttributeName': 'product_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'product_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'FF_Cart',
        'KeySchema': [
            {'AttributeName': 'cart_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'cart_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'FF_Orders',
        'KeySchema': [
            {'AttributeName': 'order_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'order_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    },
    {
        'TableName': 'FF_Order_Items',
        'KeySchema': [
            {'AttributeName': 'order_item_id', 'KeyType': 'HASH'}
        ],
        'AttributeDefinitions': [
            {'AttributeName': 'order_item_id', 'AttributeType': 'S'}
        ],
        'BillingMode': 'PAY_PER_REQUEST'
    }
]

def create_table(table_def):
    """Create a DynamoDB table"""
    table_name = table_def['TableName']
    
    try:
        print(f"Creating table: {table_name}...")
        response = dynamodb.create_table(**table_def)
        print(f"✅ Table {table_name} created successfully!")
        print(f"   Status: {response['TableDescription']['TableStatus']}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'ResourceInUseException':
            print(f"⚠️  Table {table_name} already exists. Skipping...")
            return True
        else:
            print(f"❌ Error creating table {table_name}: {e}")
            return False

def main():
    """Create all tables"""
    print("=" * 60)
    print("Furnish Fusion - DynamoDB Table Creation")
    print("Region: us-east-1")
    print("=" * 60)
    print()
    
    success_count = 0
    for table_def in TABLES:
        if create_table(table_def):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Summary: {success_count}/{len(TABLES)} tables created/verified")
    print("=" * 60)
    
    if success_count == len(TABLES):
        print("\n🎉 All tables are ready!")
        print("\nNext steps:")
        print("1. Create SNS topic: aws sns create-topic --name furnish-fusion-orders --region us-east-1")
        print("2. Set up EC2 instance with IAM role")
        print("3. Deploy application")
    else:
        print("\n⚠️  Some tables failed to create. Please check the errors above.")

if __name__ == "__main__":
    main()

