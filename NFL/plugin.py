###
# Copyright (c) 2019, cottongin
# All rights reserved.
#
#
###

import pendulum
import requests, json
from roman_numerals import convert_to_numeral

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('NFL')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

BASE_URL = "https://feeds.nfl.com/feeds-rs{}.json"

def getValidDateFmt(irc, msg, args, state):
    date = args[0]
    valid = ['yesterday', 'tomorrow']
    check = None
    try:
        if date.lower() in valid:
            if date.lower() == 'yesterday':
                check = pendulum.yesterday().format('MM/DD/YYYY')
            else:
                check = pendulum.tomorrow().format('MM/DD/YYYY')
        else:
            check = pendulum.parse(date, strict=False).format('MM/DD/YYYY')
    except:
        pass
    if not check:
        state.errorInvalid(_('date format'), str(date))
    else:
        state.args.append(check)
        del args[0]
addConverter('validDate', getValidDateFmt)

class NFL(callbacks.Plugin):
    """Fetches scores and game information from NFL.com"""
    threaded = True

    def __init__(self, irc):
        super().__init__(irc)
        self.GOOG = irc.getCallback('Google')

    @wrap([getopts({"week": "positiveInt",
                    "season": "positiveInt",
                    "type": ("literal", ("hof","pre", "reg", "post", "pro", "sb")),
                    "inp": "",
                    "pro": "",
                    "date": "validDate"}), optional("somethingWithoutSpaces")])
    def nfl(self, irc, msg, args, options, team):
        """(--week <#> | --type <pre/reg/post> | --inp | --date <YYYY-MM-DD|MM/DD/YYYY>) (<team abbreviation>)
        Fetches scores.
        """
        options = dict(options)
        inp = options.get('inp')
        seasonType = options.get('type')
        date = options.get('date') or pendulum.now().format('MM/DD/YYYY')
        week = options.get('week')
        season = options.get('season')
        gameIds = []
        network = None

        date = dict(zip(['month', 'day', 'year'], date.split('/')))
        if 1 <= int(date['month']) <= 6:
            url = BASE_URL.format(f"/schedules/{int(date['year'])-1}")
        else:
            url = BASE_URL.format(f"/schedules/{date['year']}")
        data = requests.get(url).json()
        
        if not week:
            url = BASE_URL.format('/currentWeek')
            week = requests.get(url).json()['week']
        if not season:
            url = BASE_URL.format('/currentWeek')
            season = requests.get(url).json()['seasonId']
        if not seasonType:
            url = BASE_URL.format('/currentWeek')
            tmp = requests.get(url).json()['seasonType']
            if tmp == "PRO":
                if not options.get('pro'):
                    tmp = "POST"
                    week = 22 if not week or week == 4 or week == 21 else week
            seasonType = tmp

        if options.get('date'):
            found = False
            for game in data['gameSchedules']:
                if game['gameDate'] == f"{'/'.join(date.values())}":
                    if team:
                        teams = [game['visitorTeamAbbr'], game['homeTeamAbbr']]
                        if team.upper() in teams:
                            gameIds.append(game['gameId'])
                            network = ' :: {}'.format(game['networkChannel'])
                            week = str(game['week'])
                            season = game['season']
                            seasonType = game['seasonType']
                            found = True
                            break
                    else:
                        gameIds.append(game['gameId'])
                        network = ' :: {}'.format(game['networkChannel'])
                        week = str(game['week'])
                        season = game['season']
                        seasonType = game['seasonType']
                        found = True
            if not found:
                date = '/'.join(date.values())
                irc.reply('Error: No games found on {}'.format(
                    f"{date if not team else date + ' for ' + team.upper()}"))
                return

        if seasonType.upper() in ['POST']:
            if int(week) <= 5: week += 17
        url = BASE_URL.format('/scores/{}/{}/{}'.format(
            season, seasonType.upper(), week
        ))
        try:
            scores = requests.get(url).json()['gameScores']
        except json.decoder.JSONDecodeError:
            irc.error('invalid input', Raise=True)
        except Exception as e:
            print(e)
            irc.error('something went wrong parsing data', Raise=True)

        new_scores = []
        if gameIds or team:
            for game in scores:
                if gameIds and not team:
                    if game['gameSchedule']['gameId'] in gameIds:
                        new_scores.append(game)
                if team:
                    teams = [game['gameSchedule']['visitorTeamAbbr'], game['gameSchedule']['homeTeamAbbr']]
                    if team.upper() in teams:
                        new_scores.append(game)
                        break
        else:
            new_scores = scores
                    
        week = int(week)
        if week >= 18: week -= 17
        if seasonType in ['PRE']:
            if week != 0:
                prefix = self._bold("Preseason Week {}:".format(week))
            else:
                prefix = self._bold("Hall of Fame Game:")
        elif seasonType in ['REG']:
            prefix = self._bold("Week {}:".format(week))
        else:
            prefix = self._bold("{}:")
            if new_scores[0]['gameSchedule']['gameType'] == "WC":
                prefix = prefix.format("Wildcard Weekend")
            elif new_scores[0]['gameSchedule']['gameType'] == "DIV":
                prefix = prefix.format("Divisional Round")
            elif new_scores[0]['gameSchedule']['gameType'] == "CON":
                prefix = prefix.format("Conference Finals")
            elif new_scores[0]['gameSchedule']['gameType'] == "PRO":
                prefix = prefix.format("Pro Bowl")
            elif new_scores[0]['gameSchedule']['gameType'] == "SB":
                prefix = prefix.format(f"Super Bowl {convert_to_numeral(int(season)-1965)}")
            else:
                prefix = prefix.format("Week {}".format(week))
        
        games = []
        print(new_scores)
        for game in new_scores:
            if len(new_scores) == 1:
                long_ = True
                home = "homeDisplayName"
                away = "visitorDisplayName"
                time_format = "dddd, M/D, h:mm A zz"
                sep = " :: "
                if not network:
                    for s in data['gameSchedules']:
                        if game['gameSchedule']['gameId'] == s['gameId']:
                            network = ' :: {}'.format(s['networkChannel'])
                            break
            else:
                long_ = False
                home = "homeTeamAbbr"
                away = "visitorTeamAbbr"
                time_format = "ddd h:mm A zz"
                sep = " "
                network = ''
            score = game['score']
            info = game['gameSchedule']
            time = f"{pendulum.from_timestamp(info['isoTime']/1000).in_tz('US/Eastern').format(time_format)}"
            if not score:
                string = (f"{info[away]} @ {info[home]}{sep}"
                          f"{time}{network}")
                if info['gameType'] == "SB":
                    string += f" :: {info['site']['siteFullname']}{' ({})'.format(info['site']['roofType'].title()) if info['site']['roofType'] else ''}, {info['site']['siteCity']}, {info['site']['siteState']}"
                games.append(string)
            else:
                if "FINAL" in score['phase']:
                    phase = score['phase']
                    if "OVERTIME" in phase:
                        phase = "Final/Overtime" if long_ else "F/OT"
                    else:
                        phase = "Final" if long_ else "F"
                    phase = self._color(phase, 'red')
                    h_score = score['homeTeamScore']['pointTotal']
                    v_score = score['visitorTeamScore']['pointTotal']
                    if v_score > h_score:
                        v_str = self._bold(f"{info[away]} {v_score}")
                        h_str = f"{info[home]} {h_score}"
                    elif h_score > v_score:
                        v_str = f"{info[away]} {v_score}"
                        h_str = self._bold(f"{info[home]} {h_score}")
                    else:
                        v_str = f"{info[away]} {v_score}"
                        h_str = f"{info[home]} {h_score}"
                    string = (f"{v_str} @ {h_str}{sep}{phase}")
                    if info['gameType'] == "SB":
                        string += f" :: {info['site']['siteFullname']}{' ({})'.format(info['site']['roofType'].title()) if info['site']['roofType'] else ''}, {info['site']['siteCity']}, {info['site']['siteState']}"
                    games.append(string)
                elif "PRE" in score['phase']:
                    string = (f"{info[away]} @ {info[home]}{sep}"
                              f"{time}{network}")
                    if info['gameType'] == "SB":
                        string += f" :: {info['site']['siteFullname']}{' ({})'.format(info['site']['roofType'].title()) if info['site']['roofType'] else ''}, {info['site']['siteCity']}, {info['site']['siteState']}"
                    games.append(string)
                elif "HALFTIME" in score['phase']:
                    phase = "Halftime" if long_ else "HT"
                    phase = self._color(phase, 'orange')
                    h_score = score['homeTeamScore']['pointTotal']
                    v_score = score['visitorTeamScore']['pointTotal']
                    if v_score > h_score:
                        v_str = self._bold(f"{info[away]} {v_score}")
                        h_str = f"{info[home]} {h_score}"
                    elif h_score > v_score:
                        v_str = f"{info[away]} {v_score}"
                        h_str = self._bold(f"{info[home]} {h_score}")
                    else:
                        v_str = f"{info[away]} {v_score}"
                        h_str = f"{info[home]} {h_score}"
                    string = (f"{v_str} @ {h_str}{sep}{phase}")
                    games.append(string)
                else:
                    phase = score['phaseDescription'] if long_ else score['phase']
                    phase = self._color(phase, 'green')
                    time = self._color(score['time'], 'green')
                    h_score = score['homeTeamScore']['pointTotal']
                    v_score = score['visitorTeamScore']['pointTotal']
                    if v_score > h_score:
                        v_str = self._bold(f"{info[away]} {v_score}")
                        h_str = f"{info[home]} {h_score}"
                    elif h_score > v_score:
                        v_str = f"{info[away]} {v_score}"
                        h_str = self._bold(f"{info[home]} {h_score}")
                    else:
                        v_str = f"{info[away]} {v_score}"
                        h_str = f"{info[home]} {h_score}"
                    string = (f"{v_str} @ {h_str}{sep}{time} {phase}")
                    status = None
                    try:
                        pos_team = score.get('possessionTeamAbbr')
                        at = score['yardline']
                        down = "{} and {}".format(score['down'], score['yardsToGo'])
                        status = " :: {}".format(down)
                        last_play = None
                        if pos_team:
                            status += " :: {} has the ball at {}".format(pos_team, at)
                        if len(new_scores) == 1:
                            gameId = info['gameId']
                            url = BASE_URL.format('/playbyplay/{}/latest'.format(gameId))
                            try:
                                last_play = requests.get(url).json()
                                last_play = last_play['plays'][-1]['playDescription']
                            except:
                                pass
                        if last_play:
                            status += " :: {}".format(last_play)
                    except:
                        pass
                    if status:
                        string += status
                    games.append(string)

        irc.reply(f"{prefix} {' | '.join(games)}")
        


    @wrap([ "text"])
    def nflgame(self, irc, msg, args, player):
        """<player name>
        Fetches current/previous game stats for given player.
        """
        player_id = None
        try:
            try:
                burl = "site:nfl.com {} stats".format(player.lower())
                search = self.GOOG.search('{0}'.format(burl),'#reddit-nfl',{'smallsearch': True})
                search = self.GOOG.decode(search)
                if search:
                    url = search[0]['url']
                    print(url)
                    player_id = url.split('/')[-2]
                    player_id = player_id.replace('-', ' ')
                    print(player_id)
                
            except:
                self.log.exception("ERROR :: NFL :: failed to get link for {0}".format(burl))
                pass
        except Exception as e:
            self.log.info("ERROR :: NFL :: {0}".format(e))
            pass
        
        if not player_id:
            irc.reply('ERROR: Could not find a player id for {}'.format(player))
            return
        
        endpoint = '/playerGameStats/{}'.format(player_id)
        data = requests.get(BASE_URL.format(endpoint)).json()
        game_stats = data['playerGameStats']
        player_info = data['teamPlayer']

        if not game_stats:
            irc.reply("I couln't find any current or previous game stats for {}".format(player_info['displayName']))
            return
        
        recent = game_stats[-1]
        
        name = (f"{self._bold(self._color(player_info['displayName'], 'red'))}"
                f" (#{player_info['jerseyNumber']} {player_info['position']})"
                f" [{player_info['yearsOfExperience']}yrs exp]"
                f" :: {player_info['teamFullName']}")
        
        game_time = recent['gameSchedule']['isoTime'] / 1000
        info = (f"{recent['gameSchedule']['visitorTeamAbbr']} "
                f"{recent['score']['visitorTeamScore']['pointTotal']} @ "
                f"{recent['gameSchedule']['homeTeamAbbr']} "
                f"{recent['score']['homeTeamScore']['pointTotal']} - "
                f"{pendulum.from_timestamp(game_time).in_tz('US/Eastern').format('ddd MM/DD h:mm A zz')}")

        if player_info['positionGroup'] == 'QB':
            #passing, rush, fumble
            tmp = recent['playerPassingStat']
            stats = [(f"{self._ul('Passing')}: {self._bold('Comp')} {tmp.get('passingCompletions', '-')} "
                      f"{self._bold('Att')} {tmp.get('passingAttempts', '-')} "
                      f"{self._bold('Pct')} {tmp.get('passingCompletionPercentage', '-')} "
                      f"{self._bold('Yds')} {tmp.get('passingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('passingYardsPerAttempts', '-')} "
                      f"{self._bold('TD')} {tmp.get('passingTouchdowns', '-')} "
                      f"{self._bold('Int')} {tmp.get('passingInterceptions', '-')} "
                      f"{self._bold('Sck')} {tmp.get('passingSacked', '-')} "
                      f"{self._bold('SckY')} {tmp.get('passingSackedYardsLost', '-')} "
                      f"{self._bold('Rate')} {tmp.get('passingRating', '-')}")]
            tmp = recent['playerRushingStat']
            line2 = []
            line2.append(
                     (f"{self._ul('Rushing')}: {self._bold('Att')} {tmp.get('rushingAttempts', '-')} "
                      f"{self._bold('Yds')} {tmp.get('rushingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('rushingYardsPerAttempt', '-')} "
                      f"{self._bold('TD')} {tmp.get('rushingTouchdowns', '-')}"))
            tmp = recent['playerFumbleStat']
            line2.append(
                     (f"{self._ul('Fumbles')}: {self._bold('Fum')} {tmp.get('fumbles', '-')} "
                      f"{self._bold('Lst')} {tmp.get('fumblesLost', '-')}"))
            stats.append(' :: '.join(line2))
        elif player_info['positionGroup'] == 'RB':
            #rush, recev, fumble
            line1 = []
            line2 = []
            stats = []
            tmp = recent['playerRushingStat']
            line1 = [(f"{self._ul('Rushing')}: {self._bold('Att')} {tmp.get('rushingAttempts', '-')} "
                      f"{self._bold('Att')} {tmp.get('rushingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('rushingYardsPerAttempt', '-')} "
                      f"{self._bold('Lng')} {tmp.get('rushingLong', '-')} "
                      f"{self._bold('TD')} {tmp.get('rushingTouchdowns', '-')}")] if tmp else []
            tmp = recent['playerReceivingStat']
            if tmp: line1.append(
                     (f"{self._ul('Receiving')}: {self._bold('Rec')} {tmp.get('receivingReceptions', '-')} "
                      f"{self._bold('Yds')} {tmp.get('receivingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('receivingYardsPerReception', '-')} "
                      f"{self._bold('Lng')} {tmp.get('receivingLong', '-')} "
                      f"{self._bold('TD')} {tmp.get('receivingTouchdowns', '-')}"))
            tmp = recent['playerFumbleStat']
            line2.append(
                     (f"{self._ul('Fumbles')}: {self._bold('Fum')} {tmp.get('fumbles', '-')} "
                      f"{self._bold('Lst')} {tmp.get('fumblesLost', '-')}"))
            if len(line1) == 1 and len(line2) == 1:
                stats.append('{} :: {}'.format(line1[0], line2[0]))
            else:
                if line1: stats.append(' :: '.join(line1))
                if line2: stats.append(' :: '.join(line2))
        elif player_info['positionGroup'] in ['WR', 'TE']:
            #recv, rush, fumble
            line1 = []
            line2 = []
            stats = []
            tmp = recent['playerReceivingStat']
            line1 = [(f"{self._ul('Receiving')}: {self._bold('Rec')} {tmp.get('receivingReceptions', '-')} "
                      f"{self._bold('Yds')} {tmp.get('receivingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('receivingYardsPerReception', '-')} "
                      f"{self._bold('Lng')} {tmp.get('receivingLong', '-')} "
                      f"{self._bold('TD')} {tmp.get('receivingTouchdowns', '-')}")] if tmp else []
            tmp = recent['playerRushingStat']
            if tmp: line1.append(
                     (f"{self._ul('Rushing')}: {self._bold('Att')} {tmp.get('rushingAttempts', '-')} "
                      f"{self._bold('Att')} {tmp.get('rushingYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('rushingYardsPerAttempt', '-')} "
                      f"{self._bold('Lng')} {tmp.get('rushingLong', '-')} "
                      f"{self._bold('TD')} {tmp.get('rushingTouchdowns', '-')}"))
            tmp = recent['playerFumbleStat']
            line2.append(
                     (f"{self._ul('Fumbles')}: {self._bold('Fum')} {tmp.get('fumbles', '-')} "
                      f"{self._bold('Lst')} {tmp.get('fumblesLost', '-')}"))
            if len(line1) == 1 and len(line2) == 1:
                stats.append('{} :: {}'.format(line1[0], line2[0]))
            else:
                if line1: stats.append(' :: '.join(line1))
                if line2: stats.append(' :: '.join(line2))
        elif player_info['position'] == 'K':
            #overall fg, pats, koffs
            line1 = []
            line2 = []
            stats = []
            tmp = recent['playerKickingStat']
            line1 = [(f"{self._ul('Field Goals')}: {self._bold('FG Att')} {tmp.get('kickingFgAttempts', '-')} "
                      f"{self._bold('FGM')} {tmp.get('kickingFgMade', '-')} "
                      f"{self._bold('Pct')} {tmp.get('kickingFgPercentage', '-')} "
                      f"{self._bold('Lng')} {tmp.get('kickingFgLong', '-')} "
                      f"{self._bold('Blk')} {tmp.get('kickingFgBlocked', '-')}")] if tmp else []
            if tmp: line1.append(
                     (f"{self._ul('PATs')}: {self._bold('XP Att')} {tmp.get('kickingXkAttempts', '-')} "
                      f"{self._bold('XPM')} {tmp.get('kickingXkMade', '-')} "
                      f"{self._bold('Pct')} {tmp.get('kickingXkPercentage', '-')} "
                      f"{self._bold('Blk')} {tmp.get('kickingXkBlocked', '-')} "))
            line2.append(
                     (f"{self._ul('Kickoffs')}: {self._bold('KO')} {tmp.get('kickoffs', '-')} "
                      f"{self._bold('Avg')} {tmp.get('kickoffAverageYards', '-')} "
                      f"{self._bold('TB')} {tmp.get('kickoffTouchbacks', '-')} "
                      f"{self._bold('Ret')} {tmp.get('kickoffReturns', '-')} "
                      f"{self._bold('Avg')} {tmp.get('kickoffReturnsAverageYards', '-  ')}"))
            if len(line1) == 1 and len(line2) == 1:
                stats.append('{} :: {}'.format(line1[0], line2[0]))
            else:
                if line1: stats.append(' :: '.join(line1))
                if line2: stats.append(' :: '.join(line2))
        elif player_info['positionGroup'] in ['LB', 'DB', 'DL']:
            #defense
            line1 = []
            line2 = []
            stats = []
            tmp = recent['playerDefensiveStat']
            line1 = [(f"{self._ul('Tackles')}: {self._bold('Comb')} {tmp.get('defensiveCombineTackles', '-')} "
                      f"{self._bold('Total')} {tmp.get('defensiveTotalTackles', '-')} "
                      f"{self._bold('Ast')} {tmp.get('defensiveAssist', '-')} "
                      f"{self._bold('Sck')} {tmp.get('defensiveSacks', '-')} "
                      f"{self._bold('SFTY')} {tmp.get('defensiveSafeties', '-')}")] if tmp else []
            if tmp: line1.append(
                     (f"{self._ul('Interceptions')}: {self._bold('PDef')} {tmp.get('defensivePassesDefensed', '-')} "
                      f"{self._bold('Int')} {tmp.get('defensiveInterceptions', '-')} "
                      f"{self._bold('Yds')} {tmp.get('defensiveInterceptionYards', '-')} "
                      f"{self._bold('Avg')} {tmp.get('defensiveInterceptionsAvgyds', '-')} "
                      f"{self._bold('Lng')} {tmp.get('defensiveInterceptionsLong', '-')} "
                      f"{self._bold('TDs')} {tmp.get('defensiveInterceptionsTds', '-')} "))
            line2.append(
                     (f"{self._ul('Fumbles')}: {self._bold('FF')} {tmp.get('kickoffs', '-')} "))
            if len(line1) == 1 and len(line2) == 1:
                stats.append('{} :: {}'.format(line1[0], line2[0]))
            else:
                if line1: stats.append(' :: '.join(line1))
                if line2: stats.append(' :: '.join(line2))
        elif player_info['position'] == 'P':
            line1 = []
            stats = []
            tmp = recent['playerPuntingStat']
            line1 = [(f"{self._ul('Punting')}: {self._bold('Punts')} {tmp.get('puntingPunts', '-')} "
                      f"{self._bold('Yds')} {tmp.get('puntingYards', '-')} "
                      f"{self._bold('Net Yds')} {tmp.get('puntingNetYardage', '-')} "
                      f"{self._bold('Lng')} {tmp.get('puntingLong', '-')} "
                      f"{self._bold('Avg')} {tmp.get('puntingAverageYards', '-')} "
                      f"{self._bold('Net Avg')} {tmp.get('puntingNetAverage', '-')} "
                      f"{self._bold('Blk')} {tmp.get('puntingBlocked', '-')} "
                      f"{self._bold('OOB')} {tmp.get('puntingOutOfBounds', '-')} "
                      f"{self._bold('Dn')} {tmp.get('puntingDowned', '-')} "
                      f"{self._bold('In 20')} {tmp.get('puntingPuntsInside20', '-')} "
                      f"{self._bold('TB')} {tmp.get('puntingTouchbacks', '-')} "
                      f"{self._bold('FC')} {tmp.get('puntingPuntsFairCaught', '-')} "
                      f"{self._bold('Ret')} {tmp.get('puntingNumberReturned', '-')} "
                      f"{self._bold('RetY')} {tmp.get('puntingReturnYards', '-')} "
                      f"{self._bold('TD')} {tmp.get('puntingReturnTouchdowns', '-')}")] if tmp else []
            stats.append(' :: '.join(line1))
        else:
            stats = ["No stats found"]
        
        strings = [f"{name} :: {info}"]
        
        for string in strings:
            irc.reply(string)
        for stat in stats:
            irc.reply(stat)

    def _color(self, string, color):
        return ircutils.mircColor(string, color)

    def _bold(self, string):
        return ircutils.bold(string)

    def _ul(self, string):
        return ircutils.underline(string)        
        

Class = NFL


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
