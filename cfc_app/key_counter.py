#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
Gather statistics for any key
"""
# System imports
import sys
# Django and other third-party imports


class KeyCounter():
    """
    Gather statistics for any key,value pair
    """

    def __init__(self, name, keys=None, toplist=True, limit=10):
        self.name = name
        self.dict = {}
        self.keys = []
        if not keys:
            self.keys = keys
        self.keys_min = None
        self.keys_max = None
        self.count = 0
        self.toplist = toplist
        self.limit = limit
        return None

    def consider_key(self, key):
        """ Add this key to the count for statistics """

        self.count += 1
        if self.keys:
            if key not in self.keys:
                key = "Other"
        if key in self.dict:
            self.dict[key] += 1
        else:
            self.dict[key] = 1

        if self.keys_max is None:
            self.keys_min = key
            self.keys_max = key

        elif key < self.keys_min:
            self.keys_min = key

        elif key > self.keys_max:
            self.keys_max = key

        return None

    def key_results(self):
        """ Show results for this key """

        print(self.name)
        print("Number considered: ", self.count)
        if self.count:
            print("Minimum: [{}]  Maximum [{}]".format(self.keys_min,
                                                       self.keys_max))

            num = 0
            print(' ')
            if self.count > 1 and self.toplist:
                print("Top {} List:".format(self.limit))
                for keyword, count in sorted(self.dict.items(),
                                             key=lambda item: item[1],
                                             reverse=True):
                    print("[{}] had {} occurences".format(keyword, count))
                    num += 1
                    if num >= self.limit:
                        break
        print(' ')
        return None


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    counter = KeyCounter('Test1')
    counter.key_results()

    counter = KeyCounter('Test2')
    counter.consider_key("Hello")
    counter.key_results()

    counter = KeyCounter('Test3')
    counter.consider_key("Hello")
    counter.consider_key("Goodbye")
    counter.key_results()

    counter.toplist = False
    counter.key_results()

    counter = KeyCounter("Test 4")
    for n in range(100):
        counter.consider_key(n)
    for n in range(50):
        counter.consider_key(n)
    for n in range(30):
        counter.consider_key(n)
    for n in range(20):
        counter.consider_key(n)
    for n in range(10):
        counter.consider_key(n)
    for n in range(7):
        counter.consider_key(n)
    for n in range(3):
        counter.consider_key(n)
    counter.key_results()

    counter.limit = 5
    counter.key_results()

# end
