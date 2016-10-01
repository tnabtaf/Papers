#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Information about papers 

class PaperLibrary(object):
    """
    Keeps track of all the new papers/reference, and their match in CUL entries, if any.
    """
    def __init__(self):
        self.byTitleLower = {}
        self.byDoi = {}
        self.by1stAuthorLastNameLower = {}

        # Google truncates titles, but this lib expects full paper titles.
        # Therefore we hack it.
        self.titleLenCaches = {}
        
        return(None)

    def getAllMatchupsGroupedByTitle(self):
        """
        Returns list of all matchups, grouped and indexed by lower case title.
        """
        return(self.byTitleLower)

    def getByDoi(self, doi):
        return(self.byDoi.get(doi))
        
    def addPaper(self, paper):
        """
        Add a paper to the library
        """
        titleLower = paper.getTitleLower()
        if titleLower not in self.byTitleLower:
            # Google is a special case, as they truncate titles. The paper library
            # is not set up for that.
            if type(paper).__name__ == "GSPaper" and paper.titleIsTruncated():
                # see if we have already set up a cache for this length
                truncLen = len(paper.title)
                if truncLen not in self.titleLenCaches:
                    print("      Creating new cache for length: " + str(truncLen))
                    self.titleLenCaches[truncLen] = {}
                    for lowerTitle, paperList in self.byLowerTitle.items():
                        truncLowerTitle = lowerTitle[:min(truncLen, len(lowerTitle))]
                        self.titleLenCaches[truncLen][truncLowerTitle] = papersList
                if titleLower not in self.titleLenCaches[truncLen]:
                    # Longer vesrion of paper does not exist.  Add to cache and to overall list.
                    self.byTitleLower[titleLower] = []
                    self.titleLenCaches[truncLen][titleLower] = self.byTitleLower[titleLower]
            else:
                self.byTitleLower[titleLower] = []
                # add this to any cached entries as well
                for length in self.titleLenCaches:
                    self.titleLenCaches[length][titleLower] = self.byTitleLower[titleLower]
            self.byTitleLower[titleLower].append(paper)
        else:
            self.byTitleLower[titleLower].append(paper)

        if paper.doi:
            if paper.doi not in self.byDoi:
                self.byDoi[paper.doi] = []
            self.byDoi[paper.doi].append(paper)

        firstAuthorLower = paper.getFirstAuthorLastNameLower()
        if firstAuthorLower not in self.by1stAuthorLastNameLower:
            self.by1stAuthorLastNameLower[firstAuthorLower] = []
        self.by1stAuthorLastNameLower[firstAuthorLower].append(paper)

        return(None)

    def verifyConsistentDois(self):
        """
        Confirm that any papers we think are the same, either have the same DOI, or
        don't have a DOI.
        """
        for lowerTitle, papersWithTitle in self.byTitleLower.items():
            doi = None
            for paper in papersWithTitle:
                if paper.doi:
                    if not doi:
                        doi = paper.doi
                    elif doi != paper.doi:
                        print("Papers with same title, don't have same DOIs:<br />")
                        print("  Title: " + paper.title + "<br />")
                        print("  Conflicting DOIs: " + doi + ", " + paper.doi + "<br />")

    def verifyConsistent1stAuthor(self):
        """
        Verify that any papers that we think are the same, either have the same
        first author last name, or no author specified.
        """
        for lowerTitle, papersWithTitle in self.byTitleLower.items():
            author1 = None
            for paper in papersWithTitle:
                firstAuthorForThisPaper = paper.getFirstAuthorLastNameLower()
                if firstAuthorForThisPaper:
                    if not author1:
                        author1 = firstAuthorForThisPaper
                    elif author1 != firstAuthorForThisPaper:
                        print("Papers with same title, don't have same first authors: <br />")
                        print("  Title: " + paper.title + "<br />")
                        print("  Conflicting authors: <br />")
                        print(u"    Author A: '" + author1 + u"' <br />")
                        print(u"    Author B: '" + firstAuthorForThisPaper + u"' <br />")

        
        
