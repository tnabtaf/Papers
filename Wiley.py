#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Information about a Wiley Online Library reference / Citation

import quopri                             # quoted-printable encoding
import re
import alert
import html.parser

SENDER = "WileyOnlineLibrary@wiley.com"

WILEY_JHU_URL = "http://onlinelibrary.wiley.com.proxy1.library.jhu.edu/"
WILEY_URL = "http://onlinelibrary.wiley.com/"
WILEY_URL_LEN = len(WILEY_URL)

class Paper(alert.PaperAlert, html.parser.HTMLParser):
    """
    Describe a particular paper being reported by Wiley Online Library
    """

    def __init__(self):
        """

        """
        super(alert.PaperAlert,self).__init__()
        html.parser.HTMLParser.__init__(self)
        
        self.title = ""
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.hopkinsUrl = ""
        self.search = "Wiley Online Library: "
        return None
        
    def getFirstAuthorLastName(self):
        """
        Pieter-Jan Maenhaut, Hendrik Moens, Veerle Ongenae and Filip De Turck
        This will mess up on van Drysdale etc.
        """
        if self.authors:
            return(self.authors.split(",")[0].split(" ")[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor


        
class Email(alert.Alert, html.parser.HTMLParser):
    """
    All the information in a Wiley Saved Search Alert.

    Parse HTML email body from Wiley.  The body maybe reporting more
    than one paper.
    """
    searchStartRe = re.compile(r'Access (the|all \d+) new result[s]*')

    def __init__(self, email):

        html.parser.HTMLParser.__init__(self)

        self.papers = []
        self.search = "Wiley Online Library: "
        self.currentPaper = None

        self.inParsing = False
        self.inSearch = False
        self.awaitingTitle = False
        self.inTitle = False
        self.awaitingJournal = False
        self.inJournal = False
        self.awaitingAuthors = False
        self.inAuthors = False

        # email uses Quoted Printable encoding Decode it.
        cleaned =  quopri.decodestring(email.getBodyText())

        # It's a Multipart email; just ignore anything outside HTML part.
        self.feed(cleaned.decode('utf-8')) # process the HTML body text.
        
        return None
        
    def handle_data(self, data):

        data = data.strip()

        if self.inSearch:
            self.search += data
        elif self.inTitle:
            self.currentPaper.title += data
        elif self.inJournal:
            self.currentPaper.source += data
        elif self.inAuthors:
            # Author string also has date in it:
            # March 2015Pieter-Jan Maenhaut, Hendrik Moens, Veerle Ongenae and Filip De Turck
            # strip off anything looking like a year and before.
            self.currentPaper.authors += re.split(r"\d{4}", data)[-1]
            
        return(None)
            
    def handle_starttag(self, tag, attrs):

        if tag == "html":
            self.parsing = True
        elif self.parsing and tag == "strong":
            self.inSearch = True
        elif self.parsing and tag == "a" and len(attrs) > 2 and attrs[2][1] == "http://journalshelp.wiley.com":
            self.parsing = False          # Done looking at input.
            self.awaitingTitle = False
        elif self.parsing and self.awaitingTitle and tag == "a":
            self.awaitingTitle = False
            self.inTitle = True

            self.currentPaper = Paper()
            self.papers.append(self.currentPaper)
            self.currentPaper.search = self.search
            
            # URL looks like
            # http://onlinelibrary.wiley.com/doi/10.1002/spe.2320/abstract?campaign=wolsavedsearch
            # http://onlinelibrary.wiley.com/doi/10.1002/cpe.3533/abstract
            # Make it look like:
            # http://onlinelibrary.wiley.com.proxy1.library.jhu.edu/doi/10.1002/spe.2320/abstract
            baseUrl = attrs[1][1]
            if baseUrl[0:4] != "http":
                # Wiley sometimes forgets leading http://
                baseUrl = "http://" + baseUrl
            urlParts = baseUrl.split("/")
            self.currentPaper.doi = "/".join(urlParts[4:6])
            self.currentPaper.url = baseUrl
            self.currentPaper.hopkinsUrl = createHopkinsUrl(baseUrl)
            self.currentPaper.doiUrl = "http://dx.doi.org/" + self.currentPaper.doi
        elif self.awaitingJournal and tag == "span":
            self.inJournal = True
            self.awaitingJournal = False
            
        return (None)

    def handle_endtag(self, tag):

        if self.inSearch and tag == "strong":
            self.inSearch = False
            self.awaitingTitle = True
        elif self.inTitle and tag == "a":
            self.inTitle = False
            self.awaitingJournal = True
        elif self.inJournal and tag == "span":
            self.inJournal = False
            self.awaitingAuthors = True
                
        return (None)
    
    def handle_startendtag(self, tag, attrs):
        """
        Process tags like IMG and BR that don't have end tags.
        """
        if self.awaitingAuthors and tag == "br":
            self.inAuthors = True
            self.awaitingAuthors = False
        elif self.inAuthors and tag == "br":
            self.inAuthors = False
            self.awaitingTitle = True   # in case there are more

        return(None)

        
    def getPapers(self):
        """
        Return list of referencing papers in this alert.
        """
        return(self.papers)

    def getSearch(self):
        """
        Returns text identifying what web os science search this alert is for.
        """
        return(self.search)


def isWileyUrl(url):
    """
    Return true if the given URL is a Wiley url.
    """
    return(len(url) >= WILEY_URL_LEN and url[0:WILEY_URL_LEN] == WILEY_URL)


def createHopkinsUrl(url):
    """
    Given a Wiley URL, convert it to a Hopkins URL
    """
    # Wiley URLs look like
    # http://onlinelibrary.wiley.com/doi/10.1002/spe.2320/abstract?something
    # http://onlinelibrary.wiley.com/doi/10.1002/prca.201400173/abstract?campaign=wolsavedsearch
    # Make it look like:
    # http://onlinelibrary.wiley.com.proxy1.library.jhu.edu/doi/10.1002/spe.2320/abstract
    url_parts = url.split("/")
    return(WILEY_JHU_URL + "/".join(url_parts[3:6]) + '/abstract')
