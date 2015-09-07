#!/usr/bin/env python
import os
import re
from collections import defaultdict
import urllib2
from bs4 import BeautifulSoup
from bs4 import Tag
import json
import numpy as np
import pandas as pd
import matplotlib.pylab as plt

def scrapeReferee(seasonID,gameID):
    print "getting"+seasonID+","+gameID
    try: html = urllib2.urlopen('http://www.nhl.com/scores/htmlreports/'+seasonID+'/RO'+gameID+'.HTM')
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request for:'
        print 'http://www.nhl.com/scores/htmlreports/'+seasonID+'/RO'+gameID+'.HTM'
        print 'Error code: ', e.code
    except urllib2.URLError as e:
        print 'We failed to reach a server at:'
        print 'http://www.nhl.com/scores/htmlreports/'+seasonID+'/RO'+gameID+'.HTM'
        print 'Reason: ', e.reason
    else:
        soup = BeautifulSoup(html)
        visitor=soup.find(lambda tag: tag.name == 'table'  and tag.has_attr('id') and tag['id']=="Visitor")
        home=soup.find(lambda tag: tag.name == 'table'  and tag.has_attr('id') and tag['id']=="Home")
        if (visitor is None) or (home is None):
            return
        else:
            home_team=home.find_all('td')[1].find_all('img')[1].get('alt');
            home_score=int(home.find_all('td')[1].find_all('td')[1].findAll(text=True)[0]);
            visitor_team=visitor.find_all('td')[1].find_all('img')[0].get('alt');
            visitor_score=int(visitor.find_all('td')[1].find_all('td')[1].findAll(text=True)[0])
            refs = [s.findAll(text=True)[0] for s in soup.find_all("table")[-6].find_all('td')[2].find_all('td')]
            # [str Ref, int Season, bool Playoffs, {"home": [str Team, int Score, bool Win]},{"away":[str Team, int Score, bool Win]}]
            for ref in refs:
                f.write("%s\t%s\t%s\t%s\t%s\t%s\n" % (ref, home_team, home_score, visitor_team, visitor_score, seasonID))
            return

def scrapeForSeason(seasonID, gameType):
    idList=[]
    soup = BeautifulSoup(urllib2.urlopen('http://www.nhl.com/ice/schedulebyseason.htm?season=' + seasonID + '&gameType=' + gameType + '&team=&network=&venue=').read(), 'html5lib')
    # Get table elements with class == schedTbl
    scheduleTables = soup('table', {'class' : 'schedTbl'})
    if len(scheduleTables) > 1:
        # More than one schedule table on the page. Use the last one
        scheduleTable = scheduleTables[len(scheduleTables) - 1]
    else:
        # Only one schedule table
        scheduleTable = scheduleTables[0]
    # Loop through the tr tags in the schedule table
    for row in scheduleTable.tbody('tr'):
        # Variables to scrape
        nhlGameID = None
        # Get the td tags from the current tr tag
        tds = row('td')
        # Loop through td tags and look for the date, away team abbreviation, home team abbreviation, and nhl game ID
        for col in tds:
            skedLinkAnchors = col('a', {'class', 'btn'})
            if skedLinkAnchors:
                # Loop through the anchors and look for the recap link
                for anchor in skedLinkAnchors:
                    # Use the reg ex compiled above to check if it is a recap link
                    #regExMatch = gameLinkPattern.match(anchor['href'])
                    if re.search(r'recap', anchor['href'])is not None:
                        # Extract the nhl game ID from the end of the recap link
                        nhlGameID = anchor['href'][-6:]
                        scrapeReferee(str(seasonID),str(nhlGameID))
                        #idList.append([seasonID,nhlGameID])
    return #idList

#track down refs
def extract(outfile):
    seasons=[20142015,20132014,20122013,20112012,20102011,20092010,20082009,20072008,20062007,20052006]#,20042005,20032004]
    global f
    f=open(outfile, 'w+')
    for season in seasons:
        print season
        scrapeForSeason(str(season),'2')#regSeason
        scrapeForSeason(str(season),'3')#playoffs

def load(infile):
    gameData=[]
    with open(infile,'r') as f:
        for line in f:
            gameData.append(line.split('\t'))
    return gameData

def transformWinLoss(gameData):
    '''
     [ref, hometeam, win/loss, awayteam, win/loss]
    ''' 
    winData=[]
    for ref, homeTeam, homeScore, awayTeam, awayScore, season in gameData:
        if int(homeScore) > int(awayScore):
            homeWin, awayWin = 1,0
        else:
            homeWin, awayWin = 0,1
        homePlay, awayPlay = 1,1
        winData.append({"referee" : ref, "team" : homeTeam, "teamWin" : homeWin, "teamPlay" : homePlay})
        winData.append({"referee" : ref, "team" : awayTeam, "teamWin" : awayWin, "teamPlay" : awayPlay})
    return pd.DataFrame(winData)
    
def transform(gameData):
# refHistory= { ref: { team : [total, games] }
    winData = transformWinLoss(gameData)
    collapsedData = winData.groupby([winData.referee,winData.team]).sum()
    collapsedData['winPercentage'] = collapsedData["teamWin"]/collapsedData["teamPlay"]
    totalData = winData.groupby(winData.team).sum()
    totalData['winPercentage'] = totalData["teamWin"]/totalData["teamPlay"]
    print totalData.sort_index(by='winPercentage', ascending=False)
    plt.figure(figsize=(8, 8))
    #totalData['winPercentage'].plot(kind='bar', alpha=0.5)
    #plt.show()
    #plt.clf()
    print totalData.index.values
    for team in totalData.index.values:
        print "doing %s" % team
        teamData = winData.loc[winData['team'] == team ].groupby(winData.referee).sum()
        teamData = teamData[teamData['teamPlay'] > 6]
        if teamData.empty:
            continue
        print teamData
        teamData['winPercentage'] = teamData["teamWin"]/teamData["teamPlay"]
        teamData['winPercentage'].plot(kind='bar', alpha=0.5)
        teamAvg = totalData['winPercentage'][team]
        print teamAvg
        plt.ylim([0,1.0])
        plt.axhline(teamAvg, color='k')
        plt.savefig('%s.png' % team)
        plt.clf()
    #collapsedData.xs('MONTREAL CANADIENS')['winPercentage'].plot(kind='bar', alpha=0.5)
    #plt.show()

if __name__ == "__main__":
    filename = "./output.dat"
    print filename
    print os.path.exists(filename)
    if not os.path.exists(filename):
        print "extract"
        extract(filename)
    else:
        print "load"
        gameData=load(filename)
        print "transform"
        transform(gameData)
