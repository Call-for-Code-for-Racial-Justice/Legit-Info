#!/usr/bin/env python3
# fixmap.py -- Take list of relevant words and create CSV
# By Tony Pearson, IBM, 2020
#
import os
import sys
import glob
import re
import json

OutForm = '"{}", "{}"'

if __name__ == "__main__":
    if len(sys.argv) == 3:
        in_name = sys.argv[1]
        out_name = sys.argv[2]
    else:
        sys.exit(4)

    with open(in_name, 'r') as infile:
        with open(out_name, 'w') as outfile:
            lines = infile.readlines()
            for line in lines:
                words = line.split(',')
                if len(words)>1:
                    term = words[0].rstrip()
                    impact = words[1].rstrip()
                    if term != 'term' and impact != 'impact':
                        print(OutForm.format(term, impact), file=outfile)
