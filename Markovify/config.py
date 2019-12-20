###
# Copyright (c) 2019, oddluck
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Markovify')
except:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified themself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Markovify', True)

Markovify = conf.registerPlugin('Markovify')

conf.registerChannelValue(Markovify, 'enable',
    registry.Boolean(False, _("""Determines whether the plugin is enabled on a channel. This defaults to False to avoid useless resources consumption.""")))
conf.registerChannelValue(Markovify, 'stripRelayedNick',
    registry.Boolean(True, _("""Determines whether the bot will strip strings like <XXX> at the beginning of messages.""")))
conf.registerChannelValue(Markovify, 'stripURL',
    registry.Boolean(True, _("""Determines whether the bot will strip URLs from messages.""")))
conf.registerChannelValue(Markovify, 'ignoreNicks',
    registry.SpaceSeparatedListOfStrings([], _("""A list of nicks to be ignored by the bot""")))
conf.registerChannelValue(Markovify, 'ignorePattern',
    registry.Regexp("", _("""Mesages matching this pattern will be ignored.""")))
conf.registerChannelValue(Markovify, 'stripPattern',
    registry.Regexp("", _("""Text matching this pattern will be stripped.""")))
conf.registerChannelValue(Markovify, 'stripNicks',
    registry.Boolean(False, _("""Strip all nicks, including the bots, when learning? This replaces a nick with the keyword MAGIC_NICK to use for random highlighting.""")))
conf.registerChannelValue(Markovify, 'probability',
    registry.Probability(0, _("""Determines the percent of messages the bot will answer. 0.0 - 1.0""")))
conf.registerChannelValue(Markovify, 'probabilityWhenAddressed',
    registry.Probability(0, _("""Determines the percent of messages adressed to the bot the bot will answer, 0.0 - 1.0""")))
conf.registerChannelValue(Markovify, 'responseDelay',
    registry.Boolean(False, _("""Delay responding for 2 to 4 seconds in order to seem more human?""")))
