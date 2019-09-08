# -*- coding: utf-8 -*-
###
# This file is part of Soap.
#
# Soap is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation, version 2.
#
# Soap is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE.
#
# See the GNU General Public License for more details. You should have received
# a copy of the GNU General Public License along with Soap. If not, see
# <http://www.gnu.org/licenses/>.
###

"""
lets the bot communicate with openttd via its adminport, and to control same
"""

import supybot
import supybot.world as world
import importlib

# Use this for the version of this plugin.  You may wish to put a CVS keyword
# in here if you're keeping the plugin in CVS or some similar system.
__version__ = "SUDS"

# XXX Replace this with an appropriate author or supybot.Author instance.
__author__ = supybot.Author('Taede Werkhoven', 'TWerkhoven', 't.werkhoven@turbulent-t.com')

# This is a dictionary mapping supybot.Author instances to lists of
# contributions.
__contributors__ = {}

# This is a url where the most recent plugin package can be downloaded.
__url__ = 'https://github.com/luaduck/suds'

from . import config
from . import enums
from . import soaputils
from . import soapclient
import libottdadmin2
from . import plugin
importlib.reload(config)
importlib.reload(enums)
importlib.reload(soaputils)
importlib.reload(soapclient)
importlib.reload(libottdadmin2)
importlib.reload(plugin)

# In case we're being reloaded.
# Add more reloads here if you add third-party modules and want them to be
# reloaded when this plugin is reloaded.  Don't forget to import them as well!

if world.testing:
    import test

Class = plugin.Class
configure = config.configure


# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
