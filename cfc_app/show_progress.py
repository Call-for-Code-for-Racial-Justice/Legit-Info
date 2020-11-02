#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
ShowProgress.py -- print dots across the screen

Written by Tony Pearson, IBM, 2020
Licensed under Apache 2.0, see LICENSE for details
"""

# System imports
import sys
import time

# Django and other third-party imports
# Application imports
# import pdb; pdb.set_trace()


class ShowProgress():
    """
    Class to show progress in long-running tasks

    from ShowProgress import ShowProgress
    dot = ShowProgress()
    dot.show()  # print a single character to show progress
    dot.end()  # End the sequence, print newline

    Default character is period(.), you can change the character:
        dot = ShowProgress(dotchar="#")
    """

    def __init__(self, dotchar="."):
        """ Set characters to use for showing progress"""
        self.dotchar = dotchar

    def show(self, char=None):
        """ Display a single dot """
        use_char = self.dotchar
        if char:
            use_char = char
        sys.stdout.write(use_char)
        sys.stdout.flush()
        return None

    def end(self):
        """ End the sequence of dots """
        print("")
        sys.stdout.flush()
        return None


if __name__ == "__main__":
    print('Testing: ', sys.argv[0])

    dot = ShowProgress()
    for n in range(50):
        dot.show()
        time.sleep(0.3)
    dot.end()

    print('Testing with different character')
    dash = ShowProgress(dotchar='#')
    for n in range(50):
        dash.show()
        time.sleep(0.2)
    dash.end()

    print('Changing character midway')
    hash = ShowProgress(dotchar="#")
    for n in range(50):
        hash.show()
        if n > 27:
            hash.dotchar = "@"
        time.sleep(0.1)
    hash.end()
    print('Congratulations')
