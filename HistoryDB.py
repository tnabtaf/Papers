#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Keep track of and use information from out previous runs.  The DB is just a tab delimited file.

import csv

import Matchup

NEW      = "new"
TITLE    = "title"
AUTHORS  = "authors"
DOI      = "doi"
COMMENTS = "comments"

COLUMNS = [NEW, TITLE, AUTHORS, DOI, COMMENTS]


class HistoryDB(object):
    def __init__(self, csvInFileName):

        self.byTitleLower = {}
        self.byDoi = {}
        csvIn = open(csvInFileName, "r")
        csvReader = csv.DictReader(csvIn, fieldnames=COLUMNS, dialect="excel-tab")
        for row in csvReader:
            
            self.byTitleLower[row[TITLE].lower()] = row
            self.byDoi[row[DOI]] = row

        csvIn.close()
        
        return None

    def getByTitleLower(self, lowerTitle):
        """
        Returns None if we don't know about this title.
        """
        return(self.byTitleLower.get(lowerTitle))

        
    def getByDoi(self, doi):
        """
        Returns None if we don't know about this DOI.
        """
        return(self.byDoi.get(doi))

    def getEntryGivenMatchup(self, matchup):
        """
        Use information in a matchup to locate that paper's comments in the
        history DB.  Can use DOI or lower title
        """
        entry = None
        doi = matchup.getDoiFromPapers()
        if doi:
            entry = self.getByDoi(doi)
        else:
            entry = self.getByTitleLower(matchup.lowerTitle)
        return(entry)


def writeHistory(matchups, sortedTitles, csvOutFileName, priorHistoryDb):
    
    csvOut = open(csvOutFileName, "w")
    csvWriter = csv.DictWriter(csvOut, fieldnames=COLUMNS, dialect="excel-tab")
    csvWriter.writeheader()

    for title in sortedTitles:
        matchup = matchups[title]
        row = {}
        newPaper = not matchup.culEntries
        if newPaper:
            row[NEW] = 1
        else:
            row[NEW] = 0

        row[TITLE]   = matchup.papers[0].title
        row[AUTHORS] = matchup.papers[0].authors
        row[DOI]     = Matchup.getDoiFromPaperList(matchup.papers)
        priorHistoryEntry = priorHistoryDb.getEntryGivenMatchup(matchup)
        if priorHistoryEntry:
            row[COMMENTS] = priorHistoryEntry[COMMENTS]
        csvWriter.writerow(row)

    return None
