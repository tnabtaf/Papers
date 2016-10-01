#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Module to access a CiteULike library.

import json
import re

class CiteULikeEntry(object):
    '''
    Provide access to a CiteULike JSON Entry
    '''

    def __init__(self, CUL_JSON):
        """
        Given a python encoded JSON description of a paper from CiteULike,
        create a python object for it.
        """
        self.culJson = CUL_JSON
        #print("======================================")
        #print(CUL_JSON)
        return

    def getTitle(self):
        return(self.culJson["title"])

    def getTitleLower(self):
        """
        Also strips out whitespace and non-alphanumeric character
        """
        return(re.sub(r'\W+', '',  self.culJson["title"]).lower())

    def getCulUrl(self):
        return(self.culJson["href"])

    def getDoi(self):
        return(self.culJson.get("doi"))

    def getJournalName(self):
        jrnlName = ""
        if self.getPublicationType() == "JOUR" and "journal" in self.culJson:
            jrnlName = re.sub('\n\s*', ' ', self.culJson["journal"])
        return(jrnlName)

    def getPublicationType(self):
        return(self.culJson.get("type"))
            
    def getAuthors(self):
        return(self.culJson.get("authors"))

    def getFirstAuthorLastName(self):
        authors = self.getAuthors()
        if authors:
            return(authors[0].split()[-1])
        else:
            return None

    def getFirstAuthorLastNameLower(self):
        firstAuthor = self.getFirstAuthorLastName()
        if firstAuthor:
            firstAuthor = firstAuthor.lower()
        return firstAuthor

    def getYear(self):
        """
        Return year as a 4 digit string.
        """
        published = self.culJson.get("published")
        if published:
            year = published[0]
        else:
            year = "unknown"
        return year

    def getTags(self):
        """
        Return the ordered list of the tags associated with this paper.
        """
        tags = self.culJson.get("tags")
        if not tags:
            tags = []
        return tags

        
    def debugPrint(self, descr="", indent=""):
        print(indent + "DEBUG: CiteULikeEntry: " + descr)
        print(indent + "  Title: " + self.getTitle())
        print(indent + "  Authors: ", self.getAuthors())
        print(indent + "  1st Author Last Name: " + self.getFirstAuthorLastName())
        print(indent + "  Journal Name: " + self.getJournalName())
        print(indent + "  CUL URL: " + self.getCulUrl())
        print(indent + "  DOI: " + self.getDoi())
        print(indent + "  DONE")
        return(None)


class CiteULikeLibrary(object):
    """
    Encapsulates a CiteULike library in an accessible structure.
    """
    def __init__(self, culSource):

        """
        Given either a CiteULike JSON file, or a URL from with that file can be
        obtained.  Process that into a library that can be used by the caller.
        """
        try:
            culFile = open(culSource, "r")
            self.fileName = culSource
            
        except IOError as err:
            # not a file, let's hope it's a URL.
            print("Heh, heh.  Need write code to deal with URL's as sources.")
            raise

        self.culJson = json.load(culFile)   # get whole file at once.

        self.byTitleLower = {}
        self.byDoi = {}
        self.by1stAuthorLastNameLower = {}

        for culPub in self.culJson:
            culEntry = CiteULikeEntry(culPub)
            # print(culPub)

            titleLower = culEntry.getTitleLower()
            if titleLower not in self.byTitleLower:
                self.byTitleLower[titleLower] = []
            else:
                print("Title already in library<br />")
                print("  ", culEntry.getTitle(), "<br />")
                print("    ", culEntry.getDoi(), "<br />")
                print("    ", self.byTitleLower[titleLower][0].getDoi(), "<br />")
            self.byTitleLower[titleLower].append(culEntry)
            doi = culEntry.getDoi()
            if doi:
                self.byDoi[doi] = culEntry
            authorLower = culEntry.getFirstAuthorLastNameLower()
            if authorLower not in self.by1stAuthorLastNameLower:
                self.by1stAuthorLastNameLower[authorLower] = {}
            self.by1stAuthorLastNameLower[authorLower][titleLower] = culEntry

        culFile.close()

        return(None)


    def getByTitleLower(self, titleLower):
        return(self.byTitleLower.get(titleLower))

    def getByDoi(self, doi):
        return(self.byDoi.get(doi))

    def getBy1stAuthorLastNameLower(self, lastNameLower):
        return(self.by1stAuthorLastNameLower.get(lastNameLower))

    def allPapers(self):
        """
        A generator that returns all papers in the library, in no particular order.
        """
        for papers in self.byTitleLower.values():
            for paper in papers:
                yield paper
        raise StopIteration()

    def getPaperCount(self):
        """
        Return the total number of papers
        """
        return(len(self.culJson))

