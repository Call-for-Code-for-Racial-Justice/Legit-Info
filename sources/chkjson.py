#!/usr/bin/env python3
# scanjson.py -- Scan JSON from Legiscan API
# By Tony Pearson, IBM, 2020
#
import base64
import codecs
import json
import sys

charForm = "{} for {} on {} from position {} to {}. Using '?' in-place of it!"


class Stats():
    """
    Class to identify minimum, maximum and average lenght of strings

    """

    def __init__(self, id):
        """ Set characters to use for showing progress"""
        self.id = id
        self.min = None
        self.max = None
        self.total = 0
        self.count = 0
        self.ShowForm = "{} Min: {}  Average: {}   Maximum {}"
        return None

    def add_stat(self, num):
        if self.count == 0:
            self.min = num
            self.max = num
        elif num < self.min:
            self.min = num
        elif num > self.max:
            self.max = num
        self.total += num
        self.count += 1
        return self

    def show_stat(self):
        result = id + " None"
        if self.count > 0:
            avg = self.total / self.count
            result = self.ShowForm.format(self.id, self.min, avg, self.max)
        return result


def get_parms(argv):
    display_help = False
    filename = ''
    if len(sys.argv) == 2:
        filename = sys.argv[1]
        if filename == '--help' or filename == '-h':
            display_help = True
        if not filename.endswith('.json'):
            display_help = True
    else:
        display_help = True

    if display_help:
        print('Syntax:')
        print(sys.argv[0], 'input_file.json')
        print(' ')

    return display_help, filename


def custom_character_handler(exception):
    print(charForm.format(exception.reason,
            exception.object[exception.start:exception.end],
            exception.encoding,
            exception.start,
            exception.end ))
    return ("?", exception.end)


if __name__ == "__main__":
    # Check proper input syntax
    codecs.register_error("custom_character_handler", custom_character_handler)

    display_help, jsonname = get_parms(sys.argv)
    state = jsonname[:2].upper()

    keystats = Stats('Key')
    titlestats = Stats('Title')
    summarystats = Stats('Summery')
    billstats = Stats('Billtext')

    if not display_help:
        print('Congratulations')
        with open(jsonname, "r") as jsonfile:
            data = json.load(jsonfile)
            for entry in data:
                bill = data[entry]
                key = "{}-{}.txt".format(state, bill['number'])
                title = bill['title']
                summary = bill['summary']
                print('KEY: ', key)
                print('TITLE: ', title)
                print('SUMMARY: ', summary)
                
                keystats.add_stat(len(key))
                titlestats.add_stat(len(title))
                summarystats.add_stat(len(summary)
                billstats.add_stat(len(bill['text'])

print(keystats.show_stat())
print(keystats.show_stat())
print(keystats.show_stat())
print(keystats.show_stat())
print('Done.')
        

