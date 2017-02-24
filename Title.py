#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Stuff related to publication titles

import re

def strip(title):
    """
    Remove all non-alphanumeric characters from title, including spaces,
    and force everything to lower case.

    This results in an unreadable title, but it is much more useful for 
    comparisons.
    """
    return(re.sub(r'\W+', '', title.lower()))

    
