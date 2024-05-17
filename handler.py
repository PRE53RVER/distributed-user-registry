import json
import uuid
import re
import boto3
from datetime import datetime
from http import HTTPStatus
from boto3.dynamodb.conditions import Key

dynamodb = boto3.client('dynamodb', region_name='us-east-1')
user_table = 'users-table-dev'

def is_valid_mobile_number(mob_num):
    """Validate the mobile number."""
    if len(mob_num) == 10 and mob_num.isdigit():
        return True
    return False

def is_valid_pan_number(pan_num):
    """Validate the PAN number."""
    pattern = r'^[A-Z]{5}\d{4}[A-Z]$'
    return bool(re.fullmatch(pattern, pan_num))

def create_user(event, context):
    """Create a new user."""
    
    try:
        
        body = json.loads(event.get('body'))
        

        full_name = body.get('full_name', '').strip()
        if not full_name:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Full name is required."
                })
            }

        mob_num = body.get('mob_num', '').strip()
        mob_num = re.sub(r'^0|^\+91', '', mob_num)
        if not is_valid_mobile_number(mob_num):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Invalid mobile number."
                })
            }
        
        pan_num = body.get('pan_num', '').strip().upper()
        if not is_valid_pan_number(pan_num):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Invalid PAN number."
                })
            }

        manager_id = body.get('manager_id')
        user_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()
        
        item = {
            'userId':{'S': user_id},
            'full_name': {'S':full_name},
            'mob_num': {'S':mob_num},
            'pan_num': {'S':pan_num},
            'manager_id': {'S':manager_id},
            'created_at': {'S':created_at},
            'is_active': {'N': '1'}
        }
        print("first check")
        response = dynamodb.put_item(TableName=user_table,Item=item)
        print("second check")
        if response['ResponseMetadata']['HTTPStatusCode'] == 200:
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({
                    "status": "Success",
                    "message": f'User created successfully with ID: {user_id}'
                })
        }

    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while creating the user."
            })
        }
# /get_users
def get_users(event, context):
    try:
        if event.get('body'):
            data = json.loads(event.get('body'))
            print(data)
            if 'user_id' in data:
                filter_expression = "userId = :value"
                expression_attribute_values = {":value": {"S": data['user_id']}}
            elif 'mob_num' in data:
                filter_expression = "mob_num = :value"
                expression_attribute_values = {":value": {"S": data['mob_num']}}
            elif 'manager_id' in data:
                filter_expression = "manager_id = :value"
                expression_attribute_values = {":value": {"S": data['manager_id']}}


        response = dynamodb.scan(
            TableName=user_table,
            FilterExpression=filter_expression,
            ExpressionAttributeValues=expression_attribute_values
        )
        # Process the scan results
        if 'Items' in response:
            users = response['Items']
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({"users": users})
            }
        else:
            users = []
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({"users": []})
            }

    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while retrieving users."
            })
        }

# /delete_user
def delete_user(event, context):
    """Delete a user based on user_id or mob_num."""
    try:
        body = json.loads(event.get('body'))
        user_id = body.get('user_id')
        mob_num = body.get('mob_num')

        if not user_id and not mob_num:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Either user_id or mob_num is required."
                })
            }


        if user_id:
            response = dynamodb.delete_item(TableName=user_table, Key={'userId': user_id})
            return {
                'statusCode': HTTPStatus.OK,
                'body': json.dumps({"status": "Success", "message": "User deleted successfully."})
            }  
        else:
            filter_expression = "mob_num = :value"
            expression_attribute_values = {":value": {"S": mob_num}} 
            response = dynamodb.scan(TableName=user_table,
                                    FilterExpression=filter_expression,
                                    ExpressionAttributeValues=expression_attribute_values)
            if response['Items']:
                user_id = response['Items'][0]['user_id']
                dynamodb.delete_item(TableName=user_table, Key={'user_id': {"S":user_id}})
                return {
                    'statusCode': HTTPStatus.OK,
                    'body': json.dumps({"status": "Success", "message": "User deleted successfully."})
                }  
            else:
                return {
                    'statusCode': HTTPStatus.NOT_FOUND,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "User not found."
                    })
                }

     

    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while deleting the user."
            })
        }

def update_user(event, context):
    """Update users based on user_ids and update_data."""
    try:
        body = json.loads(event.get('body'))
        user_ids = body.get('user_ids')
        update_data = body.get('update_data')

        if not user_ids or not update_data:
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "Both user_ids and update_data are required."
                })
            }

        if len(user_ids) != len(update_data):
            return {
                'statusCode': HTTPStatus.BAD_REQUEST,
                'body': json.dumps({
                    "status": "Failed",
                    "error": "The number of user_ids and update_data items should be the same."
                })
            }

        for user_id in user_ids:
            user_update_data = update_data.get(user_id)

            if not user_update_data:
                continue

            full_name = user_update_data.get('full_name', '').strip()
            mob_num = user_update_data.get('mob_num', '').strip()
            mob_num = re.sub(r'^0|^\+91', '', mob_num)
            pan_num = user_update_data.get('pan_num', '').strip().upper()
            manager_id = user_update_data.get('manager_id')
            is_active = user_update_data.get('is_active')

            if mob_num and not is_valid_mobile_number(mob_num):
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Invalid mobile number."
                    })
                }

            if pan_num and not is_valid_pan_number(pan_num):
                return {
                    'statusCode': HTTPStatus.BAD_REQUEST,
                    'body': json.dumps({
                        "status": "Failed",
                        "error": "Invalid PAN number."
                        })
                        }
            update_expression = 'SET '
            expression_attribute_names = {}
            expression_attribute_values = {}

            if full_name:
                update_expression += '#fn = :fn, '
                expression_attribute_names['#fn'] = 'full_name'
                expression_attribute_values[':fn'] = full_name

            if mob_num:
                update_expression += '#mn = :mn, '
                expression_attribute_names['#mn'] = 'mob_num'
                expression_attribute_values[':mn'] = mob_num

            if pan_num:
                update_expression += '#pn = :pn, '
                expression_attribute_names['#pn'] = 'pan_num'
                expression_attribute_values[':pn'] = pan_num

            if manager_id is not None:
                update_expression += '#mid = :mid, '
                expression_attribute_names['#mid'] = 'manager_id'
                expression_attribute_values[':mid'] = manager_id

            if is_active is not None:
                update_expression += '#ia = :ia, '
                expression_attribute_names['#ia'] = 'is_active'
                expression_attribute_values[':ia'] = is_active

            update_expression = update_expression.rstrip(', ')

            user_table.update_item(
                Key={'user_id': user_id},
                UpdateExpression=update_expression,
                ExpressionAttributeNames=expression_attribute_names,
                ExpressionAttributeValues=expression_attribute_values
            )

        return {
            'statusCode': HTTPStatus.OK,
            'body': json.dumps({
                "status": "Success",
                "message": "Users updated successfully."
            })
        }

    except Exception as e:
        print(f'Error: {e}')
        return {
            'statusCode': HTTPStatus.INTERNAL_SERVER_ERROR,
            'body': json.dumps({
                "status": "Failed",
                "error": "An error occurred while updating users."
            })
        }


