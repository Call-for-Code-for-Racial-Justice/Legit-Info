#!/usr/bin/env python3
# FOB_Storage.py -- Use FILE or OBJECT storage to hold legislation
# By Tony Pearson, IBM, 2020
#
# requires:  pip install -U ibm-cos-sdk for IBM Cloud Object Storage
#
import os
import sys
import glob
import ibm_boto3
from ibm_botocore.client import Config, ClientError

MAXLIMIT = 1000
TESTLIMIT = 10


class FOB_Storage():
    """
    Support both Local File and Remote Object Storage
    """

    def __init__(self, mode, filesys=None, bucket=None):
        """ Set characters to use for showing progress"""
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
        for bucket in bucket_list:
            bucket_name = bucket['Name']
            if bucket_name == self.cos_bucket:
                bucket_found = True

        # If we do not find the bucket, we can attempt to create it.
        # Otherwise, we disable COS access here
        if not bucket_found:
            print('COS Bucket not found {}'.format(self.cos_bucket))
            try:
                self.cos.create_bucket(Bucket=self.cos_bucket)
            except ClientError as be:
                print("CLIENT ERROR: {0}\n".format(be))
                self.cos = None
            except Exception as e:
                print("Unable to create bucket: {0}".format(e))
                self.cos = None

        return self

    def setup_filesys(self, filesys=None):
        if filesys:
            self.filesys = filesys
        else:
            self.filesys = os.environ['FOB_STORAGE']

        os.makedirs(self.filesys, exist_ok=True)
        return self

    def upload_binary(self, bindata, handle, mode='DEFAULT'):
        """ Upload binary file """
        fob_mode = mode
        if fob_mode not in ['FILE', 'OBJECT']:
            fob_mode = self.mode

        if self.cos and fob_mode == 'OBJECT':
            self.cos.put_object(Key=handle, Body=bindata,
                                Bucket=self.cos_bucket)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, handle)
            with open(fullname, 'wb') as outfile:
                outfile.write(bindata)

        return self

    def upload_text(self, textdata, handle, mode='DEFAULT', codec='UTF-8'):
        """ Upload text file """
        bindata = textdata.encode(codec)
        self.upload_binary(bindata, handle, mode=mode)
        return self

    def handle_exists(self, handle, mode='DEFAULT'):
        fob_mode = mode
        if fob_mode not in ['FILE', 'OBJECT']:
            fob_mode = self.mode

        handles = self.list_handles(mode, prefix=handle, limit=1)
        found = False
        if handles:
            if handles[0] == handle:
                found = True
        return found

    def list_handles(self, mode='DEFAULT', prefix=None, suffix=None,
                     after=None, limit=MAXLIMIT):
        """ list handles that match prefix/suffix """
        fob_mode = mode
        if fob_mode not in ['FILE', 'OBJECT']:
            fob_mode = self.mode

        handles = []

        if self.cos and fob_mode == 'OBJECT':
            found = 0
            cursor = ''
            if after:
                cursor = after

            for n in range(999):   # Avoid run-away tasks
                if prefix:
                    response = self.cos.list_objects_v2(
                        Bucket=self.cos_bucket,
                        StartAfter=cursor, MaxKeys=limit,
                        Prefix=prefix)
                else:
                    response = self.cos.list_objects_v2(
                        Bucket=self.cos_bucket,
                        StartAfter=cursor, MaxKeys=limit)
                if 'Contents' in response:
                    contents = response['Contents']
                    for content in contents:
                        handle = content['Key']
                        cursor = handle
                        if suffix and not handle.endswith(suffix):
                            continue
                        found += 1
                        handles.append(handle)
                        if limit > 0 and found >= limit:
                            break
                else:
                    break
                if limit > 0 and found >= limit:
                    break

        if self.filesys and fob_mode == 'FILE':
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
                handles.append(basename)
                num += 1
                if limit > 0 and num >= limit:
                    break

        return handles

    def download_binary(self, handle, mode='DEFAULT'):
        """ Upload binary file """
        fob_mode = mode
        if fob_mode not in ['FILE', 'OBJECT']:
            fob_mode = self.mode

        bindata = b''
        try:
            if self.cos and fob_mode == 'OBJECT':
                infile = self.cos.get_object(
                    Key=handle, Bucket=self.cos_bucket)
                bindata = infile["Body"].read()
        except Exception as e:
            print(e)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, handle)
            try:
                with open(fullname, 'rb') as infile:
                    bindata = infile.read()
            except Exception as e:
                print(e)

        return bindata

    def download_text(self, handle, mode='DEFAULT', codec='UTF-8'):
        """ Upload text file """
        bindata = self.download_binary(handle, mode=mode)
        textdata = bindata.decode(codec, errors='ignore')
        return textdata

    def remove_handle(self, handle):
        """ Remove file or object """
        fob_mode = mode
        if fob_mode not in ['FILE', 'OBJECT']:
            fob_mode = self.mode

        if self.cos and fob_mode == 'OBJECT':
            self.cos.delete_object(Bucket=self.cos_bucket, Key=handle)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, handle)
            if os.path.exists(fullname):
                os.remove(fullname)
        return self


if __name__ == "__main__":

    help_required = False
    mode = 'FILE'
    if len(sys.argv) == 2:
        mode = sys.argv[1]

    if mode not in ['FILE', 'OBJECT']:
        print('Usage: ')
        print('  ', sys.argv[0])
        print('  ', sys.argv[0], 'OPTION    Specify FILE or OBJECT')
        sys.exit(4)

    print('Testing: ', sys.argv[0], mode)
    TEST_LIMIT = 10

    fob = FOB_Storage(mode, filesys='/tmp/FOB-TEST', bucket='fob-test')

    SAMPLE_BIN = b'How quickly daft jumping zebras vex'
    SAMPLE_TEXT = "The quick brown fox jumps over a lazy dog"
    UNICODE_TEXT = "ā <- abreve, ć <- c acute, ũ <- u tilde"

    fob.upload_binary(SAMPLE_BIN, 'AAA-TEST.bin')
    fob.upload_text(SAMPLE_TEXT, 'AAA-TEST.txt')
    fob.upload_binary(SAMPLE_BIN, 'BBB-TEST.bin')
    fob.upload_text(UNICODE_TEXT, 'BBB-TEST.txt')
    fob.upload_binary(SAMPLE_BIN, 'CCC-TEST.bin')
    fob.upload_text(SAMPLE_TEXT, 'CCC-TEST.txt')

    print('List all handles:')
    print(fob.list_handles(limit=TESTLIMIT))

    print('Limit=3:')
    print(fob.list_handles(limit=3))

    print("Prefix='BBB':")
    print(fob.list_handles(prefix='BBB', limit=TESTLIMIT))

    print("Suffix='.bin':")
    print(fob.list_handles(suffix='.bin', limit=TESTLIMIT))

    print("Prefix='B' and Suffix='.bin': ")
    print(fob.list_handles(prefix='B', suffix='.bin', limit=TESTLIMIT))

    # import pdb; pdb.set_trace()
    print("After='AAA-TEST.txt' ")
    print(fob.list_handles(after='AAA-TEST.txt', limit=TESTLIMIT))

    print("After='AAA-TEST.txt' Limit=3 ")
    print(fob.list_handles(after='AAB-TEST.txt', limit=3))

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

    print('Test if BBB-TEST.txt exists')
    if fob.handle_exists('BBB-TEST.txt'):
        print('--- BBB-TEST.txt exists!')
    else:
        print('Not found: BBB-TEST.txt')

    print('Delete existing file BBB-TEST.txt:')
    fob.remove_handle('BBB-TEST.txt')
    print(fob.list_handles(limit=TESTLIMIT))

    print('Delete non-existient file ZZZ-TEST.unk:')
    fob.remove_handle('ZZZ-TEST.unk')
    handles = fob.list_handles()
    print(fob.list_handles(limit=TESTLIMIT))

    # Cleanup directory space
    fob.remove_handle('AAA-TEST.bin')
    fob.remove_handle('AAA-TEST.txt')
    fob.remove_handle('BBB-TEST.bin')
    fob.remove_handle('BBB-TEST.txt')
    fob.remove_handle('CCC-TEST.bin')
    fob.remove_handle('CCC-TEST.txt')

    print('Congratulations')
