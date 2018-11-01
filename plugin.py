# CFBScores
###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
#
###

import requests
import pendulum
import json
import html
from bs4 import BeautifulSoup
import re

from supybot import utils, plugins, ircutils, callbacks, schedule
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CFBScores')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class CFBScores(callbacks.Plugin):
    """Fetches CFB scores"""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(CFBScores, self)
        self.__parent.__init__(irc)
        
        self.SCOREBOARD = ('http://site.api.espn.com/apis/site/v2/sports/'
                           'football/college-football/scoreboard')
        
        self.FUZZY_DAYS = ['yesterday', 'tonight', 'today', 'tomorrow',
                           'sun', 'mon', 'tue', 'wed', 'thu', 'fri', 'sat']
        
        self._current_week = 0
        self._cfb_byes = {}
        
        with open("abbrv.json", 'r') as json_file:
            self.abbrv = json.load(json_file)
            
        if not self.abbrv:
            self.abbrv = requests.get(
            'https://raw.githubusercontent.com/diagonalfish/FootballBotX2/master/abbrv.json')
            self.abbrv = self.abbrv.json()
        
        def periodicCheckGames():
            self.CFB_GAMES = self._fetchGames(None, '')
            
        periodicCheckGames()
        
        try:  # check scores.
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchCFBscores')
        except AssertionError:
            try:
                schedule.removeEvent('fetchCFBscores')
            except KeyError:
                pass
            schedule.addPeriodicEvent(periodicCheckGames, 20, now=False, name='fetchCFBscores')
            
    @wrap
    def cfbbyes(self, irc, msg, args):
        """Gets teams on bye week for current week"""
        
        url = 'https://247sports.com/Article/Schedule-of-bye-weeks-for-college-footballs-top-2018-contenders-120880121/'
        headers = {'User-Agent': 'Mozilla/5.0 (X11; CrOS x86_64 11151.4.0) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/71.0.3578.8 Safari/537.36'}
        
        if not self._cfb_byes:
            data = requests.get(url, headers=headers)
            soup = BeautifulSoup(data.content)

            pattern = re.compile(r'Week')
            section = soup.find('section', class_='article-body')
            ps = section.find_all('p')

            output = {}
            for p in ps:
                if p.text.startswith('Week'):
                    week = p.text.split(':')[0]
                    week = week.split('(')[0].strip()
                    byes = p.text.split(':')[1].strip()
                    if byes:
                        output[week] = byes
                        
            self._cfb_byes = output
                
        try:
            irc.reply(self._cfb_byes[self._current_week])
            return
        except:
            irc.reply('No teams on bye this week')
            return
            
    
    @wrap([getopts({'week': 'positiveInt'}), optional('text')])
    def cfbrankings(self, irc, msg, args, optlist, filter_team=None):
        """Fetches CFB Rankings"""
        
        optlist = dict(optlist)
        week = optlist.get('week')
        
        url = 'http://site.api.espn.com/apis/site/v2/sports/football/college-football/rankings'
        if week:
            url += '?weeks={}'.format(week)
        
        try:
            data = requests.get(url)
            data = data.json()
        except:
            irc.reply('Error fetching rankings')
            return
        
        if not week:
            week = ' ' + data['latestWeek']['displayValue']
        else:
            if week > data['latestWeek']['number']:
                irc.reply("Sorry, I cannot predict the future")
                return
            week = ' Week {}'.format(week)
        
        rankings = data['rankings'][0]
        self._current_week = week.strip()
        title = data['rankings'][0]['name']
        
        output = []
        for team in rankings['ranks']:
            tmp = '#{0}{3} {1} {2}'
            
            if '+' in team['trend']:
                trend = self._green(team['trend'])
            elif '-' in team['trend'] and team['trend'] != '-':
                trend = self._red(team['trend'])
            else:
                trend = team['trend']
            tmp = tmp.format(
                team['current'],
                self._bold(team['team']['abbreviation']),
                team['recordSummary'],
                '({})'.format(trend) if trend != '-' else ''
            )
            
            if filter_team:
                if filter_team.upper() == team['team']['abbreviation']:
                    tmp += ' :: {} points'.format(team['points'])
                    output.append(tmp)
                    break
            else:
                output.append(tmp)
                
        if filter_team and len(output) == 1:
            irc.reply('{}: {}'.format(title + week, output[0]))
        elif filter_team and not output:
            irc.reply('No results found for {}'.format(filter_team))
        else:
            irc.reply('{}: {}'.format(title + week, ' | '.join(team for team in output[:11])))
            irc.reply('{}'.format(' | '.join(team for team in output[11:])))
        
    @wrap([getopts({'week': 'positiveInt', 'conf': 'positiveInt'}), optional('text')])
    def cfb(self, irc, msg, args, optlist, team=None):
        """[--conf #] [--week #] [<team>]
        Fetches CFB Scores. Defaults to current week and AP Top 25 teams. 
        Use --conf # (ESPN league #) to fetch a specific conference. 
        Use --week # to look up a specific week. 
        """
        
        optlist = dict(optlist)
        week = optlist.get('week')
        conf = optlist.get('conf')
        
        team = self._parseInput(team)
        
        if (conf==80 or conf==81 or conf==35) and not team:
            irc.reply('ERROR: You must provide a team')
            return
        
        # override games cache
        if week or conf or team == 'today':
            self.CFB_GAMES = self._fetchGames(team, conf, week)
        
        if not self.CFB_GAMES:
            self.CFB_GAMES = self._fetchGames(team, conf)
            if not self.CFB_GAMES:
                irc.reply('No games found')
                return
        
        games = self._parseGames(self.CFB_GAMES, team)
        games = self._sortGames(games)
        
        reply_string = self._replyAsString(team, games)
        
        for string in reply_string:
            irc.reply(string)
        
        # reset games cache to current week
        if week:
            self.CFB_GAMES = self._fetchGames(team, conf)
        elif conf:
            self.CFB_GAMES = self._fetchGames(team, conf='')
            
    def _parseInput(self, team):
        if not team:
            return None
        else:
            # tbd
            return team
        
    def _fetchGames(self, team, conf="80", week=None):
        team = 'all' if not team else team.upper()
        date = pendulum.now('US/Pacific')
        conf = '' if not conf else conf
        
        url = self.SCOREBOARD + '?groups={}'.format(conf)
        if team != 'all' and team != 'TODAY' and team != 'INP':
            url += '&limit=300'
            
        if week:
            url += '&week={}'.format(week)
        
        games = requests.get(url)
        games = games.json()
        
        games = games['events']
        
        if team != 'all' and team != 'TODAY' and team != 'INP':
            ngames = []
            
            # check abbreviation first
            for game in games:
                if team == game['competitions'][0]['competitors'][0]['team']['abbreviation'] \
                or team == game['competitions'][0]['competitors'][1]['team']['abbreviation']:
                    ngames.append(game)
            if not ngames:
                if team == 'HAWAII':
                    team = "HAWAI'I"
                for game in games:
                    if team == html.unescape(game['competitions'][0]['competitors'][0]['team']['location']).upper() \
                    or team == html.unescape(game['competitions'][0]['competitors'][1]['team']['location']).upper():
                        ngames.append(game)
            return ngames
                    
        
        return games
    
    def _parseGames(self, games, team=None):
        new_games = []
        
        if team:
            if team.lower() != 'all' and team.lower() != 'today' and team.lower() != 'inp':
                for idx, game in enumerate(games):
                    if team.upper() == game['competitions'][0]['competitors'][0]['team']['abbreviation'] \
                    or team.upper() == game['competitions'][0]['competitors'][1]['team']['abbreviation']:
                        games = [games.pop(idx)]
                        break
        
        for game in games:
            date = pendulum.parse(game['date']).in_tz('US/Pacific')
            today = pendulum.today('US/Pacific')
            new_game = {}
            new_game['id'] = game['id']
            new_game['time'] = pendulum.parse(game['date']).in_tz('US/Eastern').format('ddd h:mm A zz')
            new_game['date'] = pendulum.parse(game['date']).in_tz('US/Eastern').format('dddd, MMMM Do, h:mm A zz')
            new_game['home_full'] = game['competitions'][0]['competitors'][0]['team']['location']
            new_game['home'] = game['competitions'][0]['competitors'][0]['team']['abbreviation']
            new_game['home_id'] = game['competitions'][0]['competitors'][0]['team']['id']
            new_game['away_full'] = game['competitions'][0]['competitors'][1]['team']['location']
            new_game['away'] = game['competitions'][0]['competitors'][1]['team']['abbreviation']
            new_game['away_id'] = game['competitions'][0]['competitors'][1]['team']['id']
            new_game['status'] = game['status']['type']['state']
            new_game['shortDetail'] = game['status']['type']['shortDetail']
            new_game['final'] = game['status']['type']['completed']
            new_game['in_progress'] = False
            # Rankings
            new_game['home_team_rank'] = game['competitions'][0]['competitors'][0]['curatedRank'].get('current')
            new_game['away_team_rank'] = game['competitions'][0]['competitors'][1]['curatedRank'].get('current')
            
            # Odds
            try:
                new_game['odds'] = '{} (O/U: {:.0f})'.format(game['competitions'][0]['odds'][0]['details'], game['competitions'][0]['odds'][0]['overUnder'])
            except Exception as e:
                new_game['odds'] = ''
                print(e)
                
            
            if new_game['status'] == 'in' and not new_game['final']:
                new_game['in_progress'] = True
                try:
                    new_game['last_play'] = game['competitions'][0]['situation']['lastPlay']['text']
                except:
                    new_game['last_play'] = ''
                new_game['pos'] = game['competitions'][0]['situation'].get('possession')
                new_game['rz'] = game['competitions'][0]['situation'].get('isRedZone')
                new_game['desc'] = game['competitions'][0]['situation'].get('downDistanceText')
                new_game['clock'] = game['status']['type']['shortDetail']
                try:
                    new_game['clock'] = new_game['clock'].split('-')[0].strip() + ' ' + self._green(new_game['clock'].split('-')[1].strip())
                except:
                    new_game['clock'] = new_game['clock']
                if 'Delayed' in new_game['clock']:
                    new_game['clock'] = self._orange('DLY')
                if 'Halftime' in new_game['clock']:
                    new_game['clock'] = 'HT'
                    new_game['HT'] = True
                else:
                    new_game['HT'] = False
                    
            elif new_game['status'] == 'post':
                new_game['in_progress'] = False
            new_game['broadcasts'] = '{}'.format(', '.join(item['media']['shortName'] for item in game['competitions'][0]['geoBroadcasts']))
            new_game['h_score'] = int(game['competitions'][0]['competitors'][0]['score'])
            new_game['a_score'] = int(game['competitions'][0]['competitors'][1]['score'])
            if team == 'today':
                if date.day == today.day:
                    new_games.append(new_game)
            elif team == 'inp':
                if new_game['in_progress']:
                    new_games.append(new_game)
            else:
                new_games.append(new_game)
            
        return new_games
    
    def _sortGames(self, games):
        sorted_games = sorted(games, key=lambda k: k['final'])
        
        return sorted_games
        
    def _replyAsString(self, team, games):
        reply_strings = []
        tmp_strings = []
        half_point = len(games)//2
        
        def _parseScores(away, ascr, home, hscr, arnk, hrnk):
            print(ascr, arnk, hscr, hrnk)
            if ascr > hscr:
                astr = '{} {}'.format(self._bold(away), self._bold(ascr))
                hstr = '{} {}'.format(home, hscr)
                if arnk > hrnk:
                    upset = True
                else:
                    upset = False
            elif ascr < hscr:
                hstr = '{} {}'.format(self._bold(home), self._bold(hscr))
                astr = '{} {}'.format(away, ascr)
                if hrnk > arnk:
                    upset = True
                else:
                    upset = False
            else:
                astr = '{} {}'.format(away, ascr)
                hstr = '{} {}'.format(home, hscr)
                upset = False
                
            print(upset)
            return astr, hstr, upset
        
        if len(games) == 2:
            if games[0]['away'] == games[1]['away']:
                for idx, game in enumerate(games):
                    if game['shortDetail'] == 'Postponed':
                        games.pop(idx)
                        
        single = True if len(games) == 1 else False
        
        for game in games:
            string = ''
            if single:
                away = game['away_full']
                home = game['home_full']
                time = game['date']
            else:
                away = game['away']
                home = game['home']
                time = game['time']
            if game['status'] == 'pre':
                string = '{} @ {} - {}'.format(away, home, time)
                if single:
                    string += ' - \x02TV:\x02 {}'.format(game['broadcasts'])
                    if game['odds']:
                        string += ' - \x02Odds:\x02 {}'.format(game['odds'])
                tmp_strings.append(string)
            elif game['in_progress']:
                if not game['HT']:
                    if game['pos'] == game['away_id']:
                        if game['rz']:
                            away = self._red('<>{}'.format(away))
                        else:
                            away = '<>' + away
                    if game['pos'] == game['home_id']:
                        if game['rz']:
                            home = self._red('<>{}'.format(home))
                        else:
                            home = '<>' + home
                away_str, home_str, upset = _parseScores(away, game['a_score'], home, game['h_score'], game['away_team_rank'], game['home_team_rank'])
                if game['clock'] == 'HT':
                    if single:
                        game['clock'] = self._orange('Halftime')
                    else:
                        game['clock'] = self._orange(game['clock'])
                if single:
                    game['clock'] = '({})'.format(game['clock'])
                string = '{} @ {} {}'.format(away_str, home_str, game['clock'])
                if upset:
                    if single:
                        string += ' :: {}'.format(self._orange('UPSET'))
                    string = self._ul(string)
                if not game['HT'] and single:
                    if game['desc']:
                        desc = ' :: {}'.format(game['desc'])
                    else:
                        desc = ''
                    if game['last_play']:
                        string += '{} :: \x02Last Play:\x02 {}'.format(desc, game['last_play'])
                    if game['broadcasts']:
                        string += ' :: \x02TV:\x02 {}'.format(game['broadcasts'])
                if game['odds']:
                    string += ' :: \x02Odds:\x02 {}'.format(game['odds'])
                tmp_strings.append(string)
            elif game['status'] == 'post':
                if game['shortDetail'] != 'Final':
                    endCode = game['shortDetail']
                    if 'Postponed' in endCode:
                        if not single:
                            endCode = self._red('PPD')
                        else:
                            endCode = self._red(endCode)
                    elif 'Canceled' in endCode:
                        if not single:
                            endCode = self._red('C')
                        else:
                            endCode = self._red(endCode)
                    elif 'OT' in endCode:
                        if single:
                            endCode = self._red(endCode)
                        else:
                            endCode = self._red('F/OT')
                elif 'OT' in game['shortDetail']:
                    if single:
                        endCode = self._red(endCode)
                    else:
                        endCode = self._red('F/OT')
                else:
                    if single:
                        endCode = self._red('Final')
                    else:
                        endCode = self._red('F')
                away_str, home_str, upset = _parseScores(away, game['a_score'], home, game['h_score'], game['away_team_rank'], game['home_team_rank'])
                string = '{} @ {} {}'.format(away_str, home_str, endCode)
                if upset and not single:
                    string = self._ul(string)
                if single:
                    if upset:
                        string += ' :: {}'.format(self._orange('UPSET'))
                tmp_strings.append(string)
                
        
        print(len(tmp_strings), half_point)        
        if len(tmp_strings) > 1 and half_point >= 6:
            reply_strings.append(' | '.join(string for string in tmp_strings[:half_point]))
            reply_strings.append(' | '.join(string for string in tmp_strings[half_point:]))
        else:
            reply_strings.append(' | '.join(string for string in tmp_strings))
        
        
        return reply_strings
        
    def _red(self, string):
        """Returns a red string."""
        return ircutils.mircColor(string, 'red')

    def _yellow(self, string):
        """Returns a yellow string."""
        return ircutils.mircColor(string, 'yellow')
    
    def _orange(self, string):
        return ircutils.mircColor(string, 'orange')

    def _green(self, string):
        """Returns a green string."""
        return ircutils.mircColor(string, 'green')

    def _blue(self, string):
        """Returns a blue string."""
        return ircutils.mircColor(string, 'blue')

    def _bold(self, string):
        """Returns a bold string."""
        return ircutils.bold(string)

    def _ul(self, string):
        """Returns an underline string."""
        return ircutils.underline(string)

    def _bu(self, string):
        """Returns a bold/underline string."""
        return ircutils.bold(ircutils.underline(string))


Class = CFBScores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
