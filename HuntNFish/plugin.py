###
# Copyright (c) 2012, resistivecorpse
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

import os
import time
import random as random
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('HuntNFish')

@internationalizeDocstring
class HuntNFish(callbacks.Plugin):
    """Adds hunt and fish commands for a basic hunting and fishing game."""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(HuntNFish, self)
        self.__parent.__init__(irc)
        self._huntersEndTime = {}
        self._fishersEndTime = {}

    def hunt(self,irc,msg,args):
        """takes no arguments
        performs a random hunt
        """
        channel = msg.args[0]
        if not irc.isChannel(channel):
           irc.reply("This command must be run in a channel")
           return
        timeoutLength = self.registryValue('timeout', channel)
        player = msg.nick
        currentTime = time.time()
        if player in self._huntersEndTime and self._huntersEndTime[player] > currentTime:
            timeleft = self._huntersEndTime[player] - currentTime
            irc.reply("Hold on, your weapon is reloading... ({0} Seconds Remaining)".format(int(timeleft)))
        else:
            endTime = currentTime + timeoutLength
            self._huntersEndTime[player] = endTime
            hunttrophy = conf.supybot.directories.data.dirize("hunttrophy_{0}.db".format(channel))
            if not os.path.isfile(hunttrophy):
                with open(hunttrophy, 'w') as f:
                    f.write('Nobody\nnothing\n2')
            if self.registryValue('enable', msg.args[0]):
                animals = self.registryValue("huntTargets", channel)
                places = self.registryValue("huntLocales", channel)
                with open(hunttrophy, 'r') as f:
                    data = f.readlines()
                    highScore = data[2].rstrip('\n')
                huntrandom = random.getstate()
                random.seed(time.time())
                currentWhat = random.choice(animals)
                currentWhere = random.choice(places)
                weightType = self.registryValue('weightType')
                weight = (random.randint(int(highScore)//2,int(highScore)+10))
                irc.reply("You go hunting {0} for a {1}{2} {3}.".format(currentWhere, weight, weightType, currentWhat))
                irc.reply("You Aim....")
                irc.reply("Fire.....")
                time.sleep(random.randint(4,8))#pauses the output between line 1 and 2 for 4-8 seconds
                huntChance = random.randint(1,100)
                successRate = self.registryValue('SuccessRate')
                random.setstate(huntrandom)
                if huntChance < successRate:
                    irc.reply("Way to go, you killed the {0}{1} {2}!".format(weight, weightType, currentWhat))
                    with open(hunttrophy, 'r') as f:
                        data = f.readlines()
                        bigHunt = data[2].rstrip('\n')
                        if weight > int(bigHunt):
                            with open(hunttrophy, 'w') as f:
                                data[0] = msg.nick
                                data[1] = currentWhat
                                data[2] = weight
                                f.write(str(data[0]) + '\n' + str(data[1]) + '\n' + str(data[2]))
                                irc.reply("You got a new highscore!")
                else:
                    irc.reply("Oops, you missed the {0}{1} {2}.".format(weight, weightType, currentWhat))
    hunt = wrap(hunt)

    def fish(self,irc,msg,args):
        """takes no arguments
        performs a random fishing trip
        """
        channel = msg.args[0]
        if not irc.isChannel(channel):
           irc.reply("This command must be run in a channel")
           return
        timeoutLength = self.registryValue('timeout', channel)
        player = msg.nick
        currentTime = time.time()
        if player in self._fishersEndTime and self._fishersEndTime[player] > currentTime:
            timeleft = self._fishersEndTime[player] - currentTime
            irc.reply("Hold on, still putting bait on your fish hook... ({0} Seconds Remaining)".format(int(timeleft)))
        else:
            endTime = currentTime + timeoutLength
            self._fishersEndTime[player] = endTime
            fishtrophy = conf.supybot.directories.data.dirize("fishtrophy_{0}.db".format(channel))
            if not os.path.isfile(fishtrophy):
                with open(fishtrophy, 'w') as f:
                    f.write('Nobody\nnothing\n2')
            if(self.registryValue('enable', msg.args[0])):
                fishes = self.registryValue("fishTargets", channel)
                fishSpots = self.registryValue("fishLocales", channel)
                with open(fishtrophy, 'r') as f:
                    data = f.readlines()
                    highScore = data[2].rstrip('\n')
                fishrandom = random.getstate()
                random.seed(time.time())
                currentWhat = random.choice(fishes)
                currentWhere = random.choice(fishSpots)
                weight = random.randint(int(highScore)//2,int(highScore)+10)
                weightType = self.registryValue('weightType')
                irc.reply("You go fishing in {0}.".format(currentWhere))
                irc.reply("You cast in....")
                irc.reply("A {0}{1} {2} is biting...".format(str(weight), weightType, currentWhat))
                time.sleep(random.randint(4,8)) #pauses the output between line 1 and 2 for 4-8 seconds
                huntChance = random.randint(1,100)
                successRate = self.registryValue('SuccessRate')
                random.setstate(fishrandom)
                if huntChance < successRate:
                    irc.reply("Way to go, you caught the {0}{1} {2}!".format(str(weight), weightType, currentWhat))
                    with open(fishtrophy, 'r') as f:
                        data = f.readlines()
                        bigFish = data[2].rstrip('\n')
                        if weight > int(bigFish):
                            with open(fishtrophy, 'w') as f:
                                data[0] = msg.nick
                                data[1] = currentWhat
                                data[2] = weight
                                f.writelines(str(data[0]) + '\n' + str(data[1]) + '\n' + str(data[2]))
                                irc.reply("You got a new highscore!")
                else:
                    irc.reply("Oops, the {0}{1} {2} got away.".format(str(weight), weightType, currentWhat))
    fish = wrap(fish)

    def trophy(self,irc,msg,args):
        """takes no arguments
        checks the current highscores for hunting and fishing
        """
        channel = msg.args[0]
        if not irc.isChannel(channel):
           irc.reply("This command must be run in a channel")
           return
        hunttrophy = conf.supybot.directories.data.dirize("hunttrophy_{0}.db".format(channel))
        fishtrophy = conf.supybot.directories.data.dirize("fishtrophy_{0}.db".format(channel))
        if not os.path.isfile(fishtrophy):
            with open(fishtrophy, 'w') as f:
                f.write('Nobody\nnothing\n2')
        if not os.path.isfile(hunttrophy):
            with open(hunttrophy, 'w') as f:
                f.write('Nobody\nnothing\n2')
        if(self.registryValue('enable', msg.args[0])):
            weightType = self.registryValue('weightType')
            with open(hunttrophy, 'r') as f:
                data = f.readlines()
                hunter = data[0].rstrip('\n')
                hunted = data[1].rstrip('\n')
                size = data[2].rstrip('\n')
                irc.reply('Hunting highscore held by: %s with a %s%s %s' % (hunter, size, weightType, hunted))
            with open(fishtrophy, 'r') as f:
                data = f.readlines()
                fisherman = data[0].rstrip('\n')
                catch = data[1].rstrip('\n')
                size = data[2].rstrip('\n')
                irc.reply('Fishing highscore held by: %s with a %s%s %s' % (fisherman, size, weightType, catch))
    trophy = wrap(trophy)

    def resetscores(self,irc,msg,args):
        """takes no arguments
        resets the highscores for both hunting and fishing. this command is limited to the owner, to prevent just anyone from clearing the scores
        """
        channel = msg.args[0]
        if not irc.isChannel(channel):
           irc.reply("This command must be run in a channel")
           return
        hunttrophy = conf.supybot.directories.data.dirize("hunttrophy_{0}.db".format(channel))
        fishtrophy = conf.supybot.directories.data.dirize("fishtrophy_{0}.db".format(channel))
        with open(hunttrophy, 'w') as f:
            f.write('Nobody\nnothing\n2')
        with open(fishtrophy, 'w') as f:
            f.write('Nobody\nnothing\n2')
        irc.replySuccess()
    resetscores = wrap(resetscores, ['owner'])

Class = HuntNFish


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
