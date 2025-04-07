import json
import base64
import os
import cgi
from io import BytesIO
import boto3
import uuid
from typing import Dict, Tuple, Any


def create_multipart_form_data(fields: Dict[str, Any]) -> Tuple[bytes, str]:
    """
    Creates a multipart/form-data request body from a dictionary of fields.

    Args:
        fields: Dictionary containing form fields. Each value can be either a string
               or a dictionary with 'filename' and 'content' for file uploads.

    Returns:
        Tuple containing:
        - The encoded multipart/form-data body as bytes
        - The content type string with boundary
    """
    boundary = str(uuid.uuid4())
    body = BytesIO()

    for key, value in fields.items():
        # Add boundary for each field
        body.write(f"--{boundary}\r\n".encode("utf-8"))

        if isinstance(value, dict) and "filename" in value:
            # Handle file upload fields
            body.write(
                f'Content-Disposition: form-data; name="{key}"; filename="{value["filename"]}"\r\n'.encode(
                    "utf-8"
                )
            )
            body.write(b"Content-Type: application/octet-stream\r\n\r\n")
            body.write(value["content"])
        else:
            # Handle regular form fields
            body.write(
                f'Content-Disposition: form-data; name="{key}"\r\n\r\n'.encode("utf-8")
            )
            body.write(str(value).encode("utf-8"))
        body.write(b"\r\n")

    # Add closing boundary
    body.write(f"--{boundary}--\r\n".encode("utf-8"))

    return body.getvalue(), f"multipart/form-data; boundary={boundary}"


def parse_multipart_data(event: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parses multipart/form-data from an API Gateway event.

    Args:
        event: API Gateway event dictionary containing the request data

    Returns:
        Dictionary containing parsed form fields and files
    """
    # Handle base64 encoded bodies from API Gateway
    body = (
        base64.b64decode(event["body"])
        if event.get("isBase64Encoded", False)
        else event["body"].encode() if isinstance(event["body"], str) else event["body"]
    )

    # Get content type with boundary from headers
    content_type = event["headers"].get(
        "content-type", event["headers"].get("Content-Type", "")
    )

    # Parse the multipart form data using cgi.FieldStorage
    fp = BytesIO(body)
    environ = {"REQUEST_METHOD": "POST"}
    headers = {"content-type": content_type, "content-length": str(len(body))}
    parsed = cgi.FieldStorage(fp=fp, environ=environ, headers=headers)

    # Extract all fields and files
    result = {}
    for key in parsed.keys():
        item = parsed[key]
        if item.filename:
            result[key] = {"filename": item.filename, "content": item.file.read()}
        else:
            result[key] = item.value

    return result


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    Lambda handler for processing API Gateway requests and forwarding to SageMaker endpoint.

    Supports both multipart/form-data and JSON requests.

    Args:
        event: API Gateway event
        context: Lambda context

    Returns:
        API Gateway response object
    """
    try:
        # Initialize SageMaker runtime client
        runtime = boto3.client("runtime.sagemaker")
        endpoint_name = os.environ["SAGEMAKER_ENDPOINT_NAME"]

        # Get content type from request headers
        headers = event.get("headers", {})
        content_type = next(
            (headers[k] for k in headers if k.lower() == "content-type"),
            "application/json",
        )

        # Process request based on content type
        if "multipart/form-data" in content_type:
            parsed_data = parse_multipart_data(event)
            body, content_type = create_multipart_form_data(parsed_data)
        else:
            # Handle JSON requests
            body = event.get("body", "")
            if event.get("isBase64Encoded", False):
                body = base64.b64decode(body)
            if isinstance(body, bytes):
                body = body.decode("utf-8")
            body = json.dumps(json.loads(body) if isinstance(body, str) else body)
            content_type = "application/json"

        # Invoke SageMaker endpoint
        response = runtime.invoke_endpoint(
            EndpointName=endpoint_name,
            ContentType=content_type,
            Body=body,
        )

        # Return successful response
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": response["Body"].read().decode("utf-8"),
            "isBase64Encoded": False,
        }

    except Exception as e:
        # Return error response
        return {
            "statusCode": 500,
            "headers": {
                "Content-Type": "application/json",
                "Access-Control-Allow-Origin": "*",
            },
            "body": json.dumps({"error": str(e)}),
        }
