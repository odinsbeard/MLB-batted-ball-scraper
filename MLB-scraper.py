import urllib2
import json
from bs4 import BeautifulSoup
import pandas as pd
import time

BASE_URL = "http://www.milb.com/gdcross/components/game/"
# the directory for AAA is /aaa/, AA is /aax
# then the year, in the form of year_2014/
#then month in the form month_05/ (for May, for instance)
#then day in the form day_06
#so to get AAA scores for May 6, 2014, your url would be
#http://www.milb.com/gdcross/components/game/aaa/year_2014/month_05/day_06/

def getPitchers(url):
    '''give it the URL of the game directory, 
    i,e. http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_05/day_07/gid_2015_05_07_lanmlb_milmlb_1/
    '''
    try:
        pitcherURL = urllib2.urlopen(url + "pitchers/").read()
    except:
        print "Game Postponed"
        return None
    pitchSoup = BeautifulSoup(pitcherURL,"lxml")
    pitchers = pd.DataFrame(columns=("id","first_name","last_name","height","weight","dob","throws"))
    pitchers = pitchers.set_index('id')
    idlist = pitchSoup.find_all("a")[1:len(pitchSoup.find_all("a"))]
    for i in idlist:
        idURL = urllib2.urlopen(url + "pitchers/" + i['href']).read()
        idSoup = BeautifulSoup(idURL,"lxml")
        player = idSoup.player
        pitchers.loc[player['id']] = [player["first_name"],player["last_name"],player["height"],player["weight"],\
                                player["dob"],player["throws"]]
    return pitchers

def getBatters(url):
    '''give it the URL of the game directory, 
    i,e. http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_05/day_07/gid_2015_05_07_lanmlb_milmlb_1/
    '''
    pitcherURL = urllib2.urlopen(url + "batters/").read()
    pitchSoup = BeautifulSoup(pitcherURL,"lxml")
    pitchers = pd.DataFrame(columns=("id","first_name","last_name","pos","height","weight","dob","bats","throws"))
    pitchers = pitchers.set_index('id')
    idlist = pitchSoup.find_all("a")[1:len(pitchSoup.find_all("a"))]
    for i in idlist:
        idURL = urllib2.urlopen(url + "batters/" + i['href']).read()
        idSoup = BeautifulSoup(idURL,"lxml")
        player = idSoup.player
        pitchers.loc[player['id']] = [player["first_name"],player["last_name"],player["pos"],player["height"],player["weight"],\
                                player["dob"],player["bats"],player["throws"]]
    return pitchers


bipOutcomes = ["Groundout","Bunt Groundout","Bunt Lineout","Flyout","Lineout","Pop Out","Forceout","Grounded Into DP",\
                "Sac Fly DP","Sacrifice Bunt DP","Fan interference","Double Play","Triple Play","Sac Bunt","Bunt Pop Out",\
                "Sac Fly","Single","Double","Triple","Home Run", "Field Error","Fielders Choice Out","Fielders Choice",\
                "Forceout"]
nonbipOutcomes = ["Strikeout","Strikeout - DP","Hit By Pitch","Walk","Intent Walk","Catcher Interference","Batter Interference"]

def getBattedBallType(description):
    '''Description, a string, something like "Joc Pederson homers (9) on a fly ball to center field"
        Will return a string with the batted ball type, either 'gb' for grounders, 'fb' for fly balls,
        'ld' for line drives or 'pop' for popups.  Returns '' if description contains no batted ball descriptions
        at least in theory
    '''
    flyballs = set(['fly','flies'])
    grounders = set(['grounds', 'ground'])
    popups = set(['pop','pops'])
    liners = set(['lines','liner'])
    wordlist = set(description.split())
    if len(wordlist.intersection(flyballs)) > 0:
        return 'fb'
    elif len(wordlist.intersection(grounders)) > 0:
        return 'gb'
    elif len(wordlist.intersection(popups)) > 0:
        return 'pop'
    elif len(wordlist.intersection(liners)) > 0:
        return 'ld'
    else: 
        return ''
    

def gameParse(url):
    ''' takes the url of the game directory, 
    like http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_05/day_07/gid_2015_05_07_lanmlb_milmlb_1/'''
    
    #Data frame should have the following column headings
    # "play_id", "date","game_id","hometeam","awayteam",
    #"batter_id","stands", "batter","batter_team", "pitcher_id", "pitcher","throws","pitcher_team",
    # "batted_ball_type", "x_loc", "y_loc", "pitch_speed", "pitch_type","exit_speed",
    # "launch_angle","distance","loc", "venue"
    # Some of these will be obvious; play_id will be a combination of the date, the game_pk
    # (which I want to assume is unique for all games but won't), and the time of the event.
    # game_id will be the date + game_pk, 
    
    pitchers = getPitchers(url)
    if pitchers is None:
        return None
    batters = getBatters(url)
    
    gamedata = pd.DataFrame(columns=("play_id","date","game_id","venue","home","inning","away","batter_id","batter",
                                        "stands","batter_team","pitcher_id","pitcher","throws","pitcher_team",
                                        "pitch_type","pitch_speed","batted_ball_type","exit_speed","launch_angle",
                                        "distance","x_loc","y_loc","result"))
    gamedata = gamedata.set_index("play_id")
    
    #Get boxscore xml file
    boxURL = urllib2.urlopen(url + "boxscore.xml").read()
    boxSoup = BeautifulSoup(boxURL,'lxml')
    if boxSoup.boxscore['status_ind'] != "F":
        return gamedata
        print "Game Postponed!"
    
    game_pk = boxSoup.boxscore['game_pk']
    dateraw = boxSoup.boxscore['game_id'].split("/") #gets the game id, which is yyyy/mm/dd/away-home-gamenum, converts to 
                                                    #list [year,month,day,away-home-num]
    date = dateraw[0] + dateraw[1] + dateraw[2] #1/24
    home = boxSoup.boxscore['home_fname'] #2/24
    away = boxSoup.boxscore['away_fname'] #3/24
    game_id = date + "_" + game_pk #4/24
    venue = boxSoup.boxscore['venue_name'] #5/24
    
    
    json_color = urllib2.urlopen("http://statsapi.mlb.com/api/v1/game/" + game_pk + "/feed/color.json").read()
    color = json.loads(json_color)
    pbpEvents = []
    for i in color['items']:
        if i['group'] == "playByPlay" and i["guid"][0:10] == "playResult":
            pbpEvents.insert(0,{'description': i['data']['description'],'player_id':i['data']['player_id'],\
                                'result':i['data']['result'],'time_tfs':i['time_tfs'],'time_gen':i['time_gen']})
    pbpCounter = 0 #keep track of where we are in eventsCounter
    
    pbpURL = urllib2.urlopen(url + "inning/inning_all.xml").read()
    pbpSoup = BeautifulSoup(pbpURL,"lxml")
    
    hitURL = urllib2.urlopen(url + "inning/inning_hit.xml").read()
    hitSoup = BeautifulSoup(hitURL,"lxml")
    bip = hitSoup.find_all("hip")
    bipEvents = []
    for i in bip:
        bipEvents.append({"des":i["des"],"x":float(i["x"]),"y":float(i["y"]),"batter":i["batter"],"pitcher":i["pitcher"],\
                        "inning":i["inning"]})
    bipCounter = 0 #keep track of where we are in bipEvents
    
    #gamedata = pd.DataFrame(columns=("play_id","date","game_id","venue","home","inning","away","batter_id","batter",
    #                                    "stands","batter_team","pitcher_id","pitcher","throws","pitcher_team",
    #                                    "pitch_type","pitch_speed","batted_ball_type","exit_speed","launch_angle",
    #                                    "distance","x_loc","y_loc","result"))
    
    innings = pbpSoup.find_all('inning')
    for j in innings:
        atbats_away = j.top.find_all('atbat')
        for i in atbats_away:
            batter_team = "away" #6/24
            pitcher_team = "home" #7/24
            inning = j['num'] #8/24
            batter_id = i['batter'] #9/24
            batter = batters.loc[batter_id]["first_name"] + " " + batters.loc[batter_id]["last_name"] #23/24
            pitcher_id = i['pitcher'] #10/24
            pitcher = pitchers.loc[pitcher_id]["first_name"] + " " + pitchers.loc[pitcher_id]["last_name"] #24/24
            stands = i['stand'] #11/24
            throws = i['p_throws'] #12/24
            result = i['event'] #13/24
            description = i['des']
            batted_ball_type = getBattedBallType(description) #14/24
            
            try:
                pitch = i.find_all('pitch')[-1]
            except IndexError:
                continue
                
            time = pitch['tfs']
            play_id = date + "_" + game_pk + "_" + time #15/24 the index
            pitch_type = pitch["type"] #16/24
            try:
                pitch_speed = float(pitch["start_speed"]) #17/24
            except KeyError:
                pitch_speed = ""
            
            #set these in case they don't get assigned later
            exit_speed = ""
            launch_angle = ""
            distance = ""
            x_loc, y_loc = -999.99,-999.99
            
            description2 = pitch['des'].split()
            # Here we will get the x and y location for the ball if it was put into play #
            if description2[0] == "In":
                for k in xrange(bipCounter,len(bipEvents)):
                    if bipEvents[k]['batter'] == batter_id and bipEvents[k]['pitcher'] == pitcher_id and bipEvents[k]['inning'] == inning:
                        x_loc,y_loc = bipEvents[k]['x'],bipEvents[k]['y'] #18,19/24
                        bipCounter = k
                        break
                        
                #Here we well attempt to scrape the color.json, from which we got a list of pbp events, pbpEvents,
                # to get exit velocity, launch angle and distance, if available
                for k in xrange(pbpCounter,len(pbpEvents)):
                    if pbpEvents[k]["time_tfs"] == date + "_" + time:
                        wordlist = pbpEvents[k]["description"].replace(".","").replace(";","").split()
                        if "mph" in wordlist:
                            exit_speed = float(wordlist[wordlist.index("mph")-1]) #20/24
                        else:
                            exit_speed = ""
                        if "degrees" in wordlist:
                            launch_angle = float(wordlist[wordlist.index("degrees")-1]) #21/24
                        else:
                            launch_angle = ""
                        if "feet" in wordlist:
                            distance = float(wordlist[wordlist.index("feet")-1]) #22/24
    #        "play_id","date","game_id","venue","home","inning","away","batter_id","batter",
    ##                                   "stands","batter_team","pitcher_id","pitcher","throws","pitcher_team",
    ##                                    "pitch_type","pitch_speed","batted_ball_type","exit_speed","launch_angle",
    ##                                    "distance","x_loc","y_loc","result"                
                            
            gamedata.loc[play_id] = [date,game_id,venue,home,inning,away,batter_id,batter,stands,batter_team,\
                                        pitcher_id,pitcher,throws,pitcher_team,pitch_type,pitch_speed,\
                                        batted_ball_type,exit_speed,launch_angle,distance,x_loc,y_loc,result]
                            
                                                        
        bipCounter = 0
        pbpCounter = 0
        if j.bottom == None:
            break
        atbats_home = j.bottom.find_all('atbat')
        for i in atbats_home:
            batter_team = "home" #6/24
            pitcher_team = "away" #7/24
            inning = j['num'] #8/24
            batter_id = i['batter'] #9/24
            batter = batters.loc[batter_id]["first_name"] + " " + batters.loc[batter_id]["last_name"] #23/24
            pitcher_id = i['pitcher'] #10/24
            pitcher = pitchers.loc[pitcher_id]["first_name"] + " " + pitchers.loc[pitcher_id]["last_name"] #24/24
            stands = i['stand'] #11/24
            throws = i['p_throws'] #12/24
            result = i['event'] #13/24
            description = i['des']
            batted_ball_type = getBattedBallType(description) #14/24
            
            try:
                pitch = i.find_all('pitch')[-1]
            except IndexError:
                continue
                
            time = pitch['tfs']
            play_id = date + "_" + game_pk + "_" + time #15/24 the index
            pitch_type = pitch["type"] #16/24
            try:
                pitch_speed = float(pitch["start_speed"]) #17/24
            except KeyError:
                pitch_speed = ''
            
            #set these in case they don't get assigned later
            exit_speed = ""
            launch_angle = ""
            distance = ""
            x_loc, y_loc = -999.99,-999.99
            
            
            description2 = pitch['des'].split()
            # Here we will get the x and y location for the ball if it was put into play #
            if description2[0] == "In":
                for k in xrange(bipCounter,len(bipEvents)):
                    if bipEvents[k]['batter'] == batter_id and bipEvents[k]['pitcher'] == pitcher_id and bipEvents[k]['inning'] == inning:
                        x_loc,y_loc = bipEvents[k]['x'],bipEvents[k]['y'] #18,19/24
                        bipCounter = k
                        break
                        
                #Here we well attempt to scrape the color.json, from which we got a list of pbp events, pbpEvents,
                # to get exit velocity, launch angle and distance, if available
                for k in xrange(pbpCounter,len(pbpEvents)):
                    if pbpEvents[k]["time_tfs"] == date + "_" + time:
                        wordlist = pbpEvents[k]["description"].replace(".","").replace(";","").split()
                        if "mph" in wordlist:
                            exit_speed = float(wordlist[wordlist.index("mph")-1]) #20/24
                        else:
                            exit_speed = ""
                        if "degrees" in wordlist:
                            launch_angle = float(wordlist[wordlist.index("degrees")-1]) #21/24
                        else:
                            launch_angle = ""
                        if "feet" in wordlist:
                            distance = float(wordlist[wordlist.index("feet")-1]) #22/24                
             
            gamedata.loc[play_id] = [date,game_id,venue,home,inning,away,batter_id,batter,stands,batter_team,\
                                        pitcher_id,pitcher,throws,pitcher_team,pitch_type,pitch_speed,\
                                        batted_ball_type,exit_speed,launch_angle,distance,x_loc,y_loc,result]    
        
        bipCounter = 0
        pbpCounter = 0    
    print away + " at " + home + ", on " + date        
    return gamedata    


def parseDay(url, filename,writecols=True):
    ''' url should be a day's worth of game data, i.e. http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_05/day_07/
    filename should be the name of the output file.'''
    
    print "Day started at", time.ctime()
    
    dayURL = urllib2.urlopen(url).read()
    daySoup = BeautifulSoup(dayURL,"lxml")
    
    #here we get the game codes for the day's games.
    days = []
    for i in daySoup.find_all("a"):
        if i['href'][0:3] == "gid":
            days.append(i['href'])
    
    #We'll have a dummy boolean initially set to True so that when the first game is written, the header will be written
    
    for i in days:
        gamedata = gameParse(url + i)
        if gamedata is None:
            continue
        gamedata.to_csv(filename,header=writecols,mode="a")
        writecols = False
    print "Day ended at", time.ctime() 

def bugHunt(url):
    ''' opens up the innings_all.xml file and troubleshoots.  url should be the innings_all.xml ''' 
    inningURL = urllib2.urlopen(url).read()
    pbpSoup = BeautifulSoup(inningURL,'lxml')
    innings = pbpSoup.find_all('inning')
    for j in innings:
        atbats_away = j.top.find_all('atbat')
        for i in atbats_away:
            print "away at bat, number " + str(i['num']),
            
            try:
                pitch = i.find_all('pitch')[-1]
            except IndexError:
                continue
            
            try:
                print "pitch speed: " + str(float(pitch["start_speed"])) + " mph" #17/24
            except KeyError:
                print "pitch speed: __ mph" #17/24
                
            
def parseMonth(month,monthstart,monthend,filename,writecols=True):
    ''' month should be a two digit string of numbers for the month desired, i.e. may should be '05',  
    monthstart and month end should be the first day and last day of the month, respectively,filename should be the output file name'''
    print "Month started at ", time.ctime()
    
    cols = writecols #boolean marker to print the columns on monthstart if writecols = True and not after
    
    for i in range(monthstart,monthend+1):
        day_num = i
        if day_num < 10:
            day = "0" + str(day_num)
        else:
            day = str(day_num)
        url = "http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_" + month + "/day_" + day + "/"
        parseDay(url,filename,writecols=cols)
        cols = False
    
    print "Month ended at ", time.ctime()
        
        
        
        
        
    

    
