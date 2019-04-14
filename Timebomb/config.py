###
# Copyright (c) 2010, quantumlemur
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

def configure(advanced):
    # This will be called by supybot to configure this module.  advanced is
    # a bool that specifies whether the user identified himself as an advanced
    # user or not.  You should effect your configuration by manipulating the
    # registry as appropriate.
    from supybot.questions import expect, anything, something, yn
    conf.registerPlugin('Timebomb', True)


Timebomb = conf.registerPlugin('Timebomb')
# This is where your configuration variables (if any) should go.  For example:
# conf.registerGlobalValue(Timebomb, 'someConfigVariableName',
#     registry.Boolean(False, """Help for someConfigVariableName."""))
conf.registerGlobalValue(Timebomb, 'colors',
    registry.SpaceSeparatedListOfStrings(['AliceBlue', 'AntiqueWhite', 'Aqua',
        'Aquamarine', 'Azure', 'Beige', 'Bisque', 'Black', 'BlanchedAlmond', 
        'Blue', 'BlueViolet', 'Brown', 'BurlyWood', 'CadetBlue', 'Chartreuse',
        'Chocolate', 'Coral', 'CornflowerBlue', 'Cornsilk', 'Crimson', 'Cyan',
        'DarkBlue', 'DarkCyan', 'DarkGoldenRod', 'DarkGray', 'DarkGreen', 
        'DarkKhaki', 'DarkMagenta', 'DarkOliveGreen', 'DarkOrange', 
        'DarkOrchid', 'DarkRed', 'DarkSalmon', 'DarkSeaGreen', 'DarkSlateBlue',
        'DarkSlateGray', 'DarkTurquoise', 'DarkViolet', 'DeepPink', 
        'DeepSkyBlue', 'DimGray', 'DodgerBlue', 'FireBrick', 'FloralWhite',
        'ForestGreen', 'Fuchsia', 'Gainsboro', 'GhostWhite', 'Gold', 
        'GoldenRod', 'Gray', 'Green', 'GreenYellow', 'HoneyDew', 'HotPink', 
        'IndianRed', 'Indigo', 'Ivory', 'Khaki', 'Lavender', 'LavenderBlush',
        'LawnGreen', 'LemonChiffon', 'LightBlue', 'LightCoral', 'LightCyan',
        'LightGoldenRodYellow', 'LightGrey', 'LightGreen', 'LightPink', 
        'LightSalmon', 'LightSeaGreen', 'LightSkyBlue', 'LightSlateGray',
        'LightSteelBlue', 'LightYellow', 'Lime', 'LimeGreen', 'Linen', 
        'Magenta', 'Maroon', 'MediumAquaMarine', 'MediumBlue', 'MediumOrchid',
        'MediumPurple', 'MediumSeaGreen', 'MediumSlateBlue', 
        'MediumSpringGreen', 'MediumTurquoise', 'MediumVioletRed', 
        'MidnightBlue', 'MintCream', 'MistyRose', 'Moccasin', 'NavajoWhite', 
        'Navy', 'OldLace', 'Olive', 'OliveDrab', 'Orange', 'OrangeRed', 
        'Orchid', 'PaleGoldenRod', 'PaleGreen', 'PaleTurquoise', 
        'PaleVioletRed', 'PapayaWhip', 'PeachPuff', 'Peru', 'Pink', 'Plum', 
        'PowderBlue', 'Purple', 'Red', 'RosyBrown', 'RoyalBlue', 
        'SaddleBrown', 'Salmon', 'SandyBrown', 'SeaGreen', 'SeaShell', 
        'Sienna', 'Silver', 'SkyBlue', 'SlateBlue', 'SlateGray', 'Snow', 
        'SpringGreen', 'SteelBlue', 'Tan', 'Teal', 'Thistle', 'Tomato', 
        'Turquoise', 'Violet', 'Wheat', 'White', 'WhiteSmoke', 'Yellow', 
        'YellowGreen'],
    """The set of possible timebomb wire colors"""))

    
conf.registerGlobalValue(Timebomb, 'shortcolors',
        registry.SpaceSeparatedListOfStrings(['red', 'orange', 'yellow', 
            'green', 'blue', 'purple', 'pink', 'black', 'brown', 'gray', 
            'white'],
        """The set of possible timebomb wire colors when there are few
                wires"""))

conf.registerChannelValue(Timebomb, 'exclusions',
        registry.SpaceSeparatedListOfStrings([], 
        """A list of nicks who should be excluded from being 
            randombombed"""))

conf.registerChannelValue(Timebomb, 'allowBombs', 
        registry.Boolean(False, """Determines whether timebombs are allowed 
            in the channel."""))

conf.registerChannelValue(Timebomb, 'minWires',
        registry.PositiveInteger(2, """Determines the minimum number of wires 
            a timebomb will have."""))

conf.registerChannelValue(Timebomb, 'maxWires',
        registry.PositiveInteger(4, """Determines the maximum number of wires 
            a timebomb will have."""))

conf.registerChannelValue(Timebomb, 'minTime',
        registry.PositiveInteger(45, """Determines the minimum time of a 
            timebomb timer, in seconds."""))

conf.registerChannelValue(Timebomb, 'maxTime',
        registry.PositiveInteger(70, """Determines the maximum time of a 
            timebomb timer, in seconds."""))

conf.registerChannelValue(Timebomb, 'minRandombombTime',
        registry.PositiveInteger(60, """Determines the minimum time of a 
            randombomb timer, which should in general be greater than the 
            minimum targeted bomb time, to allow someone who's not paying 
            attention to respond."""))

conf.registerChannelValue(Timebomb, 'maxRandombombTime',
        registry.PositiveInteger(120, """Determines the maximum time of a 
            randombomb timer, which should in general be greater than the 
            maxiumum targeted bomb time, to allow someone who's not paying 
            attention to respond."""))

conf.registerChannelValue(Timebomb, 'showArt',
        registry.Boolean(True, """Determines whether an ASCII art bomb should 
            be shown on detonation, or a simple message."""))

conf.registerChannelValue(Timebomb, 'bombActiveUsers',
        registry.Boolean(False, """Determines whether only active users 
            should be randombombed"""))

conf.registerChannelValue(Timebomb, 'joinIsActivity',
        registry.Boolean(False, """Determines whether channel joins should 
            count as activity for randombombs"""))

conf.registerChannelValue(Timebomb, 'allowSelfBombs',
        registry.Boolean(False, """Allow the bot to bomb itself?"""))

conf.registerChannelValue(Timebomb, 'idleTime',
        registry.PositiveInteger(60, """The number of minutes before someone 
            is counted as idle for randombombs, if idle-checking is 
            enabled."""))

conf.registerChannelValue(Timebomb, 'showCorrectWire',
        registry.Boolean(False, """Determines whether the correct wire will be
            shown when a bomb detonates."""))

conf.registerGlobalValue(Timebomb, 'debug',
        registry.Boolean(False, """Determines whether debugging info will be
            shown."""))

# vim:set shiftwidth=4 tabstop=4 expandtab textwidth=79:
