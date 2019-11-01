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
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
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
import math
import supybot.utils as utils
import supybot.world as world
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircdb as ircdb
import supybot.ircmsgs as ircmsgs
import supybot.ircutils as ircutils
import supybot.schedule as schedule
import supybot.callbacks as callbacks
import supybot.registry as registry
import supybot.conf as conf


class TimeBomb(callbacks.Plugin):
    """Add the help for "@plugin help TimeBomb" here
    This should describe *how* to use this plugin."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TimeBomb, self)
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

        def __init__(self, irc, victim, wires, detonateTime, goodWire,
                     channel, sender, showArt, showCorrectWire, debug):
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
            try:
                self.command_char = conf.supybot.reply.whenAddressedBy.chars()[0]
            except KeyError:
                self.command_char = ''
            if self.debug:
                self.irc.reply('I just created a bomb in {}'.format(channel))

            def detonate():
                self.detonate(irc)

            schedule.addEvent(detonate, time.time() + self.detonateTime, '{}_bomb'.format(self.channel))
            s = 'stuffs a bomb down {}\'s pants. The timer is set for {} seconds! There are {} wires. They are: {}.'.format(self.victim, self.detonateTime, len(wires), utils.str.commaAndify(wires))
            self.irc.queueMsg(ircmsgs.action(self.channel, s))
            self.irc.queueMsg(ircmsgs.privmsg(self.channel, "{}, try to defuse the bomb using the command: '{}cutwire \x02color\x02'".format(self.victim, self.command_char)))

            if self.victim == irc.nick:
                time.sleep(1)
                cutWire = self.rng.choice(self.wires)
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '$cutwire {}'.format(cutWire)))
                time.sleep(1)
                self.cutwire(self.irc, cutWire)

        def defuse(self):
            if not self.active:
                return

            self.active = False
            self.thrown = False
            schedule.removeEvent('{}_bomb'.format(self.channel))

        def cutwire(self, irc, cutWire):
            self.cutWire = cutWire
            self.responded = True
            specialWires = False

            if self.rng.randint(1, len(self.wires)) == 1:
                specialWires = True

            if self.cutWire.lower() == 'potato' and specialWires:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '{} has turned the bomb into a potato! This has rendered it mostly harmless, and slightly{}.'.format(self.victim, self.goodWire)))
                self.defuse()
            elif self.cutWire.lower() == 'pizza' and specialWires:
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '{0} has turned the bomb into a pizza! {0}\'s pants have been ruined by the pizza stuffed into them, but at least they haven\'t exploded.'.format(self.victim)))
                self.defuse()
            elif self.goodWire.lower() == self.cutWire.lower():
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '{} has cut the {} wire! This has defused the bomb!'.format(self.victim, self.cutWire)))

                if self.victim.lower() != self.sender.lower():
                    self.irc.queueMsg(ircmsgs.privmsg(self.channel, 'They then quickly rearm the bomb and throw it back at {} with just seconds on the clock!'.format(self.sender)))
                    tmp = self.victim
                    self.victim = self.sender
                    self.sender = tmp
                    self.thrown = True
                    schedule.rescheduleEvent('{}_bomb'.format(self.channel), time.time() + 10)

                    if self.victim == irc.nick:
                        time.sleep(1)
                        self.irc.queueMsg(ircmsgs.privmsg(self.channel, '@duck'))
                        time.sleep(1)
                        self.duck(self.irc, irc.nick)
                else:
                    self.defuse()
            else:
                schedule.removeEvent('{}_bomb'.format(self.channel))
                self.detonate(irc)

        def duck(self, irc, ducker):
            if self.thrown and ircutils.nickEqual(self.victim, ducker):
                self.irc.queueMsg(ircmsgs.privmsg(self.channel, '{} ducks! The bomb misses, and explodes harmlessly a few meters away.'.format(self.victim)))
                self.defuse()

        def detonate(self, irc):
            self.active = False
            self.thrown = False
            if self.showCorrectWire:
                self.irc.sendMsg(ircmsgs.privmsg(self.channel, 'Should\'ve gone for the {} wire!'.format(self.goodWire)))

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
                if self.showCorrectWire:
                    self.irc.queueMsg(ircmsgs.kick(self.channel, self.victim, 'BOOM! You should\'ve gone for the {} wire!'.format(self.goodWire)))
                    else
                    self.irc.queueMsg(ircmsgs.kick(self.channel, self.victim, 'BOOM!'))

            def reinvite():
                if self.victim not in irc.state.channels[self.channel].users:
                    self.irc.queueMsg(ircmsgs.invite(self.victim, self.channel))

            if not self.responded:
                schedule.addEvent(reinvite, time.time() + 5)

    def _canBomb(self, irc, channel, sender, victim, replyError):
        if sender.lower() in self.registryValue('exclusions', channel):
            if replyError:
                irc.reply('You can\'t timebomb anyone, since you\'re excluded from being timebombed')
            return False

        if sender not in irc.state.channels[channel].users:
            if replyError:
                irc.error(format('You must be in {} to timebomb in there.'.format(channel), Raise=True))
            return False
        bombHistoryOrig = self.registryValue('bombHistory', channel)
        bombHistory = []
        senderHostmask = irc.state.nickToHostmask(sender)
        (nick, user, host) = ircutils.splitHostmask(senderHostmask)
        senderMask = ('{}@{}'.format(user, host)).lower()
        victim = victim.lower()
        now = int(time.time())
        storeTime = self.registryValue('rateLimitTime', channel)
        victimCount = 0
        senderCount = 0
        totalCount = 0

        for bstr in bombHistoryOrig:
            b = bstr.split('#')
            if len(b) < 3 or int(b[0]) + storeTime < now:
                continue
            totalCount += 1

            if b[1] == senderMask:
                senderCount += 1

            if b[2] == victim:
                victimCount += 1
            bombHistory.append(bstr)
        self.setRegistryValue('bombHistory', bombHistory, channel)

        if (totalCount > storeTime *
                self.registryValue('rateLimitTotal', channel) / 3600):
            if replyError:
                irc.reply('Sorry, I\'ve stuffed so many timebombs down so many pairs of pants that I\'ve temporarily run out of explosives. You\'ll have to wait.')
            return False

        if (senderCount > storeTime *
            self.registryValue('rateLimitSender', channel) / 3600):

            if replyError:
                irc.reply('You\'ve timebombed a lot of people recently, let someone else have a go.')
            return False

        if (victimCount > storeTime *
            self.registryValue('rateLimitVictim', channel) / 3600):
            if replyError:
                irc.reply('That user has been timebombed a lot recently, try picking someone else.')
            return False
        return True

    def _logBomb(self, irc, channel, sender, victim):
        bombHistory = self.registryValue('bombHistory', channel)
        senderHostmask = irc.state.nickToHostmask(sender)
        (nick, user, host) = ircutils.splitHostmask(senderHostmask)
        senderMask = ('{}@{}'.format(user, host)).lower()
        victim = victim.lower()
        bombHistory.append('{}#{}#{}'.format(int(time.time()), senderMask, victim))
        self.setRegistryValue('bombHistory', bombHistory, channel)

    def bombsenabled(self, irc, msg, args, channel, value):
        """[value]

        Sets the value of the allowBombs config value for the channel. Restricted to users with channel timebombadmin capability."""
        statusDescription = 'are currently'
        if value:
            # tmp = ircdb.channels.getChannel(channel).defaultAllow - problems with multithreading?
            # ircdb.channels.getChannel(channel).defaultAllow = False
            hasCap = ircdb.checkCapability(msg.prefix, 'timebombadmin')
            if (channel == "#powder" or channel == "#powder-dev") and not ircdb.checkCapability(msg.prefix, 'admin'):
                irc.error('You need the admin capability to do that')
                return
            # ircdb.channels.getChannel(channel).defaultAllow = tmp

            if hasCap:
                oldValue = self.registryValue('allowBombs', channel)
                try:
                    conf.supybot.plugins.TimeBomb.allowBombs.get(channel).set(value)
                except registry.InvalidRegistryValue:
                    irc.error('Value must be either True or False (or On or Off)')
                    return
                if self.registryValue('allowBombs', channel) == oldValue:
                    statusDescription = 'were already'
                else:
                    statusDescription = 'have now been'
            else:
                irc.error('You need the timebombadmin capability to do that')
                return

        if self.registryValue('allowBombs', channel):
            irc.reply('TimeBombs {} enabled in{}'.format(statusDescription, channel))
        else:
            irc.reply('TimeBombs {} disabled in{}'.format(statusDescription, channel))
    bombsenabled = wrap(bombsenabled, ['Channel', optional('somethingWithoutSpaces')])

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
        if not self.registryValue('allowBombs', channel):
            irc.reply('TimeBombs aren\'t allowed in this channel. Set plugins.TimeBomb.allowBombs to true if you want them.')
            return
        try:
            if self.bombs[channel].active:
                irc.reply('There\'s already an active bomb, in{}\'s pants!'.format(self.bombs[channel].victim))
                return
        except KeyError:
            pass

        if not self._canBomb(irc, channel, msg.nick, '', True):
            return

        if self.registryValue('bombActiveUsers', channel):
            if len(nicks) == 0:
                nicks = list(irc.state.channels[channel].users)
                items = iter(list(self.talktimes.items()))
                nicks = []
                count = 0

                while count < len(self.talktimes):
                    try:
                        item = next(items)
                        if time.time() - item[1] < self.registryValue('idleTime', channel) * 60 and item[0] in irc.state.channels[channel].users and self._canBomb(irc, channel, msg.nick, item[0], False):
                            nicks.append(item[0])
                    except StopIteration:
                        irc.reply('Something funny happened... I got a StopIteration exception')
                    count += 1
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

        if irc.nick in nicks and not self.registryValue('allowSelfBombs', channel):
            nicks.remove(irc.nick)
        eligibleNicks = []

        for victim in nicks:
            if not (victim == self.lastBomb or victim.casefold() in self.registryValue('randomExclusions', channel) or victim.casefold() in self.registryValue('exclusions', channel)) and self._canBomb(irc, channel, msg.nick, victim, False):
                eligibleNicks.append(victim)

        if len(eligibleNicks) == 0:
            irc.reply('I couldn\'t find anyone suitable to randombomb. Maybe everyone here is excluded from being randombombed or has been timebombed too recently.')
            return
        #####
        # irc.reply('These people are eligible: {}'.format(utils.str.commaAndify(eligibleNicks)))
        victim = self.rng.choice(eligibleNicks)
        self.lastBomb = victim
        detonateTime = self.rng.randint(self.registryValue('minRandombombTime', channel), self.registryValue('maxRandombombTime', channel))
        wireCount = self.rng.randint(self.registryValue('minWires', channel), self.registryValue('maxWires', channel))

        if wireCount < 12:
            colors = self.registryValue('shortcolors')
        else:
            colors = self.registryValue('colors')

        wires = self.rng.sample(colors, wireCount)
        goodWire = self.rng.choice(wires)
        self.log.info("TimeBomb: Safewire is {}".format(goodWire))
        self._logBomb(irc, channel, msg.nick, victim)
        self.bombs[channel] = self.Bomb(irc, victim, wires, detonateTime, goodWire, channel, msg.nick, self.registryValue('showArt', channel), self.registryValue('showCorrectWire', channel), self.registryValue('debug'))

        try:
            irc.noReply()
        except AttributeError:
            pass
    randombomb = wrap(randombomb, ['Channel', any('NickInChannel')])

    def timebomb(self, irc, msg, args, channel, victim):
        """<nick>

        For bombing people!"""
        channel = ircutils.toLower(channel)
        if not self.registryValue('allowBombs', channel):
            irc.reply('TimeBombs aren\'t allowed in this channel. Set plugins.TimeBomb.allowBombs to true if you want them.')
            return
        try:
            if self.bombs[channel].active:
                irc.reply('There\'s already an active bomb, in{}\'s pants!'.format(self.bombs[channel].victim))
                return
        except KeyError:
            pass

        if victim.lower() == irc.nick.lower() and not self.registryValue('allowSelfBombs', channel):
            irc.reply('You really expect me to bomb myself? Stuffing explosives into my own pants isn\'t exactly my idea of fun.')
            return
        victim = victim.casefold()
        found = False

        for nick in list(irc.state.channels[channel].users):
            if victim == nick.casefold():
                victim = nick
                found = True
        if not found:
            irc.reply('Error: nick not found.')
            return
        if victim.casefold() in self.registryValue('exclusions', channel):
            irc.reply('Error: that nick can\'t be timebombed')
            return

        # not (victim == msg.nick and victim == 'mniip') and
        if not ircdb.checkCapability(msg.prefix, 'admin') and not self._canBomb(irc, channel, msg.nick, victim, True):
            return

        detonateTime = self.rng.randint(self.registryValue('minTime', channel), self.registryValue('maxTime', channel))
        wireCount = self.rng.randint(self.registryValue('minWires', channel), self.registryValue('maxWires', channel))
        # if victim.lower() == 'halite' or (victim == msg.nick and victim == 'mniip'):
        #    wireCount = self.rng.randint(11,20)
        if wireCount < 12:
            colors = self.registryValue('shortcolors')
        else:
            colors = self.registryValue('colors')

        wires = self.rng.sample(colors, wireCount)
        goodWire = self.rng.choice(wires)
        self.log.info("TimeBomb: Safewire is {}".format(goodWire))

        if self.registryValue('debug'):
            irc.reply('I\'m about to create a bomb in{}'.format(channel))

        # if not (victim == msg.nick and victim == 'mniip'):
        self._logBomb(irc, channel, msg.nick, victim)
        self.bombs[channel] = self.Bomb(irc, victim, wires, detonateTime, goodWire, channel, msg.nick, self.registryValue('showArt', channel), self.registryValue('showCorrectWire', channel), self.registryValue('debug'))
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

            if not ircutils.nickEqual(self.bombs[channel].victim, msg.nick) and not ircdb.checkCapability(msg.prefix, 'admin'):
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
                schedule.rescheduleEvent('{}_bomb'.format(channel), time.time())
        except KeyError:
            if self.registryValue('debug'):
                irc.reply('I tried to detonate a bomb in "{}"'.format(channel))
                irc.reply('List of bombs: {}'.format(", ".join(list(self.bombs.keys()))))
        irc.noReply()
    detonate = wrap(detonate, [('checkChannelCapability', 'op')])

    def defuse(self, irc, msg, args, channel):
        """Takes no arguments

        Defuses the active bomb (channel ops only)"""
        channel = ircutils.toLower(channel)
        try:
            if self.bombs[channel].active:
                if ircutils.nickEqual(self.bombs[channel].victim, msg.nick) and not (ircutils.nickEqual(self.bombs[channel].victim, self.bombs[channel].sender) or ircdb.checkCapability(msg.prefix, 'admin')):
                    irc.reply('You can\'t defuse a bomb that\'s in your own pants, you\'ll just have to cut a wire and hope for the best.')
                    return
                self.bombs[channel].defuse()
                irc.reply('Bomb defused')
            else:
                irc.error('There is no active bomb')
        except KeyError:
            pass
            irc.error('There is no active bomb')
    defuse = wrap(defuse, [('checkChannelCapability', 'op')])


Class = TimeBomb


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
