from utils import get_aws_access_key, get_aws_secret_key
from botocore.exceptions import ClientError
import boto3

s3 = boto3.client(
    's3',
    aws_access_key_id=get_aws_access_key(),
    aws_secret_access_key=get_aws_secret_key(),
)

BUCKET_NAME = 'fakezhiyuanbucket'

def check_bucket_folder_exists(path: str):
    if not path.endswith('/'):
        path = path + '/'

    resp = s3.list_objects(Bucket=BUCKET_NAME, Prefix=path, Delimiter='/',MaxKeys=1)
    return 'Contents' in resp

def create_bucket_folder(path: str):
    if check_bucket_folder_exists(path):
        raise FileExistsError("bucket folder already exists")
    
    if not path.endswith('/'):
        path = path + '/'
    s3.put_object(Bucket=BUCKET_NAME, Key=path)

def delete_all_bucket_folders():
    confirm = input(f"Enter YES to confirm deletion of all folders in {BUCKET_NAME}: ")
    
    if not confirm == "YES":
        return
    
    s3 = boto3.resource(
        's3',
        aws_access_key_id=get_aws_access_key(),
        aws_secret_access_key=get_aws_secret_key(),
    )
    bucket = s3.Bucket(BUCKET_NAME)

    bucket.objects.all().delete()

def list_bucket_folder_files(path: str):
    if not path.endswith('/'):
        path = path + '/'

    if not check_bucket_folder_exists(path):
        create_bucket_folder(path)
    
    response = s3.list_objects_v2(Bucket=BUCKET_NAME, Prefix=path)
    files = []

    if 'Contents' in response:
        for obj in response['Contents']:
            files.append(obj['Key'])

    return files[1:]

def upload_file_to_bucket_folder(file_path, folder_path):
    # shouldn't I need to include '/'
    # this really shouldn't work but it does
    if not check_bucket_folder_exists(folder_path):
        create_bucket_folder(folder_path)

    file_name = file_path.split('/')[-1]
    s3_key = f"{folder_path}/{file_name}" if folder_path else file_name
    s3.upload_file(file_path, BUCKET_NAME, s3_key)

def download_file_from_bucket_folder(local_file_path, folder, s3_object):
    if folder and not folder.endswith('/'):
        folder = folder + '/'
    object_key = f"{folder}{s3_object}"

    try:
        # Use head_object to check if object exists (more efficient than listing)
        s3.head_object(Bucket=BUCKET_NAME, Key=object_key)
    except ClientError as e:
        if e.response['Error']['Code'] == '404':
            raise FileNotFoundError("requested s3_object does not exist")
            # return False
        raise Exception("failed to download file")

    s3.download_file(BUCKET_NAME, object_key, local_file_path)

if __name__ == "__main__":
    UUID = "1234"
    print(check_bucket_folder_exists("test"))
    print(list_bucket_folder_files(UUID))
    upload_file_to_bucket_folder("/Users/zhiyuan/Downloads/cat.jpg", UUID)
    print(list_bucket_folder_files(UUID))
    download_file_from_bucket_folder("cat.jpg", UUID, "cat.jpg")