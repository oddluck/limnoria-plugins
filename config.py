###
# Copyright (c) 2015, butterscotchstallion
# All rights reserved.
#
#
###

import supybot.conf as conf
import supybot.registry as registry
try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('IMDB')
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
    conf.registerPlugin('IMDB', True)


IMDB = conf.registerPlugin('IMDB')

conf.registerGlobalValue(IMDB, 'template',
     registry.String("$title ($year, $country) - Rating: $imdbRating :: $plot :: http://imdb.com/title/$imdbID", _("""Template for the output of a search query.""")))

# alternative template:
#                     $title ($year - $director) :: [i:$imdbRating r:$tomatoMeter m:$metascore] $plot :: http://imdb.com/title/$imdbID

conf.registerGlobalValue(IMDB, 'noResultsMessage',
     registry.String("No results for that query.", _("""This message is sent when there are no results""")))
     
# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
