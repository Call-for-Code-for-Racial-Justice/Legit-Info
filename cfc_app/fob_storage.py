#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
File/Object Storage -- Use FILE or OBJECT storage to hold legislation

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""
# System imports
import logging
import os
import re
import sys
import glob

# Django and other third-party imports
import ibm_boto3
from ibm_botocore.client import Config, ClientError

# import pdb; pdb.set_trace()
logger = logging.getLogger(__name__)

MAXLIMIT = 1000
TESTLIMIT = 10

TEST_LIMIT = 10
SAMPLE_BIN = b'How quickly daft jumping zebras vex'
SAMPLE_TEXT = "The quick brown fox jumps over a lazy dog"
UNICODE_TEXT = "ā <- abreve, ć <- c acute, ũ <- u tilde"

BN_REGEX = re.compile("([A-Z]*)([0-9]*)")


class FobStorage():
    """
    Support both Local File and Remote Object Storage
    """

    def __init__(self, mode, filesys=None, bucket=None):
        self.mode = mode  # 'FILE' or 'OBJECT'

        self.cos = None
        self.cos_endpoint_url = None
        self.cos_api_key = None
        self.cos_instance = None
        self.cos_bucket = None

        self.filesys = None

        if mode == 'FILE':
            self.setup_filesys(filesys)
        elif mode == 'OBJECT':
            self.setup_cos(bucket)
        return None

    def setup_cos(self, bucket=None):
        """ Setup variables needed to access IBM Cloud Object Storage """

        # Connect to IBM Cloud Object Storage service
        self.cos_endpoint_url = os.environ['COS_ENDPOINT_URL']
        self.cos_api_key = os.environ['COS_API_KEY_ID']
        self.cos_instance = os.environ['COS_INSTANCE']

        if bucket:
            self.cos_bucket = bucket
        else:
            self.cos_bucket = 'legi-info'

        self.cos = ibm_boto3.client("s3",
                                    ibm_api_key_id=self.cos_api_key,
                                    ibm_service_instance_id=self.cos_instance,
                                    config=Config(signature_version="oauth"),
                                    endpoint_url=self.cos_endpoint_url)

        # Get a list of buckets and verify the bucket we need exists
        response = self.cos.list_buckets()
        bucket_list = response['Buckets']
        bucket_found = False
        for buck in bucket_list:
            bucket_name = buck['Name']
            if bucket_name == self.cos_bucket:
                bucket_found = True

        # If we do not find the bucket, we can attempt to create it.
        # Otherwise, we disable COS access here
        if not bucket_found:
            logger.debug(f"COS Bucket not found {self.cos_bucket}")
            try:
                self.cos.create_bucket(Bucket=self.cos_bucket)
            except ClientError as exc:
                logger.error(f"CLIENT ERROR: {exc}")
                self.cos = None
            except Exception as exc2:
                logger.error(f"Unable to create bucket: {exc2}")
                self.cos = None

        return self

    def setup_filesys(self, filesys=None):
        """ Setup variables to access local or shared file system """

        if filesys:
            self.filesys = filesys
        else:
            self.filesys = os.environ['FOB_STORAGE']

        os.makedirs(self.filesys, exist_ok=True)
        return self

    def upload_binary(self, bindata, item_name):
        """ Upload binary file """
        fob_mode = self.mode

        if self.cos and fob_mode == 'OBJECT':
            self.cos.put_object(Key=item_name, Body=bindata,
                                Bucket=self.cos_bucket)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, item_name)
            with open(fullname, 'wb') as outfile:
                outfile.write(bindata)

        return self

    def upload_text(self, textdata, item_name, codec='UTF-8'):
        """ Upload text file """
        bindata = textdata.encode(codec)
        self.upload_binary(bindata, item_name)
        return self

    def item_exists(self, item_name):
        """ Check if item exists """

        items = self.list_items(prefix=item_name, limit=1)
        found = False
        if items:
            if items[0] == item_name:
                found = True
        return found

    def list_items(self, prefix=None, suffix=None,
                   after=None, limit=MAXLIMIT):
        """ list items that match prefix/suffix """
        fob_mode = self.mode

        items = []

        if self.cos and fob_mode == 'OBJECT':
            items = self.list_items_object(prefix, suffix, after, limit)

        if self.filesys and fob_mode == 'FILE':
            items = self.list_items_file(prefix, suffix, after, limit)

        return items

    def list_items_file(self, prefix, suffix, after, limit):
        """ List items from FILE storage """

        items = []
        mask = "*"
        if prefix:
            mask = prefix + mask
        if suffix:
            mask = mask + suffix
        pattern = os.path.join(self.filesys, mask)
        globs = glob.glob(pattern)
        files = []
        num = 0
        for filename in globs:
            basename = os.path.basename(filename)
            files.append(basename)
        files.sort()

        for basename in files:
            if after:
                if basename <= after:
                    continue
            items.append(basename)
            num += 1
            if limit > 0 and num >= limit:
                break
        return items

    def list_items_object(self, prefix, suffix, after, limit):
        """ List items from OBJECT storage """

        items = []
        found = 0
        cursor = ''
        if after:
            cursor = after

        objlimit = MAXLIMIT
        if (limit > 0) and (suffix is None):
            objlimit = min(objlimit, limit)

        for _ in range(999):   # Avoid run-away tasks
            if prefix:
                response = self.cos.list_objects_v2(
                    Bucket=self.cos_bucket,
                    StartAfter=cursor, Prefix=prefix,
                    MaxKeys=objlimit)

            else:
                response = self.cos.list_objects_v2(
                    Bucket=self.cos_bucket,
                    StartAfter=cursor, MaxKeys=objlimit)

            if 'Contents' in response:
                contents = response['Contents']
                for content in contents:
                    item_name = content['Key']
                    cursor = item_name
                    if suffix and not item_name.endswith(suffix):
                        continue
                    found += 1
                    items.append(item_name)
                    if (limit > 0) and (found >= limit):
                        break
            else:
                break
            if limit > 0 and found >= limit:
                break

        return items

    def download_binary(self, item_name):
        """ Upload binary file """

        fob_mode = self.mode

        bindata = b''
        try:
            if self.cos and fob_mode == 'OBJECT':
                infile = self.cos.get_object(
                    Key=item_name, Bucket=self.cos_bucket)
                bindata = infile["Body"].read()
        except Exception as exc:
            logger.error(f"307:Exception {exc}")

        if self.filesys and fob_mode == 'FILE':
            logger.debug("242:PATH [{self.filesys}] [{item_name}]")
            fullname = os.path.join(self.filesys, item_name)
            try:
                with open(fullname, 'rb') as infile:
                    bindata = infile.read()
            except Exception as exc:
                logger.error(f"315:Exception {exc}")

        return bindata

    def download_text(self, item_name, codec='UTF-8'):
        """ Upload text file """
        bindata = self.download_binary(item_name)
        textdata = bindata.decode(codec, errors='ignore')
        return textdata

    def remove_item(self, item_name):
        """ Remove file or object """
        fob_mode = self.mode

        if self.cos and fob_mode == 'OBJECT':
            self.cos.delete_object(Bucket=self.cos_bucket, Key=item_name)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, item_name)
            if os.path.exists(fullname):
                os.remove(fullname)
        return self

#################################################
#  Test functions
#################################################


def test_with_empty():
    """ Test with empty FOB """

    fob.upload_binary(SAMPLE_BIN, 'AAA-TEST.bin')
    fob.upload_text(SAMPLE_TEXT, 'AAA-TEST.txt')
    fob.upload_binary(SAMPLE_BIN, 'BBB-TEST.bin')
    fob.upload_text(UNICODE_TEXT, 'BBB-TEST.txt')
    fob.upload_binary(SAMPLE_BIN, 'CCC-TEST.bin')
    fob.upload_text(SAMPLE_TEXT, 'CCC-TEST.txt')


def test_list():
    """ Test list functions """

    print('List all items:')
    print(fob.list_items(limit=0))

    print('Limit=3:')
    print(fob.list_items(limit=3))

    print("Prefix='BBB':")
    print(fob.list_items(prefix='BBB', limit=TESTLIMIT))

    print("Suffix='.bin':")
    print(fob.list_items(suffix='.bin', limit=TESTLIMIT))

    print("Prefix='B' and Suffix='.bin': ")
    print(fob.list_items(prefix='B', suffix='.bin', limit=TESTLIMIT))

    # import pdb; pdb.set_trace()
    print("After='AAA-TEST.txt' ")
    print(fob.list_items(after='AAA-TEST.txt', limit=TESTLIMIT))

    print("After='AAA-TEST.txt' Limit=3 ")
    print(fob.list_items(after='AAB-TEST.txt', limit=3))

def test_download():
    """ Test downloads """

    print('Download binary:')
    bin_test = fob.download_binary('AAA-TEST.bin')
    print(bin_test)
    if bin_test != SAMPLE_BIN:
        print('Error, binary data does not match')

    print('Download text:')
    # import pdb; pdb.set_trace()
    text_data = fob.download_text('BBB-TEST.txt')
    print('=['+text_data+']=')
    if text_data != UNICODE_TEXT:
        print('Error, text data does not match')

    text_data = fob.download_text('CCC-TEST.txt')
    print('=['+text_data+']=')
    if text_data != SAMPLE_TEXT:
        print('Error, text data does not match')


def test_exists_removal():
    """ Test for item_exists and remove_item methods """

    print('Test if BBB-TEST.txt exists')
    if fob.item_exists('BBB-TEST.txt'):
        print('--- BBB-TEST.txt exists!')
    else:
        print('Not found: BBB-TEST.txt')

    print('Delete existing file BBB-TEST.txt:')
    fob.remove_item('BBB-TEST.txt')
    print(fob.list_items(limit=TESTLIMIT))

    print('Delete non-existient file ZZZ-TEST.unk:')
    fob.remove_item('ZZZ-TEST.unk')
    print(fob.list_items(limit=TESTLIMIT))

    # Cleanup directory space
    fob.remove_item('AAA-TEST.bin')
    fob.remove_item('AAA-TEST.txt')
    fob.remove_item('BBB-TEST.bin')
    fob.remove_item('BBB-TEST.txt')
    fob.remove_item('CCC-TEST.bin')
    fob.remove_item('CCC-TEST.txt')
    return None


if __name__ == "__main__":

    if len(sys.argv) == 2:
        MODE = sys.argv[1]
    else:
        MODE = 'FILE'

    if MODE not in ['FILE', 'OBJECT']:
        print('Usage: ')
        print('  ', sys.argv[0])
        print('  ', sys.argv[0], 'OPTION    Specify FILE or OBJECT')
        sys.exit(4)

    print('Testing: ', sys.argv[0], MODE)

    # Test with empty structure first
    fob = FobStorage(MODE, filesys='/tmp/FOB-TEST', bucket='fob-test')
    fob.test_with_empty()

    # test_with_live copy
    fob = FobStorage(MODE)
    item_list = fob.list_items(limit=0)
    print(len(item_list))

    state, bill_number, session_id, doc_year = "AZ", "HB1", "1234", "2016"
    print(fob.bill_text_key(state, bill_number, session_id, doc_year))

    state, bill_number, session_id, doc_year = "AZ", "SB22", "1234", "2017"
    print(fob.bill_text_key(state, bill_number, session_id, doc_year))

    state, bill_number, session_id, doc_year = "AZ", "HRJ333", "1234", "2018"
    print(fob.bill_text_key(state, bill_number, session_id, doc_year))

    state, bill_number, session_id, doc_year = "AZ", "SRC4444", "1234", "2019"
    print(fob.bill_text_key(state, bill_number, session_id, doc_year))

    print('Congratulations')
