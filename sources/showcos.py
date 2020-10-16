#!/usr/bin/env python3
# showcos.py -- List txt files in COS
# By Tony Pearson, IBM, 2020
# requires that you do:  pip install -U ibm-cos-sdk
#
import os
import sys
import glob
import re
import ibm_boto3
from ibm_botocore.client import Config, ClientError
from ShowProgress import ShowProgress

# Constants for IBM COS values
COS_ENDPOINT_URL = os.environ['COS_ENDPOINT_URL']
COS_API_KEY_ID = os.environ['COS_API_KEY_ID']
COS_INSTANCE = os.environ['COS_INSTANCE']


def understand(extracted_text):
    relevant_words = extracted_text[:50]
    #
    # Shilpi, your code goes here
    #
    return relevant_words


def process_legislation(cos, bucket_name, key, size):
    response = cos.get_object(Bucket=bucket_name, Key=key)
    extracted_text = response['Body'].read().decode('utf-8')
    relevant_words = understand(extracted_text)    
    print(key, relevant_words)
    return None


if __name__ == "__main__":
    if len(sys.argv) == 2:
        state = sys.argv[1].upper()
        states = [state]
    else:
        states = ['AZ', 'OH']

    # Create client 
    cos = ibm_boto3.client("s3",
        ibm_api_key_id=COS_API_KEY_ID,
        ibm_service_instance_id=COS_INSTANCE,
        config=Config(signature_version="oauth"),
        endpoint_url=COS_ENDPOINT_URL
        )

    buckets = []
    response = cos.list_buckets()
    bucket_list = response['Buckets']
    for bucket in bucket_list:
        bucket_name = bucket['Name']
        buckets.append(bucket_name)
        if bucket_name.startswith('legi'):
            print('Found bucket: ', bucket_name)

    bucket_name = 'legi-info'
    cursor = ''  # Starting after key, or '' to start at beginning
    prefix = ''  # specify 'AZ' or 'OH' to limit to single state
    limit = 4000  # maximum number you want to process

    found = 0
    for n in range(5000):
        response = cos.list_objects_v2(Bucket=bucket_name,
                    StartAfter=cursor, MaxKeys=10, Prefix=prefix)
        if 'Contents' in response:
            contents = response['Contents']
            for content in contents:
                key, size = content['Key'], content['Size']
                process_legislation(cos, bucket_name, key, size)
                cursor = content['Key']
                found += 1
                if found >= limit:
                    break
        else:
            break
        if found >= limit:
            break

    print('Found {} objects'.format(found))

