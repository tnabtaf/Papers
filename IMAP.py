#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Deals with sources of paper / citation info that are email

import json
import sys
import getpass                            #
import imaplib                            # Email protocol
import os.path
import re

HEADER_PARTS = "(BODY.PEEK[HEADER.FIELDS (From Subject)])"
BODY_PARTS = "(BODY.PEEK[TEXT])"

GMAIL_HOST = "imap.gmail.com"


class Email(object):
    """
    Abstraction of an IMAP email.
    """
    def __init__(self, header, body):
        self.header = header
        self.body = body

        return(None)

    def getHeader(self):
        return(self.header)

    def getBody(self):
        return(self.body)

    # need a routine here to determine if this is base64 encoded
    # have getBodyText call it, and then unencode body before returning it.
        
    def getBodyText(self):
        return(self.body[0][1])


class GMailSource(object):
    """
    Used when source is a GMail account.  It has a very definite sense of
    current mailbox, current search, and current email.
    """

    def __init__(self, account, pw):
        """
        Given a GMail account and the account password, open a connection to
        that account.
        """
        self.email = imaplib.IMAP4_SSL(GMAIL_HOST)
        self.email.login(account, pw)
        self.currentEmails = []
        
        return(None)

    def getEmails(self, mailbox, search):
        """
        Given the name of a mailbox, and a search condition (not pretty), return
        all the emails in that box, that match the search.
        """
        self.currentEmails = []
        
        self.email.select(mailbox, True)
        typ, self.msgNums = self.email.uid('search', None, search)

        # msgNums is a list of msg numbers

        for msgNum in self.msgNums[0].split():
            typ, header = self.email.uid("fetch", msgNum, HEADER_PARTS)    
            typ, body = self.email.uid("fetch", msgNum, BODY_PARTS)
            self.currentEmails.append(Email(header, body))

        return iter(self.currentEmails)

    
    def next(self):
        msgNum = self.iter.next()
        typ, header = self.email.uid("fetch", msgNum, HEADER_PARTS)    
        typ, body = self.email.uid("fetch", msgNum, BODY_PARTS)
        return(Email(header, body))
        

def buildSearchString(sender = None,
                      sentSince = None,
                      sentBefore = None):
    """
    Builds an IMAP search string from the given inputs.  At least one search parameter
    must be provided.
    """
    clauses = []
    if sentSince:
        clauses.append('SENTSINCE ' + sentSince)
    if sentBefore:
        clauses.append('SENTBEFORE ' + sentBefore)
    if sender:
        clauses.append('From "' + sender + '"')

    if len(clauses) == 0:
        print("At least one parameter must be passed to IMAP.buildSearchString")
        return None                       # That'll show 'em.
        
    return('(' + " ".join(clauses) + ')')
                       
    
        
                          
