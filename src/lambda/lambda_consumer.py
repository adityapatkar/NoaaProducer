import json
import base64
import boto3
from decimal import Decimal

# Initialize DynamoDB client
dynamodb = boto3.resource("dynamodb")


def lambda_handler(event, context):
    """
    Lambda function handler to process the Kinesis stream
    """
    for record in event["Records"]:
        payload = base64.b64decode(record["kinesis"]["data"])
        data = json.loads(payload, parse_float=Decimal)

        # Determine the table based on the datatype
        if data["datatype"] in ["PRCP", "SNOW"]:
            table = dynamodb.Table("Precipitation")
        elif data["datatype"] in ["TOBS", "TMAX", "TMIN"]:
            table = dynamodb.Table("Temperature")
        else:
            print(f"Unknown datatype: {data['datatype']}")
            continue  # Skip unknown datatypes

        # Insert the data into the appropriate table
        try:
            table.put_item(Item=data)
            print("Successful")
        except Exception as e:
            print(f"Error inserting data: {e}")

    return f"Processed {len(event['Records'])}"
