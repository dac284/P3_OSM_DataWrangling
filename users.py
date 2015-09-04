#!/usr/bin/env python
# -*- coding: utf-8 -*-
import xml.etree.cElementTree as ET
import pprint
import re
import sys

"""
Your task is to explore the data a bit more.
The first task is a fun one - find out how many unique users
have contributed to the map in this particular area!

The function process_map should return a set of unique user IDs ("uid")
"""

def get_user(element):
    try:
        return element.attrib['uid']
    except:
        return False

def process_map(filename):
    users = set()
    for _, element in ET.iterparse(filename):
        
        if get_user(element):
            if not (get_user(element) in users):
                users.add(get_user(element))

    return users


def test(file_in):

    users = process_map(file_in)
    pprint.pprint(users)
    pprint.pprint(len(users))



if __name__ == "__main__":
    test(sys.argv[1])