###
# Copyright (c) 2019, James Lu <james@overdrivenetworks.com>
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

"""
accountsdb: Provides storage for user-specific data via Supybot accounts, ident@host, or nicks.
"""

import pickle

from supybot import ircdb, log, conf, registry

MODES = ["accounts", "identhost", "nicks"]
DEFAULT_MODE = MODES[0]

class _AccountsDBAddressConfig(registry.OnlySomeStrings):
    validStrings = MODES

CONFIG_OPTION_NAME = "DBAddressingMode"
CONFIG_OPTION = _AccountsDBAddressConfig(DEFAULT_MODE, """Sets the DB addressing mode.
    This requires reloading the plugin to take effect. Valid settings include accounts
    (save users by Supybot accounts and ident@host if not registered), identhost
    (save users by ident@host), and nicks (save users by nicks).
    When changing addressing modes, existing keys will be left intact, but migration between
    addressing modes is NOT supported.""")

class AccountsDB():
    """
    Abstraction to map users to third-party account names.

    This stores users by their bot account first, falling back to their
    ident@host if they are not logged in.
    """

    def __init__(self, plugin_name, filename, addressing_mode=DEFAULT_MODE):
        """
        Loads the existing database, creating a new one in memory if none
        exists.
        """
        self.db = {}
        self._plugin_name = plugin_name
        self.filename = conf.supybot.directories.data.dirize(filename)

        self.addressing_mode = addressing_mode

        try:
            with open(self.filename, 'rb') as f:
               self.db = pickle.load(f)
        except Exception as e:
            log.debug('%s: Unable to load database, creating '
                      'a new one: %s', self._plugin_name, e)

    def flush(self):
        """Exports the database to a file."""
        try:
            with open(self.filename, 'wb') as f:
                pickle.dump(self.db, f, 2)
        except Exception as e:
            log.warning('%s: Unable to write database: %s', self._plugin_name, e)

    def _get_key(self, prefix):
        nick, identhost = prefix.split('!', 1)

        if self.addressing_mode == "accounts":
            try:  # Try to first look up the caller as a bot account.
                userobj = ircdb.users.getUser(prefix)
                return userobj.name
            except KeyError:  # If that fails, store them by nick@host.
                return identhost
        elif self.addressing_mode == "identhost":
            return identhost
        elif self.addressing_mode == "nicks":
            return nick
        else:
            raise ValueError("Unknown addressing mode %r" % self.addressing_mode)

    def set(self, prefix, newId):
        """Sets a user ID given the user's prefix."""
        user = self._get_key(prefix)
        self.db[user] = newId

    def get(self, prefix):
        """Sets a user ID given the user's prefix."""
        user = self._get_key(prefix)

        # Automatically returns None if entry does not exist
        return self.db.get(user)
