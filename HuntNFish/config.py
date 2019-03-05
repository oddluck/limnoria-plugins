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

import supybot.conf as conf
import supybot.registry as registry
from supybot.i18n import PluginInternationalization, internationalizeDocstring

_ = PluginInternationalization('HuntNFish')

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('HuntNFish', True)


HuntNFish = conf.registerPlugin('HuntNFish')
# This is where your configuration variables (if any) should go.  For example:
conf.registerChannelValue(HuntNFish, 'WeightType',
    registry.String('lb', _("""Determines what form of weight, metric or imperial, is used by the plugin. options are lb and kg.""")))
conf.registerChannelValue(HuntNFish, 'enable',
    registry.Boolean(True, _("""Turns on and off the hunt and fish commands.""")))
conf.registerChannelValue(HuntNFish, 'successRate',
    registry.NonNegativeInteger(50, _("""Percent of chance of success""")))
conf.registerChannelValue(HuntNFish, 'huntTargets',
                        registry.CommaSeparatedListOfStrings(["bear","gopher","rabbit","hunter","deer","fox","duck","moose","park ranger","Yogi Bear","Boo Boo Bear","dog named Benji","cow","raccoon","koala bear","camper","channel lurker","your mother","lion","ocelot","house cat"], _("""List of hunting tagets""")))
conf.registerChannelValue(HuntNFish, 'fishTargets',
                        registry.CommaSeparatedListOfStrings(["salmon","herring","yellowfin tuna","pink salmon","chub","barbel","perch","northern pike","brown trout","arctic char","roach","brayling","bleak","cat fish","sun fish","old tire","rusty tin can","genie lamp","message in a bottle","old log","rubber boot","dead body","Loch Ness Monster","old fishing lure","piece of the Titanic","chunk of Atlantis","squid","whale","dolphin","porpoise","stingray","submarine","seal","seahorse","jellyfish","starfish","electric eel","great white shark","scuba diver","lag monster","virus","soggy pack of cigarettes","soggy bag of weed","boat anchor","corpse","mermaid"," merman","halibut","tiddler","sock","trout"], _("""List of fishing targets""")))
conf.registerChannelValue(HuntNFish, 'huntLocales',
                        registry.CommaSeparatedListOfStrings(["in some bushes","in a hunting blind","in a hole","up in a tree","in a hiding place","out in the open","in the middle of a field","downtown","on a street corner","at the local mall"], _("""List of hunting locales""")))
conf.registerChannelValue(HuntNFish, 'fishLocales',
                        registry.CommaSeparatedListOfStrings(["a stream","a lake","a river","a pond","an ocean","a bathtub","a swimming pool","a toilet","a pile of vomit","a pool of urine","a kitchen Sink","a bathroom sink","a mud puddle","a pail of water","a bowl of Jell-O","a wash basin","a rain barrel","an aquarium","a snowbank","a waterFall","a cup of coffee","a glass of milk"], _("""List of fishing locales""")))
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
