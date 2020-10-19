#!/usr/bin/env python3
# makezip.py -- Make zip files of txt files
# By Tony Pearson, IBM, 2020
#
import os
import sys
import glob
import re

FileRegex = re.compile(r"\w\w-(\w*)(-Y\d*)?.txt")
zipForm = "{}-G{:02}-{}-{}.zip"
cmdForm = "zip zipfiles/{} {}"
resForm = 'Created {} RC={}'


def process_group(state, groupnum, first_bill, last_bill, txtfiles):
    zipname = zipForm.format(state, groupnum, first_bill, last_bill)
    cmd = cmdForm.format(zipname, txtfiles)
    rc = os.system(cmd)
    results.append(resForm.format(zipname, rc))
    return None


def group_files(state, count):
    globs = glob.glob(state + '*.txt')
    files = []
    for filename in globs:
        files.append(filename)

    files.sort()
    first_bill = ''
    last_bill = ''
    num, groupnum = 0, 1
    txtfiles = ''
    for filename in files:
        mo = FileRegex.search(filename)
        if mo:
            last_bill = mo.group(1)
            if first_bill == '':
                first_bill = mo.group(1)
            num += 1
            txtfiles += filename + ' '
            if num >= count:
                process_group(state, groupnum, first_bill, last_bill, txtfiles)
                first_bill = ''
                txtfiles = ''
                num = 0
                groupnum += 1
        else:
            print('Error in regex: ', filename)
    if txtfiles:
        process_group(state, groupnum, first_bill, last_bill, txtfiles)

    return None


if __name__ == "__main__":
    if len(sys.argv) == 2:
        state = sys.argv[1].upper()
        states = [state]
    else:
        states = ['AZ', 'OH']

    results = []
    for state in states:
        group_files(state, 100)

    print(' ')
    for res in results:
        print(res)
