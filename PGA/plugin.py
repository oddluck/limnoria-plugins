###
# Copyright (c) 2018, cottongin
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
#   * Redistributions of source code must retain the above copyright notice,
#     this list of conditions, and the following disclaimer.
#   * Redistributions in binary form must reproduce the above copyright notice,
#     this list of conditions, and the following disclaimer in the
#     documentation and/or other materials provided with the distribution.
#   * Neither the name of the author of this software nor the name of
#     contributors to this software may be used to endorse or promote products
#     derived from this software without specific prior written consent.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED.  IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
###

import pendulum
import requests

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('PGA')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

CURRENT_URL = 'https://statdata.pgatour.com/{trn_type}/current/message.json'
SCOREBOARD = 'https://statdata.pgatour.com/{trn_type}/{trn_id}/leaderboard-v2mini.json'

class PGA(callbacks.Plugin):
    """Fetches golf scores"""
    threaded = True
    
    def _fetchCurrent(self, type_='r'):
        tmp = None
        try:
            jdata = requests.get(CURRENT_URL.format(trn_type=type_)).json()
            tmp = jdata['tid']
            return [type_, tmp]
        except:
            return [type_, tmp]
        return [type_, tmp]
    
    @wrap([getopts({'all': '', 'info': '', 'champions': ''}), optional('text')])
    def golf(self, irc, msg, args, options, search=None):
        """ [player name]
        Fetches leaderboard for active or previous tournament, 
        optionally pass a name to find player in standings
        """
        options = dict(options)
        type_is_champions = options.get('champions')
        
        if type_is_champions:
            trn = self._fetchCurrent(type_='s')
        else:
            trn = self._fetchCurrent()
        if not trn[1]:
            irc.reply('Something went wrong getting the current/previous tournament')
            return
        
        if options.get('info'):
            url = 'https://www.pgatour.com/bin/data/feeds/weather.json/{}{}'.format(
                trn[0], trn[1])
            print(url)
            idata = requests.get(url).json()
            url2 = 'https://statdata.pgatour.com/r/current/schedule-v2.json' #.format(trn[0])
            #print(url2)
            sdata = requests.get(url2).json()
            #print(sdata)
        
        # now get the leaderboard json
        try:
            jdata = requests.get(SCOREBOARD.format(trn_type=trn[0], trn_id=trn[1]))
            print(jdata.url)
            jdata = jdata.json()
        except:
            irc.reply('Something went wrong fetching the leaderboard')
            return
        
        leaderboard = jdata.get('leaderboard')
        if not leaderboard:
            irc.reply('No leaderboard found')
            return
        
        name = ircutils.bold(leaderboard['tournament_name'])
        date = "{}-{}".format(
            pendulum.parse(leaderboard['start_date'], strict=False).format('MMMD'),
            pendulum.parse(leaderboard['end_date'], strict=False).format('MMMD'))
        
        round_ = 'Round {}'.format(leaderboard['current_round'])
        if leaderboard['round_state']:
            round_ += ' ({})'.format(leaderboard['round_state'])
            
        cut_line = leaderboard['cut_line'].get('cut_count') or len(leaderboard['players'])
        
        positions = []
        if not options.get('info'):
            for idx, player in enumerate(leaderboard['players']):
                if player['player_bio']['short_name']:
                    plyr_name = '{}.{}'.format(player['player_bio']['short_name'].replace('.', ''),
                                               player['player_bio']['last_name'])
                else:
                    plyr_name = '{}'.format(player['player_bio']['last_name'])
                full_name = '{} {}'.format(player['player_bio']['first_name'],
                                           player['player_bio']['last_name'])
                if idx >= cut_line:
                    if player['status'] == 'wd':
                        rank = ircutils.mircColor('WD', 'orange')
                    else:
                        rank = ircutils.mircColor('CUT', 'red')
                else:
                    rank = str(player['current_position'])
                if player['thru']:
                    thru = ' {:+d} thru {} '.format(player['today'], ircutils.mircColor(str(player['thru']), 'green')) \
                    if player['thru'] != 18 else ' {:+d}'.format(player['today']) + ircutils.bold(ircutils.mircColor(' F ', 'red'))
                else:
                    thru = ' '
                score = '{:+d}'.format(player['total']) if player['total'] else '-'
                string = '{} {}{}({})'.format(
                    ircutils.bold(ircutils.mircColor(rank, 'blue')),
                    plyr_name,
                    thru,
                    score)
                if search:
                    if search.lower() in full_name.lower():
                        positions.append(string)
                else:
                    positions.append(string)

            if not positions:
                positions.append('Player not found')
                #return
            
        if options.get('info'):
            loc = idata['current_observation']['display_location']['full']
            weather = idata['current_observation']['weather']
            try:
                temp = idata['current_observation']['temperature_string']
                wind = idata['current_observation']['wind_string']
            except:
                temp = "{}F".format(idata['current_observation']['temp_f'])
                wind = "{}mph {}".format(idata['current_observation']['wind_mph'], idata['current_observation']['wind_dir'])
            w_string = '{} :: {} - {} - Wind: {}'.format(loc, weather, temp, wind)
            year = sdata['currentYears'][trn[0]]
            for item in sdata['years']:
                if item['year'] == year:
                    data = item['tours']
                    for t in data:
                        if t['tourCodeLc'] == trn[0]:
                            tdata = t['trns']
            for tour in tdata:
                if tour['permNum'] == trn[1]:
                    tmp = tour
                    break
            course = tmp['courses'][0]['courseName']
            purse = tmp['Purse']
            winnerPrize = tmp['winnersShare']
            defending = '{} {}'.format(tmp['champions'][0]['playerName']['first'], tmp['champions'][0]['playerName']['last'])
            w_string += ' :: {} :: \x02Defending champion:\x02 {} :: \x02Purse:\x02 ${} (${} to winner)'.format(
                course, defending, purse, winnerPrize)
            positions.append(w_string)
            
        trunc = 10 if not options.get('all') else len(positions)
        
        irc.reply('{} ({}) :: {} :: {}'.format(name, date, round_,
                                               ', '.join(p for p in positions[:trunc])))
        
        return


Class = PGA


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
