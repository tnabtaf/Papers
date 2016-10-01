#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Generate reports about the Galaxy CiteULike library.
# Reports are generated in both TSV and MoinMoin markup.
#


import argparse
import titlecase
import CiteULike                          # CiteULike Handling

CUL_GROUP_ID = "16008"
CUL_GROUP_SEARCH = "http://www.citeulike.org/search/group?search=Search+library&group_id=" + CUL_GROUP_ID + "&q="

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

        
    def getJournalsByTotal(self):
        """
        Return a list of Journal names in descending order, sorted by total
        number of papers in each journal 
        """
        return(sorted (self.byJournal.keys(), key=lambda jrnlName: -self.getJournalTotalCount(jrnlName)))

        
    def getPapers(self,
                  tag = None,
                  year = None,
                  journal = None):
        """
        Given any combination of tag, year and.or journal, return the only the
        set of papers that have the sepcified combination of values.
        """
        sets = []
        if tag:
            sets.append(self.byTag[tag])
        if year:
            sets.append(self.byYear[year])
        if journal:
            sets.append(self.byJournal[journal])

        if len(sets) == 0:
            return(frozenset(self.culLib.allPapers()))
        elif len(sets) == 1:
            return(sets[0])
        else:
            narrowed = sets[0]
            for restriction in sets[1:]:
                narrowed = narrowed.intersection(restriction)
            return(narrowed)

    def getPaperCount(self):
        return(self.culLib.getPaperCount())


def genMoinTagYearReport(fastCulLib):
    """
    Generate a papers by tag and year report in MoinMoin markup.
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
    report.append('||<|2 class="th"> Year ' +
                  '||<-' + str(len(tags)) + ' class="th"> Tags ||' +
                  '||<|2 class="th"> # ||\n')

    for tag in tagsInCountOrder:
        report.append('||<class="th"> ' + tag + ' ')
    report.append('||\n')

    # generate numbers per year
    for year in fastCulLib.getYears():  # years are listed chronologically
        nPapersThisYear = len(fastCulLib.getPapers(year=year))
        report.append('||<class="th"> ' + year + ' ')
        for tag in tagsInCountOrder:
            papersForTagYear = fastCulLib.getPapers(tag=tag, year=year)
            if papersForTagYear:
                style = genMoinCountStyle(len(papersForTagYear))
                count = str(len(papersForTagYear))
            else:
                style = ""
                count = ""
            report.append('||' + style + count + ' ')
        report.append('||<)> ' + str(nPapersThisYear) + ' ||\n')

    # generate total line at bottom
    report.append('||<class="th"> Total ')
    for tag in tagsInCountOrder:
        report.append('||<) class="th"> ' + str(nPapersWTag[tag]) + ' ')
    report.append(' ||<) class="th"> ' +
                  str(len(fastCulLib.getPapers())) + ' ||\n')

    return(u"".join(report))


def genMoinYearTagReport(fastCulLib):
    """
    Generate a papers by year and tag report in MoinMoin markup.
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
    report.append('||<class="th"> Tag ')

    for year in fastCulLib.getYears(): # years are listed chronologically
        report.append('||<class="th"> ' + year + ' ')
    report.append('||<class="th"> # ||\n')

    # generate numbers per tag/year
    for tag in tagsInCountOrder:  
        report.append('||<class="th"> [[' + CUL_GROUP_TAG_BASE_URL + tag + "|"
                      + tag + ']] ')
        for year in fastCulLib.getYears():
            papersForTagYear = fastCulLib.getPapers(tag=tag, year=year)
            if papersForTagYear:
                style = genMoinCountStyle(len(papersForTagYear))
                count = str(len(papersForTagYear))
            else:
                style = ""
                count = ""
            report.append('||' + style + count + ' ')
        report.append("||<)> '''" + str(nPapersWTag[tag]) + "''' ||\n")
 
    # generate total line at bottom
    report.append('||<class="th"> Total ')
    for year in fastCulLib.getYears():
        nPapersThisYear = len(fastCulLib.getPapers(year=year))
        report.append('||<) class="th"> ' + str(nPapersThisYear) + ' ')
    report.append(' ||<) class="th"> ' +
                  str(len(fastCulLib.getPapers())) + ' ||\n')

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


def genMoinCountStyle(numPapers):
    """
    Bigger counts get more emphasis.
    """
    style = '<) '

    if numPapers == 0:
        style += 'style="color: #AAAAAA;"> '
    elif numPapers == 1:
        style += 'style="background-color: #dddddd;"> '
    elif numPapers <= 5:
        style += 'style="background-color: #cfe2f3;"> '
    elif numPapers <= 10:
        style += 'style="background-color: #9fc5e8;"> '
    elif numPapers <= 20:
        style += 'style="background-color: #6fa8dc;"> '
    elif numPapers <= 50:
        style += 'style="background-color: #3d85c6; color: #ffffff"> '
    elif numPapers <= 100:
        style += 'style="background-color: #2d65b6; color: #ffffff"> '
    elif numPapers <= 500:
        style += 'style="background-color: #1d45a6; color: #ffffff"> '
    else:
        style += '> '

    return style

        
def genMoinJournalReport(fastCulLib):
    """
    Generate a papers by by Journal and Year report in MoinMoin markup.
    Report is returned as a multi-line string.
    """

    report = []
    years = fastCulLib.getYears()
    
    # generate header
    report.append('||<rowclass="th"> Journal || ')
    for year in years:  # years are listed chronologically
        report.append(year + ' || ')
    report.append(' Total ||\n')

    # spew numbers for each journal
    for journalName in fastCulLib.getJournalsByTotal():
        # Generate link to journal in CUL.
        culGroupSearch = CUL_GROUP_SEARCH + 'journal:"' + journalName + '"'
        report.append("|| ''[[" + culGroupSearch + "|"
                      + titlecase.titlecase(journalName) +
                      "]]'' ||")
        for year in years:
            numPapers = len(fastCulLib.getPapers(journal=journalName, year=year))
            style = genMoinCountStyle(numPapers)
            report.append(style +
                          str(len(fastCulLib.getPapers(journal=journalName,
                                                       year=year))) + ' ||')
        report.append("<)> '''" +
                      str(fastCulLib.getJournalTotalCount(journalName)) + "''' ||\n'")

    # gernate footer
    report.append('||>class="th"> TOTALS ||<)> ')
    for year in years:  # years are listed chronologically
        report.append(str(len(fastCulLib.getPapers(year=year))) + ' ||<)> ')
    report.append(" ||<)> '''" + str(fastCulLib.getPaperCount()) + "''' ||\n")

    return(u"".join(report).encode('utf-8'))



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
        "--moin", required=False, action="store_true",
        help="Produce report(s) using MoinMoin markup")
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

    # options are to have one routine per report/format combo, or create a Moin
    # report, or a tsv report and then have their separate methods do the dirty
    # work. Try that.

    # report showing papers by tag by year requested.
    if args.moin:
        # generate a tag year report in MoinMoin format.
        moinReport = genMoinTagYearReport(fastCulLib)
        print(moinReport)
    if args.tsv:
        # generate tag year data in a tab delimited file
        tsvReport = genTsvTagYearReport(fastCulLib)
        print(tsvReport)

if args.yeartag:

    # Generate them reports

    # options are to have one routine per report/format combo, or create a Moin
    # report, or a tsv report and then have their separate methods do the dirty
    # work. Try that.

    # report showing papers by tag by year requested.
    if args.moin:
        # generate a tag year report in MoinMoin format.
        moinReport = genMoinYearTagReport(fastCulLib)
        print(moinReport)


if args.journalyear:
    # Count how many papers appeared in each jounal in each year.
    # Generate TSV here?  Need to sort it somehow.  X axis should be year.
    # Y axis Journal.  Put the journal with the most all time pubs at the top
    # And also include publisher as we care about BMC.

    if args.tsv:
        journalReport = genTsvJournalReport(fastCulLib)
        print(journalReport)
    
    if args.moin:
        journalReport = genMoinJournalReport(fastCulLib)
        print(journalReport)
    
