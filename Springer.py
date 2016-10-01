#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Information about Springer references.
#
# Note that we don't currently get alerts from Springer.  This module supports
# Springer articles that are identified from other sources

import quopri                             # quoted-printable encoding
import re
import alert

SPRINGER_JHU_URL = "http://link.springer.com.proxy1.library.jhu.edu/"
SPRINGER_URL = "http://link.springer.com/"
SPRINGER_URL_LEN = len(SPRINGER_URL)



def isSpringerUrl(url):
    """
    Return true if the given URL is a Springer url.
    """
    return(len(url) >= SPRINGER_URL_LEN and url[0:SPRINGER_URL_LEN] == SPRINGER_URL)


def createHopkinsUrl(url):
    """
    Given a Springer URL, convert it to a Hopkins URL
    """
    # Springer URLs look like
    # http://link.springer.com/protocol/10.1007/978-1-4939-2690-9_20
    # Make it look like:
    # http://link.springer.com.proxy1.library.jhu.edu/protocol/10.1007%2F978-1-4939-2690-9_20
    urlParts = url.split("/")
    return(SPRINGER_JHU_URL + "/".join(urlParts[3:]))
