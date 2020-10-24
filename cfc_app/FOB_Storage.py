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
DSLregex = re.compile('^DatasetList-(\d\d\d\d-\d\d-\d\d).json$')
DSNregex = re.compile('^(\w\w)-Dataset-(\d\d\d\d).json$')

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
            found = 0
            cursor = ''
            if after:
                cursor = after

            objlimit = MAXLIMIT
            if (limit > 0) and (suffix is None):
                objlimit = min(objlimit, limit)

            for n in range(999):   # Avoid run-away tasks
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
                items.append(basename)
                num += 1
                if limit > 0 and num >= limit:
                    break

        return items

    # Helpers for Legiscan DatasetList (DatasetList-YYYY-MM-DD.json)
    def DatasetList_items():
        dsl_list = self.fob.list_items(prefix='DatasetList-', suffix='.json')
        return dsl_list

    def DatasetList_search(item_name):
        mo = DSLregex.search(item_name)
        return mo

    def DatasetList_name(today):
        return 'DatasetList-{}.json'.format(today)

    # Helpers for Legiscan Dataset (SS-Dataset-NNNN.json)
    def Dataset_items(state):
        dsn_prefix = "{}-Dataset-".format(state)
        dsl_list = self.fob.list_items(prefix=dsn_prefix, suffix='.json')
        return dsl_list

    def Dataset_search(item_name):
        mo = DSNregex.search(item_name)
        return mo

    def Dataset_name(self, state, state_id):
        item_name = "{}-Dataset-{:04d}.json".format(state, state_id)
        return item_name


    def download_binary(self, item_name):
        """ Upload binary file """
        fob_mode = self.mode

        bindata = b''
        try:
            if self.cos and fob_mode == 'OBJECT':
                infile = self.cos.get_object(
                    Key=item_name, Bucket=self.cos_bucket)
                bindata = infile["Body"].read()
        except Exception as e:
            print(e)

        if self.filesys and fob_mode == 'FILE':
            fullname = os.path.join(self.filesys, item_name)
            try:
                with open(fullname, 'rb') as infile:
                    bindata = infile.read()
            except Exception as e:
                print(e)

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




    def test_with_empty(self):
        TEST_LIMIT = 10
    
        SAMPLE_BIN = b'How quickly daft jumping zebras vex'
        SAMPLE_TEXT = "The quick brown fox jumps over a lazy dog"
        UNICODE_TEXT = "ā <- abreve, ć <- c acute, ũ <- u tilde"
    
        fob.upload_binary(SAMPLE_BIN, 'AAA-TEST.bin')
        fob.upload_text(SAMPLE_TEXT, 'AAA-TEST.txt')
        fob.upload_binary(SAMPLE_BIN, 'BBB-TEST.bin')
        fob.upload_text(UNICODE_TEXT, 'BBB-TEST.txt')
        fob.upload_binary(SAMPLE_BIN, 'CCC-TEST.bin')
        fob.upload_text(SAMPLE_TEXT, 'CCC-TEST.txt')
    
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
    
    # Test with empty structure first
    fob = FOB_Storage(mode, filesys='/tmp/FOB-TEST', bucket='fob-test')
    fob.test_with_empty()

    # test_with_live copy
    fob = FOB_Storage(mode)
    item_list = fob.list_items(limit=0)
    print(len(item_list))

    print('Congratulations')
