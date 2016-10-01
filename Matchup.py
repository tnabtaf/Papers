#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Matchups between new reports and papers already in CiteUlike

import csv
import urllib.parse
import yattag

import Springer
import Wiley                              # Wileay Online Library Saved Search Alerts
import HistoryDB

class Matchup(object):
    """
    Pairs titles (and the list of papers with that title) and CUL entries with that title
    """

    def __init__(self, papers, culEntries):

        self.papers = papers
        self.culEntries = culEntries          # might be None
        self.lowerTitle = papers[0].getTitleLower()
        self.title = papers[0].getTitle()
        return None

    def debugPrint(self, descrip="", indent=""):
        print(indent + "DEBUG: Matchup: " + descrip)
        print(indent + "  lowerTitle: " + self.lowerTitle)
        print(indent + "  title: " + self.title)
        print(indent + "  papers: ")
        for paper in self.papers:
            paper.debugPrint(indent=indent + "  ")
        print(indent + "  culEntries: ")
        if self.culEntries:
            for culEntry in self.culEntries:
                culEntry.debugPrint(indent=indent + "  ")
        print(indent + "  DONE")
        return(None)


    def getDoiFromPapers(self):
        """
        List is assumed to have been pre-verified to have consistent DOIs
        """
        for paper in self.papers:
            if paper.doi:
                return(paper.doi)
        return(None)

        

def getDoiFromPaperList(paperList):
    """
    List is assumed to have been pre-verified to have consistent DOIs
    """
    for paper in paperList:
        if paper.doi:
            return(paper.doi)
    return(None)

def getDoiUrlFromPaperList(paperList):
    """
    List is assumed to have been pre-verified to have consistent DOIs
    """
    for paper in paperList:
        if paper.doiUrl:
            return(paper.doiUrl)
    return(None)

def getUrlFromPaperList(paperList):
    """
    Extract a URL from paper list.  Favor DOI URLs, and then fallback to others
    if needed.
    List is assumed to have been pre-verified to have consistent DOIs
    """
    doiUrl = getDoiUrlFromPaperList(paperList)
    if not doiUrl:  
        for paper in paperList:
            if paper.url:
                return(paper.url)

    return(doiUrl)

def getHopkinsUrlFromPaperList(paperList):
    """
    Extract a Hopkins specific URL from paper list.  
    Not all sources have this.
    """
    hopkinsUrl = None
    doiUrl = getDoiUrlFromPaperList(paperList)
    if doiUrl:
        urlParts = doiUrl.split("/")
        hopkinsUrl = "/".join(urlParts[0:3]) + ".proxy1.library.jhu.edu/" + "/".join(urlParts[3:])
    else:
        for paper in paperList:
            if paper.hopkinsUrl:
                return(paper.hopkinsUrl)
            elif Wiley.isWileyUrl(paper.url):
                # Some wiley comes from other searches.
                return(Wiley.createHopkinsUrl(paper.url))
            elif Springer.isSpringerUrl(paper.url):
                return(Springer.createHopkinsUrl(paper.url))
            elif paper.url and not hopkinsUrl:
                urlParts = paper.url.split("/")
                hopkinsUrl = "/".join(urlParts[0:3]) + ".proxy1.library.jhu.edu/" + "/".join(urlParts[3:])
    return(hopkinsUrl)

def createReport(matchupsByLowTitle, sectionTitle):
    """
    Return an HTML report of what needs to be done.
    """
    
    doc, tag, text = yattag.Doc().tagtext()

    with tag("h2", style="width: 100%; background-color: #eeeeff"):
        text(sectionTitle)

    for matchup in matchupsByLowTitle.values():

        with tag("h3"):
            text(matchup.papers[0].title)

        with tag("ol"):
            for paper in matchup.papers:
                with tag("li"):
                    text(paper.search)
                    with tag("ul"):
                        with tag("li"):
                            text(paper.authors)
                        if paper.doi:
                            with tag("li"):
                                with tag("a", href=paper.doiUrl, target="_blank"):
                                    text(paper.doi)
                        with tag("li"):
                            text(paper.source)
                        with tag("li"):
                            text(paper.title)

        if matchup.culEntries:
            for culEntry in matchup.culEntries:
                with tag("p"):
                    with tag("a", href=culEntry.getCulUrl()):
                        text("Paper @ CiteULike")
        else:
            with tag("ul"):
                url = getUrlFromPaperList(matchup.papers)
                if url:
                    # Got a url, post it to CiteULike, and link to it.
                    with tag("li"):
                        with tag("a", href="http://www.citeulike.org/posturl?url=" + url,
                                target="citeulike"):
                            text("Submit to CiteULike")
                    with tag("li"):
                        with tag("a", href=url, target="paper"):
                            text("See paper")

                hopkinsUrl = getHopkinsUrlFromPaperList(matchup.papers)
                if hopkinsUrl:
                    with tag("li"):
                        with tag("a", href=hopkinsUrl, target="paperhopkins"):
                            text("See paper @ Hopkins")
                            
                # Search for it at Hopkins; Google and pubmed too
                with tag("li"):
                    with tag("a",
                             href="https://catalyst.library.jhu.edu/?utf8=%E2%9C%93&search_field=title&" +
                             urllib.parse.urlencode({"q": matchup.title}),
                             target="jhulib"):
                        text("Search Hopkins")
                    
                with tag("li"):
                    with tag("a",
                             href="https://www.google.com/search?q=" + matchup.title,
                             target="googletitlesearch"):
                        text("Search Google")
                        
                with tag("li"):
                    with tag("a",
                             href="http://www.ncbi.nlm.nih.gov/pubmed/?term=" + matchup.title,
                             target="pubmedtitlesearch"):
                        text("Search Pubmed")
                        
    reportHtml = yattag.indent(doc.getvalue())

    # do some cleanup
    # fix a problem with some Google Scholar URLs.  Google Scholar does not like &amp; in place of &
    reportHtml = reportHtml.replace("&amp;", "&")   # potentially risky outside of URLs
    
    return(reportHtml)




def reportPaper(matchup, history):
    """
    Return HTML report for this matchup
    """
    if not hasattr(reportPaper, "newCounter"):
        reportPaper.newCounter = 0  # it doesn't exist yet, so initialize it
        reportPaper.knownCounter = 0
    
    doc, tag, text = yattag.Doc().tagtext()

    newPaper = not matchup.culEntries
    
    if newPaper:
        # reported paper already in CiteULike
        reportPaper.newCounter += 1
        bgColor = "#eef"
        fontColor = "#000"

        # if we saw this paper in the previous run, then it is newish.
        leader = "New"
        if history:
            historyEntry = history.getByTitleLower(matchup.lowerTitle)
            if not historyEntry:
                historyEntry = history.getByDoi(getDoiFromPaperList(matchup.papers))
            if historyEntry:
                leader = "Newish [" + historyEntry[HistoryDB.COMMENTS] + "] "
        leader += " (#" + str(reportPaper.newCounter) + "):" 
        hLevel = "h2"
    else:
        # report paper is known
        reportPaper.knownCounter += 1
        bgColor = "#ccc"
        fontColor = "#666" # evil, very
        leader = "Known (#" + str(reportPaper.knownCounter) + "):" 
        hLevel = "h3"
        
    with tag("div", style="width: 100%; color: " + fontColor + "; background-color: " + bgColor):

        with tag(hLevel):
            text(leader)
            with tag("br"):
                pass
            text(matchup.papers[0].title)
    
        with tag("ol"):
            for paper in matchup.papers:
                with tag("li"):
                    text(paper.search)
                    with tag("ul"):
                        with tag("li"):
                            text(paper.authors)
                        if paper.doi:
                            with tag("li"):
                                with tag("a", href=paper.doiUrl, target="_blank"):
                                    text(paper.doi)
                        with tag("li"):
                            text(paper.source)
                        with tag("li"):
                            text(paper.title)

        if not newPaper:
            for culEntry in matchup.culEntries:
                with tag("p"):
                    with tag("a", href=culEntry.getCulUrl()):
                        text("Paper @ CiteULike")
        else:
            with tag("ul"):
                url = getUrlFromPaperList(matchup.papers)
                if url:
                    # Got a url, post it to CiteULike, and link to it.
                    with tag("li"):
                        with tag("a", href="http://www.citeulike.org/posturl?url=" + url,
                                target="citeulike"):
                            text("Submit to CiteULike")
                    with tag("li"):
                        with tag("a", href=url, target="paper"):
                            text("See paper")

                hopkinsUrl = getHopkinsUrlFromPaperList(matchup.papers)
                if hopkinsUrl:
                    with tag("li"):
                        with tag("a", href=hopkinsUrl, target="paperhopkins"):
                            text("See paper @ Hopkins")
                            
                # Search for it at Hopkins; Google and pubmed too
                with tag("li"):
                    with tag("a",
                             href="https://catalyst.library.jhu.edu/?utf8=%E2%9C%93&search_field=title&" +
                             urllib.parse.urlencode({"q": matchup.title}),
                             target="jhulib"):
                        text("Search Hopkins")
                    
                with tag("li"):
                    with tag("a",
                             href="https://www.google.com/search?q=" + matchup.title,
                             target="googletitlesearch"):
                        text("Search Google")
                        
                with tag("li"):
                    with tag("a",
                             href="http://www.ncbi.nlm.nih.gov/pubmed/?term=" + matchup.title,
                             target="pubmedtitlesearch"):
                        text("Search Pubmed")

    reportHtml = yattag.indent(doc.getvalue())

    # do some cleanup
    # fix a problem with some Google Scholar URLs.  Google Scholar does not like &amp; in place of &
    reportHtml = reportHtml.replace("&amp;", "&")   # potentially risky outside of URLs
    
    return(reportHtml)


