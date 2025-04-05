from utils import get_aws_access_key, get_aws_secret_key, get_openai_key

import boto3

# Initialize a session using Amazon S3
s3 = boto3.client(
    's3',
    aws_access_key_id=get_aws_access_key(),
    aws_secret_access_key=get_aws_secret_key(),
)

# Replace with your bucket name and folder (prefix)
bucket_name = 'fakezhiyuanbucket'
folder_prefix = 'test/'  # Note the trailing slash

# List objects within the specified folder
response = s3.list_objects_v2(Bucket=bucket_name, Prefix=folder_prefix)

# Check if the response contains any objects
if 'Contents' in response:
    for obj in response['Contents']:
        print(obj['Key'])
else:
    print("No objects found in this folder.")
