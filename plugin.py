###
# Copyright (c) 2018, cottongin
# All rights reserved.
#
#
###

from supybot import utils, plugins, ircutils, callbacks
from supybot.commands import *
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('CBBScores')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x


class CBBScores(callbacks.Plugin):
    """Fetches College Basketball scores"""
    threaded = True


Class = CBBScores


# vim:set shiftwidth=4 softtabstop=4 expandtab textwidth=79:
