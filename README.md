# MLB-batted-ball-scraper
A work in progress python script to scrape play by play data from MLB games, focusing on getting any statcast data.  Written in Python 2.7.

0.  Required Packages

This code requires the user to have the following (non-standard) libaries installed:
- Beautiful Soup (http://www.crummy.com/software/BeautifulSoup/), an excellent package for scraping webpages.
- Pandas (http://pandas.pydata.org), a Python Data Analysis package from which we use the data frame object.

1.  Data Sources

First, MLB gameday files can be found at: http://www.mlb.com/gdcross/components/game/mlb/.  Game data is kept in directories of the form http://www.mlb.com/gdcross/components/game/mlb/year_2015/month_05/day_07/gid_2015_05_07_lanmlb_milmlb_1/; this is the game directory for the game between the Los Angeles Dodgers and the Milwaukee Brewers, played on May 7, 2015.  The '1' at the end denotes it was the first game played between them on that day.  A '2' would denote the second game, if there had been a double header.

The scraper makes use of several files.  First, the boxscore.xml file.  From this, gameParse gets data such as the teams playing, the date, the venue, and the game_pk, a unique (?) identifier.  From this identifier, we can determine location of the file that houses batted ball data: exit velocity, which is included for many but not all balls in play; distance, which is included on (most?) flyballs; and launch angle, which so far is only included for home runs.  This file is found at http://statsapi.mlb.com/api/v1/game/game_pk/feed/color.json, where "game_pk" is the identifier found in the boxscore.xml file.  In addition to batted ball data (which is in raw text form), this file contains the text for the 'feed' found in gameday.

In addition to these files, two files of use can be found in the inning directory: inning_all.xml, contains the play-by-play data for the game, including pitch f/x data for each pitch; and inning_hit.xml which includes the x and y location of each ball in play.  Unfortunately, this x and y is determined by the stringer marking a location on a 250x250 pixel grid, containing a drawing of the field of play, and is different for every stadium.

Lastly, in the batters and pitchers directories are files given by a 6 digit numerical code corresponding to player IDs assigned by MLBAM.  These files are needed to set names to IDs, as the play by play data only includes batter and pitcher IDs, and not names.

2. Functions

-getBatters(url)
This function requires the URL of the gameday files for a game, used to get data on position players on both teams involved.  It returns a pandas data frame for indexed by the batter ID, containing the following columns: First Name, Last Name, Position, Height, Weight, Birthdate, Batting handedness, Throwing Handedness.

-getPitchers(url)
This function requires the URL of the gameday files for a game, used to get data on pitchers from both teams involved.  It returns a pandas data frame indexed by the pitcher ID, containing the following columns: First Name, Last Name, Height, Weight, Birthdate, Throwing Handedness.

-getBattedBallType(description)
This function takes a description (outputted by gameday, found in the play by play data), and determines if the ball in play was a fly ball, ground ball, line drive or pop up.  If the ball was not in play, it will output an empty string.

-gameParse(url)
This function does the bulk of the work.  The argument is a gameday file directory (see section 1).  It outputs a pandas data frame, where rows represent the results of at bats.  Currently, events occuring between at bats (e.g. baserunning events) are not used.  From each at bat, the following data is recorded:
+ play_id: this is a code which indexes individual plays, it is of the form yyyymmdd_game_pk_tfs, where tfs is the time the atbat occurred.  
+ date
+ game_id: this is the same as the play_id but without the time code on the end.
+ venue
+ home team
+ away team
+ batter ID
+ batter name
+ batter handedness
+ batter's team (this is only home or away)
+ pitcher ID
+ pitcher name
+ pitcher handedness 
+ pitcher's team (again, only if they are home or away)
+ batted ball type: either "gb", "fb", "ld", or "pop", if the ball is put in play.  Otherwise, "" is recorded.
+ x_loc, y_loc these are the x and y locations marked by the stringer, as mentioned in section 1.
+ pitch speed: the starting velocity of the pitch according to pitch f/x data.
+ pitch type: the type of pitch, according to pitch f/x (note that these are of varying accuracy)
+ exit speed: the speed of the ball leaving the bat, according to the statcast data.  Not necessarily included on all plays.
+ launch angle: the angle the balls leaves the bat, according to statcast data.  Currently only appears to be recorded for home runs.
+ distance: the distance the ball traveled, according to statcast data.  Currently only appears to be recorded for fly balls.
+ result: the result of the play (walk, strikeout, ground out, double, etc.)

-parseDay(url,filename)
url should be the url containing a day's worth of games; filename should be the name of the output csv file.  This function parses a day's worth of games, and writes a csv files containing all the data output from each call to gameParse.

-monthParse(month,numdays,filename) Simple script parses a month of data.  Month should be the month written as a two digit numeric string type, i.e. if you want to parse May, it should be '05'; if you want to parse October, it would be '10'.  Needs to be a string.  numdays should just be the number of days in the month.  Filename should be self explanatory.



