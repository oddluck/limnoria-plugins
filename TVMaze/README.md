Fetch TV show information and schedules from the TVMaze API.

# TVMaze

### Instructions

#### This plugin requires Python 3 and Limnoria

1. Install with PluginDownloader @install oddluck TVMaze

2. Install requirements for the plugin via pip
```
pip install -r requirements.txt
```

3. Load the plugin on your bot
```
@load TVMaze
```

### Example Usage
```
<cottongin> @schedule --country GB --tz GMT
<bot> Today's Shows: Cuckoo: Ivy Arrives [S05E01] (10:00 AM GMT), Cuckoo: Ivy Nanny [S05E02] (10:00 AM GMT), Cuckoo: Weed Farm [S05E03] (10:00 AM GMT), Cuckoo: Macbeth [S05E04] (10:00 AM GMT), Cuckoo: Divorce Party [S05E05] (10:00 AM GMT), Cuckoo: Two Engagements and a Funeral [S05E06] (10:00 AM GMT), Cuckoo: Election [S05E07] (10:00 AM GMT), The Dumping Ground: Rage [S08E01] (5:00 PM GMT),  (1 more message)      

<cottongin> @tvshow the orville
<bot> The Orville (2017) | Next: Home [S02E03] (2019-01-10 in 6 days) | Prev: Primal Urges [S02E02] (2019-01-03) | Running | English | 60m | FOX | Comedy/Adventure/Science-Fiction | http://www.tvmaze.com/shows/20263/the-orville | https://imdb.com/title/tt5691552/ | http://www.fox.com/the-orville
```
Use @help tvshow|schedule to see details on each command.

---

You can use @settvmazeoptions to save common command options to make using commands easier:
```
@settvmazeoptions --country GB
@settvmazeoptions --tz US/Central
@settvmazeoptions --country AU --tz US/Pacific
```
This stores settings per nick, you can clear them via --clear:
```
@settvmazeoptions --clear
```
