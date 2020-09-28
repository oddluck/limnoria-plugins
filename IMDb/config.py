###
# Copyright (c) 2015, butterscotchstallion
# Copyright (c) 2020, oddluck <oddluck@riseup.net>
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

try:
    from supybot.i18n import PluginInternationalization

    _ = PluginInternationalization("IMDb")
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

    conf.registerPlugin("IMDb", True)


IMDb = conf.registerPlugin("IMDb")

conf.registerChannelValue(
    IMDb,
    "template",
    registry.String(
        "$logo :: $title ($year, $country, [$rated], $genre, $runtime) "
        ":: IMDb: $imdbRating | MC: $metascore | RT: $tomatoMeter :: "
        "http://imdb.com/title/$imdbID :: $plot :: Director: $director :: "
        "Cast: $actors :: Writer: $writer",
        _("""IMDb reply template."""),
    ),
)

conf.registerChannelValue(
    IMDb,
    "logo",
    registry.String(
        "\x02\x031,8 IMDb \x0F", _("""Logo used with {{logo}} in template""")
    ),
)

conf.registerChannelValue(
    IMDb,
    "noResultsMessage",
    registry.String(
        "No results for that query.",
        _("""This message is sent when there are no results"""),
    ),
)

conf.registerChannelValue(
    IMDb,
    "google",
    registry.Integer(
        1,
        """
        Google search priority. Google plugin must be loaded.
        0 = disabled. 1 = first. 2 = second.
        """,
    ),
)

conf.registerChannelValue(
    IMDb,
    "ddg",
    registry.Integer(
        2,
        """
        DDG search priority. DDG plugin must be loaded.
        0 = disabled. 1 = first. 2 = second.
        """,
    ),
)

conf.registerGlobalValue(
    IMDb, "omdbAPI", registry.String("", _("""OMDB API Key"""), private=True)
)

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
