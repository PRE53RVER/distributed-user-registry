import boto3

# Initialize the DynamoDB client
dynamodb = boto3.client('dynamodb', region_name='us-east-1')

# Define the table name
table_name = 'users-table-dev'

# Define the userId of the user you want to retrieve
mob_num ="9744667890"

# Retrieve the user details
 # Replace "S" with the appropriate data type

if user_id:
    response = dynamodb.delete_item(TableName=table_name, Key={'userId': user_id})
else:
    filter_expression = "mob_num = :value"
    expression_attribute_values = {":value": {"S": mob_num}} 
    response = dynamodb.scan(TableName=table_name,
                             FilterExpression=filter_expression,
                             ExpressionAttributeValues=expression_attribute_values)
    if response['Items']:
        user_id = response['Items'][0]['user_id']
        dynamodb.delete_item(TableName=user_table, Key={'user_id': user_id})



