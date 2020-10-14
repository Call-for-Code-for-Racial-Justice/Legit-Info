#!/usr/bin/env python3
# scanjson.py -- Scan JSON from Legiscan API
# By Tony Pearson, IBM, 2020
#
import codecs
import json
import sys

charForm = "{} for {} on {} from position {} to {}. Using '?' in-place of it!"


class Stats():
    """
    Class to identify minimum, maximum and average lenght of strings

    """

    def __init__(self, id, limit):
        """ Set characters to use for showing progress"""
        self.id = id
        self.limit = limit
        self.min = None
        self.max = None
        self.total = 0
        self.count = 0
        self.overlim = 0
        self.ShowForm = "{} Min: {}  Average: {}  "
        self.ShowForm += "Maximum {}  Count {}  Over {}"
        return None

    def add_stat(self, num):
        if self.count == 0:
            self.min = num
            self.max = num
        elif num < self.min:
            self.min = num
        elif num > self.max:
            self.max = num
        if num > self.limit:
            self.overlim += 1

        self.total += num
        self.count += 1
        return self

    def show_stat(self):
        result = self.id + " No statistics"
        if self.count > 0:
            avg = self.total // self.count
            result = self.ShowForm.format(self.id, self.min, avg,
                                          self.max, self.count, self.overlim)
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
                          exception.end))
    return ("?", exception.end)


if __name__ == "__main__":
    # Check proper input syntax
    codecs.register_error("custom_character_handler", custom_character_handler)

    display_help, jsonname = get_parms(sys.argv)
    state = jsonname[:2].upper()

    keystats = Stats('Key', 20)
    titlestats = Stats('Title', 200)
    summarystats = Stats('Summary', 1000)
    billstats = Stats('Billtext', 4000000)

    if not display_help:
        with open(jsonname, "r") as jsonfile:
            data = json.load(jsonfile)
            num = 0
            for entry in data:
                num += 1
                bill = data[entry]
                key = "{}-{}.txt".format(state, bill['number'])
                title = bill['title']
                summary = bill['description']
                print('KEY: ', key)
                print('TITLE: ', title)
                print('SUMMARY: ', summary)

                keystats.add_stat(len(key))
                titlestats.add_stat(len(title))
                summarystats.add_stat(len(summary))
                billstats.add_stat(len(bill['bill_text']))
                if num >= 10:
                    break

    print(' ')
    print('Statistics:')
    print(keystats.show_stat())
    print(titlestats.show_stat())
    print(summarystats.show_stat())
    print(billstats.show_stat())
    print('Done.')
