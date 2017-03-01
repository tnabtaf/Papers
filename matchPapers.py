#!/usr/local/bin/python3
# -*- coding: utf-8 -*-
#
# Program to compare newly reported publications with a library of pubs.
# For each new pub
#   determine if it's already in the publication lib or not.
#   If it's not, generate a bunch of links that will make it easier to add
#   the pub to the library.
#
# This doesn't modify the library at all.  It merely makes it easier for the human
# operator to add the pubs.


import argparse
import getpass

import Papers
import CiteULike                          # CiteULike Handling
import Matchup                            # Matchup newly reported papers & what's in CUL
import HistoryDB                          # record what was found in this run
import IMAP                               # Nasty Email handling.
import WOS                                # web of science
import ScienceDirect                      # Science Direct reports
import Springer                           # Used to link to Springer papers
import GoogleScholar
import MyNCBI
import Wiley                              # Wileay Online Library Saved Search Alerts

SOURCE_MAPPING = {
    "sciencedirect": ScienceDirect,
    "webofscience":  WOS,
    #"springer":      Springer,            # Don't get any reports from Springer
    "googlescholar": GoogleScholar,
    "myncbi":        MyNCBI,
    "wiley":         Wiley
    }

PAPERS_MAILBOX = "Papers"                 # Should be a run time param
        
        
class Argghhs(object):
    """
    Process and provide access to command line arguments.
    """

    def __init__(self):
        argParser = argparse.ArgumentParser(
            description="Given a list of data sources for papers, generate a report showing which papers are possibly new, and which papers we already have in CiteULike.")
        argParser.add_argument(
            "-c", "--cullib", required=True,
            help="JSON formatted file containing CiteUlike Library; obtained by going to http://www.citeulike.org/json/group/16008")
        argParser.add_argument(
            "-e", "--email", required=True,
            help="Email account to pull notifications from")
        argParser.add_argument(
            "--sentsince", required=True,
            help=("Only look at email sent after this date." +
                    " Format: DD-Mon-YYYY.  Example: 01-Dec-2014."))
        argParser.add_argument(
            "--sentbefore", required=False,
            help=("Optional. Only look at email sent before this date." +
                    " Format: DD-Mon-YYYY.  Example: 01-Jan-2015."))
        argParser.add_argument(
            "--sources", required=True,
            help="Which alert sources to process. Is either 'all' or comma-separated list: sciencedirect,webofscience,myncbi,wiley,googlescholar")
        argParser.add_argument(
            "--historyin", required=False,
            help="Read in history of previous run. Tells you what you've seen before.")
        argParser.add_argument(
            "--historyout", required=False,
            help="Create a history of this run in CSV format as well.")
        argParser.add_argument(
            "--verify1stauthors", required=False,
            action="store_true", 
            help="When we have a paper from more than one source, check that" +
                 " the two sources have the same first author.  This is noisy.")
        self.args = argParser.parse_args()
        
        # split comma separated list of sources
        self.sources = self.args.sources.split(",")
        
        return(None)

    def getCulLib(self):
        return self.args.cullib

    def getEmailAddress(self):
        return self.args.email

    def getSentSince(self):
        return self.args.sentsince

    def getSentBefore(self):
        return self.args.sentbefore

    def getSources(self):
        # Returns an array of citation sources
        return self.sources

    def getHistoryIn(self):
        return self.args.historyin

    def getHistoryOut(self):
        return self.args.historyout
    
# MAIN

args = Argghhs()                          # process command line arguments
# print str(args.args)

# create database from CiteULike Library.
culLib = CiteULike.CiteULikeLibrary(args.getCulLib())

historyIn = args.getHistoryIn()

if historyIn:
    # read in history of previous run
    history = HistoryDB.HistoryDB(historyIn)

# Now build a library of newly reported papers.
papers = Papers.PaperLibrary()

# connect to email source
gmail = IMAP.GMailSource(args.getEmailAddress(), getpass.getpass())

# go through each source and match with CUL library.
sources = args.getSources()
if sources[0] == 'all':
    sources = SOURCE_MAPPING.keys()

for source in sources:
    sourceClass = SOURCE_MAPPING[source]
    sourceSearch = IMAP.buildSearchString(sender = sourceClass.SENDER,
                                          sentSince = args.getSentSince(),
                                          sentBefore = args.getSentBefore())
    emailsFromSource = 0
    for email in gmail.getEmails(PAPERS_MAILBOX, sourceSearch):
        sourceEmail = sourceClass.Email(email)
        papersFromEmail = 0
        for paper in sourceEmail.getPapers():
            paper.search = sourceEmail.getSearch()
            papers.addPaper(paper)
            papersFromEmail += 1

        if papersFromEmail == 0:
            print("<br />Warning: Email from source " + source +
                  " does not contain any papers.")
            
        emailsFromSource += 1

    if emailsFromSource == 0:
        print("<br />Warning: No emails were found from " + source + ".<br />")
        
        
# All papers from all emails read; do some verification
papers.verifyConsistentDois()      # all papers with same title have the same (or no) DOI

# next report is mostly noise.  Only generate it if requested.
if args.args.verify1stauthors:
    papers.verifyConsistent1stAuthor() # all papers with same title have same 1st author

# Now compare new pubs with existing CUL lib.
# Using title, because everything has a title

byLowerTitle = {}

for lowerTitle, papersWithTitle in papers.getAllMatchupsGroupedByTitle().items():
    
    # Match by DOI first, if possible.
    doi = Papers.getDoiFromPaperList(papersWithTitle)

    culPaper = culLib.getByDoi(doi)
    if culPaper:                # Can Match by DOI; already have paper
        # print("Matching on DOI")
        byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, [culPaper])
    else:
        culPapers = culLib.getByTitleLower(lowerTitle)
        if culPapers:           # Matching by Title; already have paper
            # TODO: also check first author, pub?
            # print("Matched by title")
            byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, culPapers)
        else:                      # Appears New
            # print("New paper")
            byLowerTitle[lowerTitle] = Matchup.Matchup(papersWithTitle, None)


# Get the papers in Lower Title order

sortedTitles = sorted(byLowerTitle.keys())

# And then produce the page listing all titles, old and new.
    
for title in sortedTitles:
    print(Matchup.reportPaper(byLowerTitle[title], history))
        
if args.getHistoryOut():
    # And finally the History DB.  This will be manually updated while processing
    # the papers list, and then read in the next time we run this.
    HistoryDB.writeHistory(byLowerTitle, sortedTitles, args.getHistoryOut(), history)
            

    
