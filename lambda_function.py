import os
import io
import urllib.parse
import boto3
from PIL import Image

s3_client = boto3.client('s3')

# Define target maximum dimensions for resized images
MAX_SIZE = (800, 800)

def lambda_handler(event, context):
    for record in event['Records']:
        bucket_name = record['s3']['bucket']['name']
        object_key = urllib.parse.unquote_plus(record['s3']['object']['key'], encoding='utf-8')
        
        # Prevent infinite loops: process only images uploaded in 'original-images/'
        if not object_key.startswith('original-images/'):
            print(f"Skipping key {object_key} - Not in 'original-images/' folder.")
            continue
            
        file_name = os.path.basename(object_key)
        if not file_name:
            continue
            
        # Target path inside 'resized-images/' folder
        resized_object_key = f"resized-images/{file_name}"
        
        try:
            # 1. Download image from S3 into memory
            response = s3_client.get_object(Bucket=bucket_name, Key=object_key)
            image_content = response['Body'].read()
            
            # 2. Open and resize image using Pillow
            with Image.open(io.BytesIO(image_content)) as image:
                image.thumbnail(MAX_SIZE, Image.Resampling.LANCZOS)
                
                # Save resized image into memory buffer
                buffer = io.BytesIO()
                image_format = image.format if image.format else 'JPEG'
                image.save(buffer, format=image_format)
                buffer.seek(0)
                
                content_type = response.get('ContentType', 'image/jpeg')
                
            # 3. Upload resized image to 'resized-images/' folder
            s3_client.put_object(
                Bucket=bucket_name,
                Key=resized_object_key,
                Body=buffer,
                ContentType=content_type
            )
            
            print(f"Successfully resized {object_key} and saved to {resized_object_key}")
            
        except Exception as e:
            print(f"Error processing object {object_key} from bucket {bucket_name}: {str(e)}")
            raise e
