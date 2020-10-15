#!/usr/bin/env python3
# uploadcos.py -- Upload txt files to COS
# By Tony Pearson, IBM, 2020
# requires that you do:  pip install -U ibm-cos-sdk
#
import os
import sys
import glob
import re
import ibm_boto3
from ibm_botocore.client import Config, ClientError

# Constants for IBM COS values
COS_ENDPOINT_URL = os.environ['COS_ENDPOINT_URL']
COS_API_KEY_ID = os.environ['COS_API_KEY_ID']
COS_INSTANCE = os.environ['COS_INSTANCE']


def upload_files(state, cos, bucket_name):
    globs = glob.glob(state + '*.txt')
    for filename in globs:
        cos.upload_file(filename, bucket_name, filename)
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
    print(response)
    bucket_list = response['Buckets']
    for bucket in bucket_list:
        bucket_name = bucket['Name']
        buckets.append(bucket_name)
        if bucket_name.startswith('legi'):
            print('Found bucket: ', bucket_name)

    results = []
    bucket_name = 'legi-info'
    for state in states:
        upload_files(state, cos, bucket_name)

    print(' ')
    for res in results:
        print(res)

