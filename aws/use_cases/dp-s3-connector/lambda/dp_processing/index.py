import json
import os
import boto3
import uuid
import mimetypes
from typing import List, Dict, Any
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

s3_client = boto3.client('s3')
sagemaker_client = boto3.client('sagemaker-runtime')


def process_file(bucket: str, file_key: str) -> Dict[str, Any]:
    """Process a single file using SageMaker endpoint."""
    # Download file to /tmp
    local_path = f"/tmp/{os.path.basename(file_key)}"
    s3_client.download_file(bucket, file_key, local_path)
    
    # Determine content type based on file extension
    content_type = mimetypes.guess_type(local_path)[0] or "application/octet-stream"
    
    # Create multipart form data manually
    boundary = str(uuid.uuid4())
    body = bytearray()
    
    # Add document field
    body.extend(f'--{boundary}\r\n'.encode('utf-8'))
    body.extend(f'Content-Disposition: form-data; name="document"; filename="{os.path.basename(file_key)}"\r\n'.encode('utf-8'))
    body.extend(f'Content-Type: {content_type}\r\n\r\n'.encode('utf-8'))
    
    # Add file content
    with open(local_path, 'rb') as f:
        body.extend(f.read())
    
    body.extend(b'\r\n')
    
    # Add other fields
    fields = {
        "model": "document-parse",
        "ocr": "force",
        "coordinates": "true",
        "output_formats": '["text", "html", "markdown"]',
        "base64_encoding": '["table"]',
        "chart_recognition": "true",
    }
    
    for key, value in fields.items():
        body.extend(f'--{boundary}\r\n'.encode('utf-8'))
        body.extend(f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode('utf-8'))
        body.extend(value.encode('utf-8'))
        body.extend(b'\r\n')
    
    # Add final boundary
    body.extend(f'--{boundary}--\r\n'.encode('utf-8'))
    
    try:
        # Call SageMaker endpoint
        response = sagemaker_client.invoke_endpoint(
            EndpointName=os.environ['SAGEMAKER_ENDPOINT'],
            ContentType=f'multipart/form-data; boundary={boundary}',
            Body=body
        )
        
        # Parse response
        result = json.loads(response['Body'].read().decode())
    finally:
        # Clean up
        os.remove(local_path)
    return result

def save_result(src_bucket: str, dest_bucket: str, file_key: str, result: Dict[str, Any]):
    """Save processing result to output bucket."""    
    # Save result to output bucket
    output_key = f"{os.path.splitext(os.path.basename(file_key))[0]}.json"
    s3_client.put_object(
        Bucket=dest_bucket,
        Key=output_key,
        Body=json.dumps(result)
    )
    
    # Move processed file to processed folder in input bucket
    new_key = f"processed/{os.path.basename(file_key)}"
    s3_client.copy_object(
        Bucket=src_bucket,
        CopySource={'Bucket': src_bucket, 'Key': file_key},
        Key=new_key
    )
    s3_client.delete_object(Bucket=src_bucket, Key=file_key)

def handler(event, context):
    try:
        # Get the source bucket and object key from the event
        source_bucket = event['Records'][0]['s3']['bucket']['name']
        source_key = event['Records'][0]['s3']['object']['key']
        dest_bucket = os.environ['OUTPUT_BUCKET']
        
        # Check if the file is a supported document type
        file_extension = os.path.splitext(source_key)[1].lower()
        supported_extensions = ['.pdf', '.png', '.jpeg', '.jpg']
        
        if file_extension not in supported_extensions:
            logger.info(f"Skipping unsupported file type: {source_key}")
            return {
                'statusCode': 200,
                'body': json.dumps({
                    'message': f'Skipped unsupported file type: {source_key}',
                    'file_type': file_extension
                })
            }
        
        # Process the file
        logger.info(f"Processing file: {source_bucket} {source_key}")
        result = process_file(source_bucket, source_key)
        
        # Save the result
        logger.info(f"Processing completed, save result: {dest_bucket} {source_key}")
        save_result(source_bucket, dest_bucket, source_key, result)
        
        return {
            'statusCode': 200,
            'body': json.dumps({
                'message': f'Successfully processed {source_key}',
                'result': result
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing file: {str(e)}")
        raise 