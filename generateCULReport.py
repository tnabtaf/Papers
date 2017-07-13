#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Generate reports about the Galaxy CiteULike library.
# Reports are generated in both TSV and Markdown.
#


import argparse
import math
import titlecase
import urllib.parse
import CiteULike                          # CiteULike Handling

CUL_GROUP_ID = "16008"
CUL_GROUP_SEARCH = "http://www.citeulike.org/search/group?search=Search+library&group_id=" + CUL_GROUP_ID + "&q="
CUL_SEARCH_LOGICAL_AND = "+%26%26+"              # " && "
CUL_SEARCH_YEAR        = "year%3A"               # "year:"
CUL_SEARCH_TAG         = "tag%3A"                # "tag:"

CUL_GROUP_TAG_BASE_URL = "http://www.citeulike.org/group/" + CUL_GROUP_ID + "/tag/"




class FastCulLib(object):
    """
    Provides quick access to a citeulike library.
    """

    def __init__(self, culLib):
        """
        Given a CiteULike library, build quick index strucutures needed by
        reports.
        """
        self.culLib = culLib

        # These are replaced by frozensets at the end.
        byYear = {}          # unordered array of papers from that year
        byTag = {}           # value is unordered array of papers w/ tag
        byJournal= {}        # unordered list of papers in each journal

        sortedByJournal = [] # sorted by lower case journal name
        self.journalAlphaRank = {} # key is lower case Journal Name; value is alphabetized rank.
        
        for paper in culLib.allPapers():

            # Process Year
            year = paper.getYear()
            if year == "unknown":
                print("Year UNKNOWN", paper.culJson) # Fix these when you find them.
            if year not in byYear:
                byYear[year] = []
            byYear[year].append(paper)

            # Process tags
            tags = paper.getTags()                # every paper should have tags
            for tag in tags:
                if tag not in byTag:
                    byTag[tag] = []
                byTag[tag].append(paper)
            if len(tags) == 0:
                # should not happen, fix it when it happens.
                print("Paper missing tags", paper.getTitle(), paper.getCulUrl())

            # Process Journal
            jrnl = paper.getJournalName().lower()
            if jrnl:
                if jrnl not in byJournal:
                    byJournal[jrnl] = []
                    sortedByJournal.append(jrnl)
                byJournal[jrnl].append(paper)

        # create set versions
        self.byYear = {}
        for year in byYear:
            self.byYear[year] = frozenset(byYear[year])
        self.byTag = {}
        for tag in byTag:
            self.byTag[tag] = frozenset(byTag[tag])
        self.byJournal = {}
        for journal in byJournal:
            self.byJournal[journal] = frozenset(byJournal[journal])

        # create sorted list of Journal names
        sortedByJournal.sort()
        for idx in range(len(sortedByJournal)):
            self.journalAlphaRank[sortedByJournal[idx]] = idx
        
        return(None)

    def getYears(self):
        """
        Return a list of years that papers were published in, in chronological
        order.
        """
        return(sorted(self.byYear.keys()))

    def getTags(self):
        """
        Return an unordered list of tags that exist in this lib.
        """
        return(self.byTag.keys())

    def getJournals(self):
        """
        Return an unordered list of Journal names.
        """
        return(self.byJournal.keys())
        

    def getJournalTotalCount(self, journalName):
        """
        Return the total number of papers from this Journal.
        """
        return(len(self.getPapers(journal = journalName.lower())))


    def keySortTotalName(self, journalName):
        """
        Somehow make the Python 3 sort work.

        Try returning a floating point number with count
        """        
        return(self.getJournalTotalCount(journalName) - (self.journalAlphaRank[journalName] * 0.000001))
        
    def getJournalsByTotal(self):
        """
        Return a list of Journal names in descending order, sorted by total
        number of papers in each journal 
        """
        return(sorted (self.byJournal.keys(), key=self.keySortTotalName, reverse=True))

        
    def getPapers(self,
                  tag = None,
                  year = None,
                  journal = None,
                  startDate = None,
                  endDate = None):
        """
        Given any combination of tag, year, journal and/or startDate and endDate, 
        return the only the set of papers that have the sepcified combination of values.
        """
        sets = []
        if tag:
            sets.append(self.byTag[tag])
        if year:
            sets.append(self.byYear[year])
        if journal:
            sets.append(self.byJournal[journal])

        if len(sets) > 1:
            selected = sets[0]
            for restriction in sets[1:]:
                selected = selected.intersection(restriction)
        elif len(sets) == 1:
            selected = sets[0]
        else: # sets is empty 
            selected = frozenset(self.culLib.allPapers())

        # apply date selections if present
        if startDate or endDate:
            matchDates = []
            for paper in selected:
                inSoFar = True
                if startDate and paper.getEntryDate() < startDate:
                    inSoFar = False
                elif endDate and paper.getEntryDate() > endDate:
                    inSoFar = False
                if inSoFar:
                    matchDates.append(paper)

            selected = matchDates

        return(selected)


    
    def getPaperCount(self):
        return(self.culLib.getPaperCount())



def genMarkdownCountStyleBlue(numPapers):
    """
    Bigger counts get more emphasis.
    """
    style = ' style="text-align: right; '

    if numPapers == 0:
        style += 'color: #AAAAAA;'
    elif numPapers == 1:
        style += 'background-color: #f0f8ff;'
    elif numPapers == 2:
        style += 'background-color: #dcecf8;'
    elif numPapers <= 5:
        style += 'background-color: #c8d0f0;'
    elif numPapers <= 10:
        style += 'background-color: #b4c4e8;'
    elif numPapers <= 20:
        style += 'background-color: #a0b8e0;'
    elif numPapers <= 50:
        style += 'background-color: #8cacd8;'
    elif numPapers <= 100:
        style += 'background-color: #78a0d0; color: #ffffff'
    elif numPapers <= 200:
        style += 'background-color: #6494c8; color: #ffffff'
    elif numPapers <= 500:
        style += 'background-color: #5088c0; color: #ffffff'
    elif numPapers <= 1000:
        style += 'background-color: #3c7cb8; color: #ffffff'
    elif numPapers <= 2000:
        style += 'background-color: #2870b0; color: #ffffff'
    elif numPapers <= 5000:
        style += 'background-color: #1464a8; color: #ffffff'
    elif numPapers <= 10000:
        style += 'background-color: #0058a0; color: #ffffff'
    style += '" '

    return style


def genHtmlCountStyle(numPapers):
    """
    Bigger counts get more emphasis.
    """
    style = ' style="text-align: right; '

    if numPapers == 0:
        style += 'color: #ffffff;'
    elif numPapers == 1:
        style += 'background-color: #f8fff8;'
    elif numPapers == 2:
        style += 'background-color: #f0fff0;'
    elif numPapers <= 5:
        style += 'background-color: #e8ffe8;'
    elif numPapers <= 10:
        style += 'background-color: #e0ffe0;'
    elif numPapers <= 20:
        style += 'background-color: #d8ffd8;'
    elif numPapers <= 50:
        style += 'background-color: #c8ffc8;'
    elif numPapers <= 100:
        style += 'background-color: #b8f0b8;'
    elif numPapers <= 200:
        style += 'background-color: #a8e8a8;'
    elif numPapers <= 500:
        style += 'background-color: #98e098;'
    elif numPapers <= 1000:
        style += 'background-color: #88d888;'
    elif numPapers <= 2000:
        style += 'background-color: #78d078;'
    elif numPapers <= 5000:
        style += 'background-color: #68c868;'
    elif numPapers <= 10000:
        style += 'background-color: #58c058;'
    style += '" '

    return style


def genHtmlTagYearReport(fastCulLib):
    """
    Generate a papers by tag and year report in HTML markup.
    Report is returned as a multi-line string.
    """
    # Preprocess. Need to know order of tags and years.
    tags = fastCulLib.getTags()
    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in tags:
        nPapersWTag[tag] = len(fastCulLib.getPapers(tag=tag))

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    report = []                # now have everything we need; generate report
    
    # generate header
    report.append('<table class="table">\n')
    report.append('  <tr>\n')
    report.append('    <th rowspan="2"> Year </th>\n')
    report.append('    <th colspan="' + str(len(tags)) + '"> Tags </th>\n')
    report.append('    <th rowspan="2"> # </th>\n')
    report.append('  </tr>\n')
    
    report.append('  <tr>\n')
    for tag in tagsInCountOrder:
        report.append(
            '    <th> <a href="' + CUL_GROUP_TAG_BASE_URL + tag + '">' + tag + '</a> </th>\n')
    report.append('  </tr>\n')

    # generate numbers per year
    for year in fastCulLib.getYears():  # years are listed chronologically
        report.append('  <tr>\n')
        nPapersThisYear = len(fastCulLib.getPapers(year=year))
        report.append('    <th> ' + year + ' </th>\n')
        for tag in tagsInCountOrder:
            papersForTagYear = fastCulLib.getPapers(tag=tag, year=year)
            if papersForTagYear:
                style = genHtmlCountStyle(len(papersForTagYear))
                count = (
                    '<a href="' + CUL_GROUP_SEARCH +
                    CUL_SEARCH_YEAR + year +
                    CUL_SEARCH_LOGICAL_AND +
                    CUL_SEARCH_TAG + tag +
                    '">' + str(len(papersForTagYear)) + '</a>')
            else:
                style = ""
                count = ""
            report.append('    <td ' + style + '> ' + count + ' </td>\n')
        yearCountStyle = genHtmlCountStyle(nPapersThisYear)
        report.append(
            '    <td ' + yearCountStyle + '> ' +
            '<a href="' + CUL_GROUP_SEARCH + CUL_SEARCH_YEAR + year + '">' + 
            str(nPapersThisYear) + '</a> </td>\n')
        report.append('  </tr>\n')

    # generate total line at bottom
    report.append('  <tr>\n')
    report.append('    <th> Total </th>\n')
    for tag in tagsInCountOrder:
        tagCountStyle =  genHtmlCountStyle(nPapersWTag[tag])
        report.append(
            '    <th ' + tagCountStyle + '> ' +
            '<a href="' + CUL_GROUP_TAG_BASE_URL + tag + '">' +
            str(nPapersWTag[tag]) + '</a> </th>\n')

    allPapersCount = len(fastCulLib.getPapers())
    allPapersStyle = genHtmlCountStyle(allPapersCount)
    report.append('    <th ' + allPapersStyle + '> ' + str(allPapersCount) + ' </th>\n')
    report.append('  </tr>\n')
    report.append('</table>\n')
    
    return(u"".join(report))


def genHtmlYearTagReport(fastCulLib):
    """
    Generate a papers by year and tag report in HTML markup.
    Report is returned as a multi-line string.
    """
    # Preprocess. Need to know order of tags and years.
    tags = fastCulLib.getTags()
    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in tags:
        nPapersWTag[tag] = len(fastCulLib.getPapers(tag=tag))

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    report = []                # now have everything we need; generate report
    
    # generate header
    report.append('<table class="table">\n')
    report.append('  <tr>\n')
    report.append('    <th> Tag </th>\n')

    for year in fastCulLib.getYears(): # years are listed chronologically
        report.append('    <th> ' + year + ' </th>\n')
    report.append('    <th> # </th>\n')
    report.append('  </tr>\n')

    # generate numbers per tag/year
    for tag in tagsInCountOrder:
        report.append('  <tr>\n')
        report.append('    <th> <a href="' + CUL_GROUP_TAG_BASE_URL + tag + '"> '
                      + tag + '</a></th>\n')
        for year in fastCulLib.getYears():
            papersForTagYear = fastCulLib.getPapers(tag=tag, year=year)
            if papersForTagYear:
                style = genHtmlCountStyle(len(papersForTagYear))
                count = str(len(papersForTagYear))
            else:
                style = ""
                count = ""
            report.append('    <td ' + style + '> ' + count + ' </td>\n')

        tagCountStyle = genHtmlCountStyle(nPapersWTag[tag])
        report.append('    <th ' + tagCountStyle + '> ' + str(nPapersWTag[tag]) + " </th>\n")
        report.append('  </tr>\n')
 
    # generate total line at bottom
    report.append('  <tr>\n')
    report.append('    <th> Total </th>\n')
    for year in fastCulLib.getYears():
        nPapersThisYear = len(fastCulLib.getPapers(year=year))
        papersThisYearStyle = genHtmlCountStyle(nPapersThisYear)
        report.append('    <th ' + papersThisYearStyle + '>' + str(nPapersThisYear) + ' </th>\n')

    totalPapers = len(fastCulLib.getPapers())
    totalPapersStyle = genHtmlCountStyle(totalPapers)
    report.append('    <th ' + totalPapersStyle + '> ' +
                  str(totalPapers) + ' </th>\n')
    report.append('  </tr>\n')
    report.append('</table>\n')

    return(u"".join(report))



    
def genTsvJournalReport(fastCulLib):
    """
    Generate a papers by by Journal and Year report in TSV.
    Report is returned as a multi-line string.
    """
    # I don't think we need to sort it.  The output is TSV and isn't that what
    # spreadsheets are for?

    report = []
    years = fastCulLib.getYears()
    
    # generate header
    report.append('Journal\t')
    for year in years:  # years are listed chronologically
        report.append(year + '\t')
    report.append('Total\n')

    # spew numbers for each journal
    for journalName in fastCulLib.getJournals():
        report.append(journalName + '\t')
        for year in years:
            report.append(str(len(fastCulLib.getPapers(journal=journalName,
                                                       year=year))) + '\t')
        report.append(str(len(fastCulLib.getPapers(journal=journalName))) + '\n')

    # gernate footer
    report.append('TOTALS\t')
    for year in years:  # years are listed chronologically
        report.append(str(len(fastCulLib.getPapers(year=year))) + '\t')
    report.append(str(fastCulLib.getPaperCount()) + '\n')

    return(u"".join(report).encode('utf-8'))


def genHtmlJournalReport(fastCulLib):
    """
    Generate a papers by by Journal and Year report in HTML Bootstrap markup.
    Report is returned as a multi-line string.
    """

    report = []
    years = fastCulLib.getYears()
    
    # generate header
    report.append('<table class="table">\n')
    report.append('  <tr>\n')
    report.append('    <th> </th>\n')
    report.append('    <th> Journal </th>\n')
    for year in years:  # years are listed chronologically
        report.append("    <th> " + year + ' </th>\n')
    report.append("    <th> Total </th>\n")
    report.append("    <th> Rank </th>\n")
    report.append("  </tr>\n")

    # spew numbers for each journal
    journalNum = 1
    journalRank = 0
    previousScore = 0
    
    for journalName in fastCulLib.getJournalsByTotal():
        # Generate link to journal in CUL.
        culGroupSearch = CUL_GROUP_SEARCH + urllib.parse.quote('journal:"' +journalName + '"')
        report.append('  <tr>\n')
        report.append('    <td style="text-align: right;"> ' + str(journalNum) + ' </td>') 
        report.append('    <td> <strong> <a href="' + culGroupSearch + '">'
            + titlecase.titlecase(journalName) + "</a></strong> </td>\n")
            
        for year in years:
            numPapers = len(fastCulLib.getPapers(journal=journalName, year=year))
            style = genHtmlCountStyle(numPapers)
            report.append('    <td ' + style + "> " + str(numPapers) + ' </td>\n')

        # Add total for journal across all years.
        journalTotalPapers = fastCulLib.getJournalTotalCount(journalName)
        journalTotalStyle = genHtmlCountStyle(journalTotalPapers)
        report.append("    <th " + journalTotalStyle + "> " +
                      str(journalTotalPapers) + " </th>\n")

        # figure out rank
        if previousScore != journalTotalPapers:
            journalRank = journalNum
            previousScore = journalTotalPapers
        report.append('    <td style="text-align: right;"> ' + str(journalRank) + ' </td>')
        report.append('  </tr>\n')
        journalNum += 1

    # gernate footer
    report.append('  <tr>\n')
    report.append('    <th> </th>\n')
    report.append('    <th> TOTALS </th>\n')
    for year in years:  # years are listed chronologically
        yearTotal = len(fastCulLib.getPapers(year=year))
        yearStyle = genHtmlCountStyle(yearTotal)
        report.append('    <th ' + yearStyle + "> " + str(yearTotal) + ' </th>\n')

    totalPapers = fastCulLib.getPaperCount()
    totalStyle = genHtmlCountStyle(totalPapers)
    report.append("    <th " + totalStyle + "> " + str(totalPapers) + "</th>\n")
    report.append('    <th> </th>\n')
    report.append("  </tr>\n")
    report.append("</table>\n")
    
    return(u"".join(report))


def genHtmlTagsDateRangeReport(fastCulLib, startDate, endDate):
    """
    report how many papers have each tag that were enterred into CUL during
    a given date range.

    Report is returned as a multi-line string.

    Can see a couple of ways to do this:
    1. Only report tags that have papers
    2. Report all tags, even the ones with no papers.
    3. Order tags from most to least papers
    4. Order tags alphabetically
    5. Present tags in a multi-column table
    6. Present tabs in 2 column table: count, and tag.

    Went with #1, #3, and #5.  An earlier version went with #1, #3, and #6.
    """

    N_TAG_COLUMN_GROUPS = 4         # create report with n tags and n counts across

    # get total # of papers during time range
    nTotalPapers = len(fastCulLib.getPapers(startDate=startDate, endDate=endDate))
    
    # Preprocess. Need to know order of tags and years.
    tags = fastCulLib.getTags()
    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in tags:
        nPapersWTag[tag] = len(fastCulLib.getPapers(tag=tag, startDate=startDate, endDate=endDate))

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    # generate numbers per tag
    tagMarkup = []
    for tag in tagsInCountOrder:
        if nPapersWTag[tag] > 0:
            tagMarkup.append(
                '    <td style="text-align: right"> ' + str(nPapersWTag[tag]) + ' </td>\n' +
                '    <td> <a href="' + CUL_GROUP_TAG_BASE_URL + tag + '">' + tag + '</a></td>\n')

    # Have markup for individual tags; now decide how many go in each column
    nTagsToReport = len(tagMarkup)
    nTagsPerCol = int(math.ceil(nTagsToReport / N_TAG_COLUMN_GROUPS))

    report = []              # now have everything we need; generate report

    # generate header
    report.append('\n' + str(nTotalPapers) + ' papers added between ' +
                  startDate + ' and ' + endDate +'.\n\n') # markdown! 
    report.append(
        '<table class="table">\n' +
        '  <tr>\n')
    for colGroup in range(N_TAG_COLUMN_GROUPS):
        report.append(
            '    <th> # </th>\n' +
            '    <th> Tag </th>\n')
        if colGroup < N_TAG_COLUMN_GROUPS - 1:
            report.append('    <td rowspan="' + str(nTagsPerCol + 1) + '"> </td>')
    report.append('  </tr>\n')

    # add tags & counts
    for rowIdx in range(nTagsPerCol):
        report.append('  <tr>\n')
        for colGroup in range(N_TAG_COLUMN_GROUPS):
            tagIdx = (rowIdx * N_TAG_COLUMN_GROUPS) + colGroup
            if tagIdx < nTagsToReport:
                report.append(tagMarkup[tagIdx])
            else:
                report.append(
                    '    <td> </td>\n' +
                    '    <td> </td>\n')
        report.append('  </tr>\n')
 
    report.append('</table>\n')

    return(u"".join(report))


def genMarkdownTagsDateRangeReport(fastCulLib, startDate, endDate):
    """
    report how many papers have each tag that were enterred into CUL during
    a given date range.

    Report is returned as a multi-line string.

    Can see a couple of ways to do this:
    1. Only report tags that have papers
    2. Report all tags, even the ones with no papers.
    3. Order tags from most to least papers
    4. Order tags alphabetically
    5. Present tags in a multi-column table
    6. Present tabs in 2 column table: count, and tag.

    Went with #1, #3, and #5.  An earlier version went with #1, #3, and #6.
    """

    N_TAG_COLUMN_GROUPS = 4         # create report with n tags and n counts across

    # get total # of papers during time range
    nTotalPapers = len(fastCulLib.getPapers(startDate=startDate, endDate=endDate))
    
    # Preprocess. Need to know order of tags and years.
    tags = fastCulLib.getTags()
    # Count number of papers with each tag
    nPapersWTag = {}
    for tag in tags:
        nPapersWTag[tag] = len(fastCulLib.getPapers(tag=tag, startDate=startDate, endDate=endDate))

    # sort tags by paper count, max first
    tagsInCountOrder = [tag for tag in
                        sorted(nPapersWTag.keys(),
                               key=lambda keyValue: - nPapersWTag[keyValue])]

    # generate numbers per tag
    tagMarkup = []
    for tag in tagsInCountOrder:
        if nPapersWTag[tag] > 0:
            tagMarkup.append(
                '| ' + str(nPapersWTag[tag]) +
                ' | [' + tag + '](' + CUL_GROUP_TAG_BASE_URL + tag + ') | ')

    # Have markup for individual tags; now decide how many go in each column
    nTagsToReport = len(tagMarkup)
    nTagsPerCol = int(math.ceil(nTagsToReport / N_TAG_COLUMN_GROUPS))

    report = []              # now have everything we need; generate report

    # generate header
    report.append('\n' + str(nTotalPapers) + ' papers added between ' +
                  startDate + ' and ' + endDate +'.\n\n') # markdown! 

    headerLine = []              
    for colGroup in range(N_TAG_COLUMN_GROUPS):
        report.append(
            '| # | Tag | ')
        headerLine.append('| ---: | --- |')
        if colGroup < N_TAG_COLUMN_GROUPS - 1:
            headerLine.append(' --- ')
    report.append("\n")
    report.append("".join(headerLine) + "\n")

    # add tags & counts
    for rowIdx in range(nTagsPerCol):
        for colGroup in range(N_TAG_COLUMN_GROUPS):
            tagIdx = (rowIdx * N_TAG_COLUMN_GROUPS) + colGroup
            if tagIdx < nTagsToReport:
                report.append(tagMarkup[tagIdx])
            else:
                report.append('| | | ')
        report.append('\n')
 
    return(u"".join(report))



def argghhs():
    """
    Process and provide access to command line arguments.
    """

    argParser = argparse.ArgumentParser(
        description="Generate reports for the CiteULike Galaxy library.")
    argParser.add_argument(
        "-c", "--cullib", required=True,
        help="JSON formatted file containing CiteUlike Library; obtained by going to http://www.citeulike.org/json/group/16008")
    argParser.add_argument(
        "--tagyear", required=False, action="store_true",
        help="Produce table showing number of papers with each tag, each year.")
    argParser.add_argument(
        "--yeartag", required=False, action="store_true",
        help="Produce table showing number of papers with each year, each tag.")
    argParser.add_argument(
        "--journalyear", required=False, action="store_true",
        help="Produce table showing number of papers in different journals, each year.")
    argParser.add_argument(
        "--tagcountdaterange", required=False, action="store_true",
        help="Produce table showing number of papers that were tagged with each tag during a given time perioud. " +
             "--startdate and --enddate parameters are required if tagcountdaterange is specified.")
    argParser.add_argument(
        "--startdate", required=False,
        help="tagcountdaterange will report on papers with entry dates greater than or equal to this date.  " +
             "Example: 2016-12-29")
    argParser.add_argument(
        "--enddate", required=False,
        help="tagcountdaterange will report on papers with entry dates less than or equal to this date.  " +
             "Example: 2017-01-29")
    argParser.add_argument(
        "--markdown", required=False, action="store_true",
        help="Produce report(s) using Markdown")
    argParser.add_argument(
        "--html", required=False, action="store_true",
        help="Produce report(s) using HTML")
    argParser.add_argument(
        "--tsv", required=False, action="store_true", 
        help=("Produce report(s) in TSV format"))

    return(argParser.parse_args())


        
# =============================================================
# MAIN

args = argghhs()                          # process command line arguments
# print str(args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.cullib)

fastCulLib = FastCulLib(culLib)

if args.tagyear:

    # Generate them reports

    # options are to have one routine per report/format combo, or create a Markdown
    # report, or a tsv report and then have their separate methods do the dirty
    # work. Try that.

    # report showing papers by tag by year requested.
    if args.html:
        # generate a tag year report in Markdown format.
        htmlReport = genHtmlTagYearReport(fastCulLib)
        print(htmlReport)
    if args.tsv:
        # generate tag year data in a tab delimited file
        tsvReport = genTsvTagYearReport(fastCulLib)
        print(tsvReport)

if args.yeartag:

    # Generate them reports

    # options are to have one routine per report/format combo, or create a Markdown
    # report, or a tsv report and then have their separate methods do the dirty
    # work. Try that.

    # report showing papers by tag by year requested.
    if args.html:
        # generate a tag year report in Markdown format.
        htmlReport = genHtmlYearTagReport(fastCulLib)
        print(htmlReport)


if args.journalyear:
    # Count how many papers appeared in each jounal in each year.
    # Generate TSV here?  Need to sort it somehow.  X axis should be year.
    # Y axis Journal.  Put the journal with the most all time pubs at the top
    # And also include publisher as we care about BMC.

    if args.tsv:
        journalReport = genTsvJournalReport(fastCulLib)
        print(journalReport)
    
    if args.html:
        journalReport = genHtmlJournalReport(fastCulLib)
        print(journalReport)
    
if args.tagcountdaterange:
    # Generate a table of tags showing how many papers were tagged with each
    # during a given date range.

    # This report is used in the monthly newsletters

    if args.markdown:
        tagsDateRangeReport = genMarkdownTagsDateRangeReport(fastCulLib, args.startdate, args.enddate)
        print(tagsDateRangeReport)
    
    if args.html:
        tagsDateRangeReport = genHtmlTagsDateRangeReport(fastCulLib, args.startdate, args.enddate)
        print(tagsDateRangeReport)

        
