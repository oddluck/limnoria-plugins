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
    _ = PluginInternationalization('IRCArt')
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
    conf.registerPlugin('IRCArt', True)

IRCArt = conf.registerPlugin('IRCArt')

conf.registerGlobalValue(IRCArt, 'pasteAPI',
registry.String('', _("""Paste.ee API Key""")))

conf.registerGlobalValue(IRCArt, 'imgurAPI',
registry.String('', _("""Imgur Client ID""")))

conf.registerChannelValue(IRCArt, 'pasteEnable',
registry.Boolean(False, _("""Turns on and off paste.ee support""")))

conf.registerChannelValue(IRCArt, 'delay',
registry.Float(1.0, _("""Set the time delay betwen lines. Not currently implemented.""")))

conf.registerChannelValue(IRCArt, 'quantize',
registry.Boolean(False, _("""Enable quantizing to 256 colors before rendering. Results in much faster rendering at a slight decrease in quality. Default: False""")))

conf.registerChannelValue(IRCArt, 'resize',
registry.Integer(3, _("""Set the resize algorithm. 0 = nearest, 1 = lanczos, 2 = bilinear, 3 = bicubic, 4 = box, 5 = hamming""")))

conf.registerChannelValue(IRCArt, 'speed',
registry.String('Slow', _("""Set the speed of the color rendering. 'Slow' (default) to use CIEDE2000 color difference. 'Fast' to use Euclidean color difference.""")))

conf.registerChannelValue(IRCArt, 'imgDefault',
registry.String('1/2', _("""Set the default art type for the img command. Options are 'ascii', '1/2' (default), '1/4', 'block', and 'no-color'""")))

conf.registerChannelValue(IRCArt, 'asciiWidth',
registry.Integer(100, _("""Set the default column width for ascii art images""")))

conf.registerChannelValue(IRCArt, 'blockWidth',
registry.Integer(80, _("""Set the default column width for 1/2 and 1/4 block art images""")))

conf.registerChannelValue(IRCArt, 'colors',
registry.Integer(99, _("""Set the default number of colors to use. Options are 16 for colors 0-15 only, 83 for colors 16-98 only, and 99 (default) to use all available colors""")))

conf.registerChannelValue(IRCArt, 'fg',
registry.Integer(99, _("""Set the default foreground color for ascii art images. 0-98. 99 is disabled (default)""")))

conf.registerChannelValue(IRCArt, 'bg',
registry.Integer(99, _("""Set the default background color for ascii art images. 0-98. 99 is disabled (default)""")))
