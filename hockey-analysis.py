import os
import re
import urllib2
from bs4 import BeautifulSoup
from bs4 import Tag
import json


# In[6]:

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
                    #print anchor, seasonID
                    # Use the reg ex compiled above to check if it is a recap link
                    #regExMatch = gameLinkPattern.match(anchor['href'])
                    if re.search(r'recap', anchor['href'])is not None:
                        # Extract the nhl game ID from the end of the recap link
                        nhlGameID = anchor['href'][-6:]
                        #print nhlGameID
                        idList.append([seasonID,nhlGameID])
    return idList

#track down refs
seasons=[20132014,20122013,20112012,20102011,20092010,20082009,20072008,20062007,20052006]#,20042005,20032004]
recaps=[]
for season in seasons:
    recaps+=(scrapeForSeason(str(season),'2'))#regSeason
    if season != 20132014:
        recaps+=(scrapeForSeason(str(season),'3'))#playoffs
print recaps[1]
teams=[]
refs = []
results=[]
for recap in recaps:
    tag=recap[1]
    season=recap[0]
    try: html = urllib2.urlopen('http://www.nhl.com/scores/htmlreports/'+season+'/RO'+tag+'.HTM')
    except urllib2.HTTPError as e:
        print 'The server couldn\'t fulfill the request for:'
        print 'http://www.nhl.com/scores/htmlreports/'+season+'/RO'+tag+'.HTM'
        print 'Error code: ', e.code
    except urllib2.URLError as e:
        print 'We failed to reach a server at:'
        print 'http://www.nhl.com/scores/htmlreports/'+season+'/RO'+tag+'.HTM'
        print 'Reason: ', e.reason
    else:
        soup = BeautifulSoup(html)
        visitor=soup.find(lambda tag: tag.name == 'table'  and tag.has_attr('id') and tag['id']=="Visitor")
        home=soup.find(lambda tag: tag.name == 'table'  and tag.has_attr('id') and tag['id']=="Home")
        home_team=home.find_all('td')[1].find_all('img')[1].get('alt');
        home_score=int(home.find_all('td')[1].find_all('td')[1].findAll(text=True)[0]);
        visitor_team=visitor.find_all('td')[1].find_all('img')[0].get('alt');
        visitor_score=int(visitor.find_all('td')[1].find_all('td')[1].findAll(text=True)[0])
        refs = [s.findAll(text=True)[0] for s in soup.find_all("table")[-6].find_all('td')[2].find_all('td')]
            # [str Ref, int Season, bool Playoffs, {"home": [str Team, int Score, bool Win]},{"away":[str Team, int Score, bool Win]}]
        for ref in refs:
            results.append([ref,home_team, home_score, visitor_team, visitor_score,season])
print results

# In[3]:




# In[9]:




# In[5]:




# In[13]:




# In[7]:




# In[ ]:

#ice(/scores.htm?date=05/01/2014)

#The recap links and the roster report links differ in that 2013 is replaced by the letters RO

