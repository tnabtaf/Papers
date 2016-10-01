#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Information about a Web of Science reference / Citation


import re
import alert
import html.parser

SENDER = "noreply@isiknowledge.com"


class WOSPaper(alert.PaperAlert):
    """
    Describe a particular paper being reported by Web of Science
    """

    def __init__(self):
        """
        Next thing is get DOIs and sources, clean up auhors,
        """
        self.title = ""
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.hopkinsUrl = ""
        self.search = "WoS: "
        return None

    def getTitleLower(self):
        return(re.sub(r'\W+', '', self.title.lower()))
        
    def getFirstAuthorLastName(self):
        if self.authors:
            return(self.authors[0].split()[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


        
class Email(alert.Alert, html.parser.HTMLParser):
    """
    All the information in a Web of Science Email.

    Parse HTML email body from Web Of Science. The body maybe reporting more than one
    paper.
    """

    paperStartRe = re.compile(r'Record \d+ of \d+\.')
    citedArticleRe = re.compile(r'.*Cited Article:.*')

    def __init__(self, email):

        alert.Alert.__init__(self)
        html.parser.HTMLParser.__init__(self)
        
        self.inTitle = False
        self.inTitleValue = False
        self.inAuthors = False
        self.inCitedArticle = False
        self.inCitedArticleValue = False
        self.inSource = False
        self.search = "WoS: "

        self.feed(str(email.getBodyText())) # process the HTML body text.

        return None
        
    def handle_data(self, data):

        data = data.strip().strip(r'\r\n')
        # print("In handle_data: " + data)
        starting = Email.paperStartRe.match(data)
        if starting:
            # Each paper starts with: "Record m of n. "
            self.current = WOSPaper()
            self.papers.append(self.current) 
            
        elif data == "Title:":
            self.inTitle = True
            # print("Set inTitle")

        elif data == "Authors:":
            self.inAuthors = True

        elif Email.citedArticleRe.match(data):
            self.inCitedArticle = True
            # print("Set inCitedArticle")
            
        elif data == "Source:":
            self.inSource = True

        elif data == "Language:":
            self.inSource = False
            
        elif self.inTitleValue:
            self.current.title = data
            # print("Set Title= " + self.current.title)

        elif self.inAuthors:
            self.current.authors = data
            self.inAuthors = False

        elif self.inCitedArticleValue:
            # need to strip "]]>" from anywhere. Bug in WOS, if punctuation in title.
            self.search += data.replace("]]>","")
            self.inCitedArticle = False
            self.inCitedArticleValue = False
            # print("Set Search: " + self.search)

        elif self.inSource:
            self.current.source += data + " "
            
    def handle_starttag(self, tag, attrs):

        # print("In handle_starttag: " + tag)
        if self.inTitle and tag == "value":
            self.inTitleValue = True
            # print("Set inTitleValue")
            
        elif self.inCitedArticle and tag == "font":
            self.inCitedArticleValue = True
            # print("Set inCitedArticleValue")
            
        elif self.inSource and tag == "a":
            self.current.doiUrl = attrs[0][1].lower()
            self.current.doi = self.current.doiUrl[18:]
                

    def handle_endtag(self, tag):

        # print("In handle_endtag: " + tag)
        if self.inTitleValue and tag == "value":
            # print("Clearing inTitleValue, inTitle")
            self.inTitleValue = False
            self.inTitle = False
            
        elif self.inCitedArticleValue and tag == "font":
            # print("Clearing inCitedArticleValue, inCitedArticle")
            self.inCitedArticleValue = False
            self.inCitedArticle = False
