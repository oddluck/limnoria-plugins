###
# Copyright (c) 2010, quantumlemur
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

import time
import string
import random
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks


class Timebomb(callbacks.Plugin):
    """Add the help for "@plugin help Timebomb" here
    This should describe *how* to use this plugin."""
    threaded = True
    
    def __init__(self, irc):
        self.__parent = super(Timebomb, self)
        self.__parent.__init__(irc)
        self.rng = random.Random()
        self.rng.seed()
        self.bombs = {}
        self.lastBomb = ""
        self.talktimes = {}


    def doPrivmsg(self, irc, msg):
        self.talktimes[msg.nick] = time.time()


    def doJoin(self, irc, msg):
        if self.registryValue('joinIsActivity', msg.args[0]):
            self.talktimes[msg.nick] = time.time()


    class Bomb():
        def __init__(self, irc, victim, wires, detonateTime, goodWire, channel, sender, showArt, showCorrectWire, debug):
            self.victim = victim
            self.detonateTime = detonateTime
            self.wires = wires
            self.goodWire = goodWire
            self.active = True
            self.channel = channel
            self.sender = sender
            self.irc = irc
            self.showArt = showArt
            self.showCorrectWire = showCorrectWire
            self.debug = debug
            self.thrown = False
            self.responded = False
            self.rng = random.Random()
            self.rng.seed()
            if self.debug:
                self.irc.reply('I just created a bomb in %s' % channel)
            def detonate():
                self.detonate(irc)
            schedule.addEvent(detonate, time.time() + self.detonateTime, '%s_bomb' % self.channel)
            s = 'stuffs a bomb down %s\'s pants.  The timer is set for %s seconds!  There are %s wires.  They are: %s.' % (self.victim, self.detonateTime, len(wires), utils.str.commaAndify(wires))
            self.irc.queueMsg(ircmsgs.action(self.channel, s))
            if self.victim == irc.nick:
                time.sleep(1)
                cutWire = self.rng.choice(self.wires)
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '@cutwire %s' % cutWire))
                time.sleep(1)
                self.cutwire(self.irc, cutWire)

        def cutwire(self, irc, cutWire):
            self.cutWire = cutWire
            self.responded = True
            if self.thrown == True:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, 'You don\'t have the coordination to cut wires on bombs in midair while they\'re flying towards your head!  Ducking might be a better idea.'))
            else:
                if self.goodWire.lower() == self.cutWire.lower():
                    self.irc.queueMsg(ircmsgs.privmsg(self.channel, '%s has cut the %s wire!  This has defused the bomb!' % (self.victim, self.cutWire)))
                    self.irc.queueMsg(ircmsgs.privmsg(self.channel, 'He then quickly rearms the bomb and throws it back at %s with just seconds on the clock!' % self.sender))
                    self.victim = self.sender
                    self.thrown = True
                    schedule.rescheduleEvent('%s_bomb' % self.channel, time.time() + 5)
                    if self.victim == irc.nick:
                        time.sleep(1)
                        self.irc.queueMsg(ircmsgs.privmsg(self.channel, '@duck'))
                        time.sleep(1)
                        self.duck(self.irc, irc.nick)
                else:
                    schedule.removeEvent('%s_bomb' % self.channel)
                    self.detonate(irc)

        def duck(self, irc, ducker):
            if self.thrown and ircutils.nickEqual(self.victim, ducker):
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '%s ducks!  The bomb misses, and explodes harmlessly a few meters away.' % self.victim))
                self.active = False
                self.thrown = False
                schedule.removeEvent('%s_bomb' % self.channel)

        def detonate(self, irc):
            self.active = False
            self.thrown = False
            if self.showCorrectWire:
                self.irc.reply('Should\'ve gone for the %s wire!' % self.goodWire)
            if self.showArt:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1.....\x0315,1_.\x0314,1-^^---....,\x0315,1,-_\x031,1.......'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1.\x0315,1_--\x0314,1,.\';,`.,\';,.;;`;,.\x0315,1--_\x031,1...'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x0315,1<,.\x0314,1;\'`".,;`..,;`*.,\';`.\x0315,1;\'>)\x031,1.'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x0315,1I.:;\x0314,1.,`;~,`.;\'`,.;\'`,..\x0315,1\';`I\x031,1.'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1.\x0315,1\\_.\x0314,1`\'`..`\';.,`\';,`\';,\x0315,1_../\x031,1..'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1....\x0315,1```\x0314,1--. . , ; .--\x0315,1\'\'\'\x031,1.....'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1..........\x034,1I\x031,1.\x038,1I\x037,1I\x031,1.\x038,1I\x034,1I\x031,1...........'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1..........\x034,1I\x031,1.\x037,1I\x038,1I\x031,1.\x037,1I\x034,1I\x031,1...........'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1.......,\x034,1-=\x034,1II\x037,1..I\x034,1.I=-,\x031,1........'))
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, '\x031,1.......\x034,1`-=\x037,1#$\x038,1%&\x037,1%$#\x034,1=-\'\x031,1........'))
            else:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, 'KABOOM!'))
            self.irc.queueMsg(ircmsgs.kick(self.channel, self.victim, 'BOOM!'))
            def reinvite():
                if not self.victim in irc.state.channels[self.channel].users:
                    self.irc.queueMsg(ircmsgs.invite(self.victim, self.channel))
            if not self.responded:
                schedule.addEvent(reinvite, time.time()+5)
                
    
    def duck(self, irc, msg, args, channel):
        """takes no arguments

        DUCK!"""
        channel = ircutils.toLower(channel)
        try:
            if not self.bombs[channel].active:
                return
        except KeyError:
            return
        self.bombs[channel].duck(irc, msg.nick)
        irc.noReply()
    duck = wrap(duck, ['Channel'])

   
    def randombomb(self, irc, msg, args, channel, nicks):
        """takes no arguments

        Bombs a random person in the channel
        """
        channel = ircutils.toLower(channel)
        if not self.registryValue('allowBombs', msg.args[0]):
            irc.reply('Timebombs aren\'t allowed in this channel.  Set plugins.Timebomb.allowBombs to true if you want them.')
            return
        try:
            if self.bombs[channel].active:
                irc.reply('There\'s already an active bomb, in %s\'s pants!' % self.bombs[channel].victim)
                return
        except KeyError:
            pass
        if self.registryValue('bombActiveUsers', msg.args[0]):
            if len(nicks) == 0:
                nicks = list(irc.state.channels[channel].users)
                items = self.talktimes.iteritems()
                nicks = []
                for i in range(0, len(self.talktimes)):
                    try:
                        item = items.next()
                        if time.time() - item[1] < self.registryValue('idleTime', msg.args[0])*60 and item[0] in irc.state.channels[channel].users:
                            nicks.append(item[0])
                    except StopIteration:
                        irc.reply('hey quantumlemur, something funny happened... I got a StopIteration exception')
                if len(nicks) == 1 and nicks[0] == msg.nick:
                    nicks = []
            if len(nicks) == 0:
                irc.reply('Well, no one\'s talked in the past hour, so I guess I\'ll just choose someone from the whole channel')
                nicks = list(irc.state.channels[channel].users)
            elif len(nicks) == 2:
                irc.reply('Well, it\'s just been you two talking recently, so I\'m going to go ahead and just bomb someone at random from the whole channel')
                nicks = list(irc.state.channels[channel].users)
        elif len(nicks) == 0:
            nicks = list(irc.state.channels[channel].users)
        if irc.nick in nicks and not self.registryValue('allowSelfBombs', msg.args[0]):
            nicks.remove(irc.nick)
        #####
        #irc.reply('These people are eligible: %s' % utils.str.commaAndify(nicks))
        victim = self.rng.choice(nicks)
        while victim == self.lastBomb or victim in self.registryValue('exclusions', msg.args[0]):
            victim = self.rng.choice(nicks)
        self.lastBomb = victim
        detonateTime = self.rng.randint(self.registryValue('minRandombombTime', msg.args[0]), self.registryValue('maxRandombombTime', msg.args[0]))
        wireCount = self.rng.randint(self.registryValue('minWires', msg.args[0]), self.registryValue('maxWires', msg.args[0]))
        if wireCount < 12:
            colors = self.registryValue('shortcolors')
        else:
            colors = self.registryValue('colors')
        wires = self.rng.sample(colors, wireCount)
        goodWire = self.rng.choice(wires)
        self.bombs[channel] = self.Bomb(irc, victim, wires, detonateTime, goodWire, channel, msg.nick, self.registryValue('showArt', msg.args[0]), self.registryValue('showCorrectWire', msg.args[0]), self.registryValue('debug'))
        try:
            irc.noReply()
        except AttributeError:
            pass
    randombomb = wrap(randombomb, ['Channel', any('NickInChannel')])

 
    def timebomb(self, irc, msg, args, channel, victim):
        """<nick>

        For bombing people!"""
        channel = ircutils.toLower(channel)
        if not self.registryValue('allowBombs', msg.args[0]):
            irc.reply('Timebombs aren\'t allowed in this channel.  Set plugins.Timebomb.allowBombs to true if you want them.')
            return
        try:
            if self.bombs[channel].active:
                irc.reply('There\'s already an active bomb, in %s\'s pants!' % self.bombs[channel].victim)
                return
        except KeyError:
            pass
        if victim == irc.nick and not self.registryValue('allowSelfBombs', msg.args[0]):
            irc.reply('You really expect me to bomb myself?  Stuffing explosives into my own pants isn\'t exactly my idea of fun.')
            return
        victim = string.lower(victim)
        found = False
        for nick in list(irc.state.channels[channel].users):
            if victim == string.lower(nick):
                victim = nick
                found = True
        if not found:
            irc.reply('Error: nick not found.')
            return
        detonateTime = self.rng.randint(self.registryValue('minTime', msg.args[0]), self.registryValue('maxTime', msg.args[0]))
        wireCount = self.rng.randint(self.registryValue('minWires', msg.args[0]), self.registryValue('maxWires', msg.args[0]))
        if wireCount < 12:
            colors = self.registryValue('shortcolors')
        else:
            colors = self.registryValue('colors')
        wires = self.rng.sample(colors, wireCount)
        goodWire = self.rng.choice(wires)
        if self.registryValue('debug'):
            irc.reply('I\'m about to create a bomb in %s' % channel)
        self.bombs[channel] = self.Bomb(irc, victim, wires, detonateTime, goodWire, channel, msg.nick, self.registryValue('showArt', msg.args[0]), self.registryValue('showCorrectWire', msg.args[0]), self.registryValue('debug'))
        if self.registryValue('debug'):
            irc.reply('This message means that I got past the bomb creation line in the timebomb command')
    timebomb = wrap(timebomb, ['Channel', ('checkChannelCapability', 'timebombs'), 'somethingWithoutSpaces'])


    def cutwire(self, irc, msg, args, channel, cutWire):
        """<colored wire>

        Will cut the given wire if you've been timebombed."""
        channel = ircutils.toLower(channel)
        try:
            if not self.bombs[channel].active:
                return
            if not ircutils.nickEqual(self.bombs[channel].victim, msg.nick):
                irc.reply('You can\'t cut the wire on someone else\'s bomb!')
                return
            self.bombs[channel].cutwire(irc, cutWire)
        except KeyError:
            pass
        irc.noReply()
    cutwire = wrap(cutwire, ['Channel', 'something'])


    def detonate(self, irc, msg, args, channel):
        """Takes no arguments

        Detonates the active bomb."""
        channel = ircutils.toLower(channel)
        try:
            if self.bombs[channel].active:
                schedule.rescheduleEvent('%s_bomb' % channel, time.time())
        except KeyError:
            if self.registryValue('debug'):
                irc.reply('I tried to detonate a bomb in "%s"' % channel)
                irc.reply('List of bombs: %s' % self.bombs.keys())
        irc.noReply()
    detonate = wrap(detonate, [('checkChannelCapability', 'op')])


Class = Timebomb


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
