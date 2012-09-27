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
import re
import time
import string
import random as random
import supybot.conf as conf
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('HuntNFish')

hunttrophy = conf.supybot.directories.data.dirize('hunttrophy.db')
fishtrophy = conf.supybot.directories.data.dirize('fishtrophy.db')

if not os.path.isfile(hunttrophy):
    with open(hunttrophy, 'w') as f:
        f.write('Nobody\nnothing\n2')

if not os.path.isfile(fishtrophy):
    with open(fishtrophy, 'w') as f:
        f.write('Nobody\nnothing\n2')


@internationalizeDocstring
class HuntNFish(callbacks.Plugin):
    """Adds hunt and fish commands for a basic hunting and fishing game."""
    threaded = True

    def hunt(self,irc,msg,args):
        """takes no arguments
        performs a random hunt
        """
        if(self.registryValue('enable', msg.args[0])):
            animals = ['bear', 'gopher', 'rabbit', 'hunter', 'deer', 'fox', 'duck', 'moose', 'pokemon named Pikachu', 'park ranger', 'Yogi Bear', 'Boo Boo Bear', 'dog named Benji', 'cow', 'raccoon', 'koala bear', 'camper', 'channel lamer', 'your mom']
            places = ['in some bushes', 'in a hunting blind', 'in a hole', 'up in a tree', 'in a hiding place', 'out in the open', 'in the middle of a field', 'downtown', 'on a street corner', 'at the local mall']

            with open(hunttrophy, 'r') as f:
                data = f.readlines()
                highScore = data[2].rstrip('\n')
            huntrandom = random.getstate()   
            random.seed(time.time())
            currentWhat = random.choice(animals)
            currentWhere = random.choice(places)
            weightType = self.registryValue('weightType')
            weight = (random.randint(int(highScore)/2,int(highScore)+10))
            thisHunt = '%s goes hunting %s for a %s%s %s' % (msg.nick, currentWhere, weight, weightType, currentWhat)
            irc.reply(thisHunt)
            irc.reply("aims....")
            irc.reply("fires.....")
            time.sleep(random.randint(4,8))#pauses the output between line 1 and 2 for 4-8 seconds
            huntChance = random.randint(1,100)
            successRate = self.registryValue('SuccessRate')
            random.setstate(huntrandom)

            if huntChance < successRate:
                win = 'way to go, %s. You killed the %s%s %s' % (msg.nick, weight, weightType, currentWhat)
                irc.reply(win)
                with open(hunttrophy, 'r') as f:
                    data = f.readlines()
                    bigHunt = data[2].rstrip('\n')
                    if weight > int(bigHunt):
                        with open(hunttrophy, 'w') as f:
                            data[0] = msg.nick
                            data[1] = currentWhat 
                            data[2] = weight
                            f.write(str(data[0]) + '\n' + str(data[1]) + '\n' + str(data[2]))
                            irc.reply("you got a new highscore")

            else:
                lose = ' '.join(["oops, you missed", msg.nick])
                irc.reply(lose)

    hunt = wrap(hunt)

    def fish(self,irc,msg,args):
        """takes no arguments
        performs a random fishing trip
        """
        if(self.registryValue('enable', msg.args[0])):
            fishes = ('Salmon', 'Herring', 'Yellowfin Tuna', 'Pink Salmon', 'Chub', 'Barbel', 'Perch', 'Northern Pike', 'Brown Trout', 'Arctic Char', 'Roach', 'Brayling', 'Bleak', 'Cat Fish', 'Sun Fish', 'Old Tire', 'Rusty Tin Can', 'Genie Lamp', 'Love Message In A Bottle', 'Old Log', 'Rubber Boot' , 'Dead Body', 'Loch Ness Monster', 'Old Fishing Lure', 'Piece of the Titanic', 'Chunk of Atlantis', 'Squid', 'Whale', 'Dolphin',  'Porpoise' , 'Stingray', 'Submarine', 'Seal', 'Seahorse', 'Jellyfish', 'Starfish', 'Electric Eel', 'Great White Shark', 'Scuba Diver' , 'Lag Monster', 'Virus', 'Soggy Pack of Smokes', 'Bag of Weed', 'Boat Anchor', 'Pair Of Floaties', 'Mermaid', ' Merman', 'Halibut', 'Tiddler', 'Sock', 'Trout')
            fishSpots = ('a Stream', 'a Lake', 'a River', 'a Pond', 'an Ocean', 'a Bathtub', 'a Kiddies Swimming Pool', 'a Toilet', 'a Pile of Vomit', 'a Pool of Urine', 'a Kitchen Sink', 'a Bathroom Sink', 'a Mud Puddle', 'a Pail of Water', 'a Bowl of Jell-O', 'a Wash Basin', 'a Rain Barrel', 'an Aquarium', 'a SnowBank', 'a WaterFall', 'a Cup of Coffee', 'a Glass of Milk')

            with open(fishtrophy, 'r') as f:
                data = f.readlines()
                highScore = data[2].rstrip('\n')
            fishrandom = random.getstate()
            random.seed(time.time())
            currentWhat = random.choice(fishes)
            currentWhere = random.choice(fishSpots)
            weight = random.randint(int(highScore)/2,int(highScore)+10)
            weightType = self.registryValue('weightType')
            thisFishing = '%s goes fishing in %s' % (msg.nick, currentWhere)
            irc.reply(thisFishing)
            irc.reply("casts in....")
            irc.reply('a %s%s %s is biting...' % (str(weight), weightType, currentWhat))
            time.sleep(random.randint(4,8))#pauses the output between line 1 and 2 for 4-8 seconds
            huntChance = random.randint(1,100)
            successRate = self.registryValue('SuccessRate')
            random.setstate(fishrandom)

            if huntChance < successRate:
                win = 'way to go, %s. You caught the %s%s %s' % (msg.nick, str(weight), weightType, currentWhat)
                irc.reply(win)
                with open(fishtrophy, 'r') as f:
                    data = f.readlines()
                    bigFish = data[2].rstrip('\n')
                    if weight > int(bigFish):
                        with open(fishtrophy, 'w') as f:
                            data[0] = msg.nick
                            data[1] = currentWhat 
                            data[2] = weight
                            f.writelines(str(data[0]) + '\n' + str(data[1]) + '\n' + str(data[2]))
                            irc.reply("you got a new highscore")

            else:
                lose = ' '.join(["oops, it got away", msg.nick])
                irc.reply(lose)

    fish = wrap(fish)

    def trophy(self,irc,msg,args):
        """takes no arguments
        checks the current highscores for hunting and fishing
        """
        if(self.registryValue('enable', msg.args[0])):
            weightType = self.registryValue('weightType')
            with open(hunttrophy, 'r') as f:
                data = f.readlines()
                hunter = data[0].rstrip('\n')
                hunted = data[1].rstrip('\n')
                size = data[2].rstrip('\n')
                irc.reply('hunting highscore held by: %s with a %s%s %s' % (hunter, size, weightType, hunted))
            with open(fishtrophy, 'r') as f:
                data = f.readlines()
                fisherman = data[0].rstrip('\n')
                catch = data[1].rstrip('\n')
                size = data[2].rstrip('\n')
                irc.reply('fishing highscore held by: %s with a %s%s %s' % (fisherman, size, weightType, catch))

    trophy = wrap(trophy)

    def resetscores(self,irc,msg,args):
        """takes no arguments
        resets the highscores for both hunting and fishing. this command is limited to the owner, to prevent just anyone from clearing the scores
        """
        with open(hunttrophy, 'w') as f:
            f.write('Nobody\nnothing\n2')
        with open(fishtrophy, 'w') as f:
            f.write('Nobody\nnothing\n2')
        irc.replySuccess()

    resetscores = wrap(resetscores, ['owner'])        

Class = HuntNFish


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
