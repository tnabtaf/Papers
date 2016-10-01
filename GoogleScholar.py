#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Information about alert from Google Scholar


import re
import alert
import quopri                             # Quoted printable encoding
import html.parser
import urllib.parse

SENDER = "scholaralerts-noreply@google.com"

ELLIPSIS_TAIL = "  " + chr(8230)  #"  &hellip;"
ELLIPSIS_TAIL_LEN = len(ELLIPSIS_TAIL)

#SD_JHU_PII_URL = "http://www.sciencedirect.com.proxy1.library.jhu.edu/science/article/pii/"
#SD_PII_URL = "http://www.sciencedirect.com/science/article/pii/"

class Paper(alert.PaperAlert, html.parser.HTMLParser):
    """
    Describe a particular paper being reported by Google Scholar
    """

    def __init__(self):
        """

        """
        super(alert.PaperAlert,self).__init__()
        html.parser.HTMLParser.__init__(self)
        
        self.title = ""
        self.titleTruncated = False
        self.authors = ""
        self.source = ""
        self.doiUrl = ""
        self.doi = ""
        self.url = ""
        self.hopkinsUrl = ""
        self.search = "Google "
        return None
        
    def getFirstAuthorLastName(self):
        """
        DM Meinel, G Margos, R Konrad, S Krebs, H Blum ...
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

    def titleIsTruncated(self):
        return self.titleTruncated


class Email(alert.Alert, html.parser.HTMLParser):
    """
    All the information in a Google Scholar Email alert.

    Parse HTML email body from Google Scholar.  The body may be reporting more
    than one paper.
    """
    searchStartRe = re.compile(r'Scholar Alert: ')

    def __init__(self, email):

        html.parser.HTMLParser.__init__(self)

        self.papers = []
        self.search = "Google "
        self.currentPaper = None

        self.inSearch = False
        self.inTitleLink = False
        self.inTitleText = False
        self.inAuthorList = False

        # Google Scholar email body content is Quoted Printable encoded.  Decode it.
        emailBodyText = quopri.decodestring(email.getBodyText())
        self.feed(emailBodyText.decode('utf-8')) # process the HTML body text.
        
        return None
        
    def handle_data(self, data):

        data = data.strip()

        startingSearch = Email.searchStartRe.match(data)
        if startingSearch:
            self.search += data
            self.inSearch = True

        elif self.inSearch:
            self.search += " " + data

        elif self.inTitleText and data:
            # sometimes we lose space between too parts of title.
            if self.currentPaper.title and self.currentPaper.title[-1] != " ":
                self.currentPaper.title += " "
            self.currentPaper.title += data
            """
            if self.currentPaper.title[- ELLIPSIS_TAIL_LEN:] == ELLIPSIS_TAIL:
                # clip it, title will be only a partial match.
                self.currentPaper.title = self.currentPaper.title[0:- ELLIPSIS_TAIL_LEN]
                self.currentPaper.titleTruncated = True
                print("Clipped: " + self.currentPaper.title)
            """
            # Fix title, stripping thing yattag can't cope with.
            self.currentPaper.title = self.currentPaper.title

        elif self.inAuthorList and data:
            # Author list may also have source at end
            parts = data.split("- ")
            self.currentPaper.authors += parts[0].strip()
            if len(parts) == 2:
                self.currentPaper.source = parts[1]

        return(None)
            
    def handle_starttag(self, tag, attrs):
        
        if tag == "h3":
            # link to paper is shown in h3.
            self.inTitleLink = True
            self.currentPaper = Paper()
            self.papers.append(self.currentPaper)
            self.currentPaper.search = self.search
            
        elif tag == "a" and self.inTitleLink:
            fullUrl = attrs[0][1]
            urlArgs = fullUrl[fullUrl.find("?")+1:].split("&")
        
            for urlArg in urlArgs:
                #print("URL_ARG: " + urlArg)
                if urlArg[0:2] == "q=":
                    # need to get rid of URL encoding.
                    self.currentPaper.url = urllib.parse.unquote(urlArg[2:])
                    #print("Q URL Uncoded: " + urllib.unquote(urlArg[2:]))
                    break
                elif urlArg[0:4] == "url=":
                    self.currentPaper.url = urllib.parse.unquote(urlArg[4:])
                    #print("URL URL Uncoded: " + urllib.unquote(urlArg[4:]))
                    break
            self.inTitleLink = False
            self.inTitleText = True
            
        return (None)

    def handle_endtag(self, tag):

        if tag == "b" and self.inSearch:
            self.inSearch = False
        elif tag =="a" and self.inTitleText:
            self.inTitleText = False
        elif tag == "h3":
            self.inAuthorList = True
        elif tag == "div" and self.inAuthorList:
            self.inAuthorList = False
            
        return (None)
    
    def handle_startendtag(self, tag, attrs):
        """
        Process tags like IMG and BR that don't have end tags.
        """
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
