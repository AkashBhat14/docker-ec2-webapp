import boto3
import logging
from botocore.exceptions import ClientError, NoCredentialsError
from typing import Optional

logger = logging.getLogger(__name__)

class S3Service:
    def __init__(self, bucket_name: str = None):
        """
        Initialize S3 service using IAM role credentials.
        No need to provide AWS credentials - they're automatically obtained from the IAM role.
        """
        try:
            # This will automatically use the IAM role attached to the EC2 instance
            self.s3_client = boto3.client('s3')
            self.bucket_name = bucket_name
            logger.info("S3 client initialized successfully using IAM role")
        except NoCredentialsError:
            logger.error("No AWS credentials found. Make sure IAM role is attached to EC2 instance.")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise

    def upload_file(self, file_content: bytes, key: str, content_type: str = "text/plain") -> bool:
        """
        Upload file content to S3.
        
        Args:
            file_content: The content to upload as bytes
            key: S3 object key (filename/path)
            content_type: MIME type of the content
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=key,
                Body=file_content,
                ContentType=content_type
            )
            logger.info(f"Successfully uploaded {key} to {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to upload {key}: {str(e)}")
            return False

    def download_file(self, key: str) -> Optional[bytes]:
        """
        Download file from S3.
        
        Args:
            key: S3 object key to download
            
        Returns:
            bytes: File content if successful, None otherwise
        """
        try:
            response = self.s3_client.get_object(Bucket=self.bucket_name, Key=key)
            content = response['Body'].read()
            logger.info(f"Successfully downloaded {key} from {self.bucket_name}")
            return content
        except ClientError as e:
            logger.error(f"Failed to download {key}: {str(e)}")
            return None

    def list_files(self, prefix: str = "") -> list:
        """
        List files in S3 bucket.
        
        Args:
            prefix: Filter objects by prefix
            
        Returns:
            list: List of object keys
        """
        try:
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix
            )
            
            if 'Contents' in response:
                files = [obj['Key'] for obj in response['Contents']]
                logger.info(f"Found {len(files)} files in {self.bucket_name}")
                return files
            else:
                logger.info(f"No files found in {self.bucket_name}")
                return []
        except ClientError as e:
            logger.error(f"Failed to list files: {str(e)}")
            return []

    def delete_file(self, key: str) -> bool:
        """
        Delete file from S3.
        
        Args:
            key: S3 object key to delete
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=key)
            logger.info(f"Successfully deleted {key} from {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Failed to delete {key}: {str(e)}")
            return False

    def check_bucket_access(self) -> bool:
        """
        Test if we can access the S3 bucket.
        
        Returns:
            bool: True if bucket is accessible, False otherwise
        """
        try:
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            logger.info(f"Successfully accessed bucket {self.bucket_name}")
            return True
        except ClientError as e:
            logger.error(f"Cannot access bucket {self.bucket_name}: {str(e)}")
            return False 