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

import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import random as random
import re
import time
import string
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('HuntNFish')

@internationalizeDocstring
class HuntNFish(callbacks.Plugin):
    """Adds hunt and fish commands for a basic hunting and fishing game."""
    threaded = True

    def hunt(self,irc,msg,args):
        """
        performs a random hunt
        """
        if(self.registryValue('enable', msg.args[0])):
            animals = [' bear', ' gopher', ' rabbit', ' hunter', ' deer', ' fox', ' duck', ' moose', ' pokemon named Pikachu', ' park ranger', ' Yogi Bear', ' Boo Boo Bear', ' dog named Benji', ' cow', ' raccoon', ' koala bear', ' camper', ' channel lamer']
            places = ['in some bushes', 'in a hunting blind', 'in a hole', 'up in a tree', 'in a hiding place', 'out in the open', 'in the middle of a field', 'downtown', 'on a street corner', 'at the local mall']

            currentWhat = random.choice(animals)
            currentWhere = random.choice(places)
            weight = random.randint(1,200)
            weightType = self.registryValue('weightType')
            thisHunt = (msg.nick + " goes hunting " + currentWhere + " for a " + str(weight) + weightType +  currentWhat)
            irc.reply(thisHunt)
            irc.reply("aims....")
            irc.reply("fires.....")
            time.sleep(7)#pauses the output between line 1 and 2 for 5 seconds
            huntChance = random.randint(1,100)
            successRate = self.registryValue('SuccessRate')

            if huntChance < successRate:
                win = ("way to go, " + msg.nick + ". You killed the " + str(weight) + weightType + currentWhat)
                irc.reply(win)
            else:
                lose = ("oops, you missed, " + msg.nick)
                irc.reply(lose)


    def fish(self,irc,msg,args):
        """
        performs a random fishing trip
        """
        if(self.registryValue('enable', msg.args[0])):
            fishes = (' Salmon', ' Herring', ' Yellowfin Tuna', ' Pink Salmon', ' Chub', ' Barbel', ' Perch', ' Northern Pike', ' Brown Trout', ' Arctic Char', ' Roach', ' Brayling', ' Bleak', ' Cat Fish', ' Sun Fish', ' Old Tire', ' Rusty Tin Can', ' Genie Lamp', ' Love Message In A Bottle', ' Old Log', ' Rubber Boot' , ' Dead Body', ' Loch Ness Monster', ' Old Fishing Lure', ' Piece of the Titanic', ' Chunk of Atlantis', ' Squid', ' Whale', ' Dolphin',  ' Porpoise' , ' Stingray', ' Submarine', ' Seal', ' Seahorse', ' Jellyfish', ' Starfish', ' Electric Eel', ' Great White Shark', ' Scuba Diver' , ' Lag Monster', ' Virus', ' Soggy Pack of Smokes', ' Bag of Weed', ' Boat Anchor', ' Pair Of Floaties', ' Mermaid', ' Merman', ' Halibut', ' Tiddler', ' Sock', ' Trout')
            fishSpots = ('a Stream', 'a Lake', 'a River', 'a Pond', 'an Ocean', 'a Bathtub', 'a Kiddies Swimming Pool', 'a Toilet', 'a Pile of Vomit', 'a Pool of Urine', 'a Kitchen Sink', 'a Bathroom Sink', 'a Mud Puddle', 'a Pail of Water', 'a Bowl of Jell-O', 'a Wash Basin', 'a Rain Barrel', 'an Aquarium', 'a SnowBank', 'a WaterFall', 'a Cup of Coffee', 'a Glass of Milk')

            currentWhat = random.choice(fishes)
            currentWhere = random.choice(fishSpots)
            weight = random.randint(1,200)
            weightType = self.registryValue('weightType')
            thisFishing = (msg.nick + " goes fishing in " + currentWhere)
            irc.reply(thisFishing)
            irc.reply("casts in....")
            irc.reply("a " + str(weight) + weightType + currentWhat + " is biting...")
            time.sleep(7)#pauses the output between line 1 and 2 for 5 seconds
            huntChance = random.randint(1,100)
            successRate = self.registryValue('SuccessRate')

            if huntChance < successRate:
                win = ("way to go, " + msg.nick + ". You caught the " + str(weight) + weightType + currentWhat)
                irc.reply(win)
            else:
                lose = ("oops, it got away, " + msg.nick)
                irc.reply(lose)


Class = HuntNFish


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
