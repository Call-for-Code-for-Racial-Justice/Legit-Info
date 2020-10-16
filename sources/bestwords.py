#!/usr/bin/env python3
# bestwords.py -- Take list of relevant words and create CSV
# By Tony Pearson, IBM, 2020
#
import os
import sys
import glob
import re
import json

RelRegex = re.compile(r"('.*'),")
RelRegex2 = re.compile(r'(".*"),')

def process_group(state, groupnum, first_bill, last_bill, txtfiles):
    zipname = zipForm.format(state, groupnum, first_bill, last_bill)
    cmd = cmdForm.format(zipname, txtfiles)
    rc = os.system(cmd)
    results.append(resForm.format(zipname,rc))
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
        filename = sys.argv[1]
    else:
        sys.exit(4)

    words, wordlist = {}, []

    # Using readlines() 
    num = 0
    with open(filename, 'r') as infile:
        lines = infile.readlines() 
        for line in lines:
            if line[0] == '[':
                relevants = line.split("{'text':")
                for rel in relevants:

                    mo = RelRegex.search(rel)
                    if mo:
                        term = mo.group(1)
                        newterm = '"' + term[1:-1] + '"'
                        if newterm not in words:
                            words[newterm] = 1
                            wordlist.append(newterm)
                        else:
                            words[newterm] += 1
                    elif rel == '[':
                        pass
                    else:
                        mo = RelRegex2.search(rel)
                        if mo:
                            term = mo.group(1)
                            if term not in words:
                                words[term] = 1
                                wordlist.append(term)
                            else:
                                words[term] += 1

    wordlist.sort()
    with open("wordlist.csv", "w") as outfile:
        print("term, occurs, impact", file=outfile)
        for word in wordlist:
            print(word, "," , words[word], ", ", file= outfile)
                
    print("Created: wordlist.csv")
  
    
