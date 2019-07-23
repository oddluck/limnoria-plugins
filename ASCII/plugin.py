###
# Copyright (c) 2019 oddluck
# All rights reserved.
#
#
###

import supybot.ansi as ansi
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.callbacks as callbacks
import supybot.ircmsgs as ircmsgs
import os
import requests
from PIL import Image, ImageOps, ImageFont, ImageDraw, ImageEnhance
import numpy as np
import sys, math
from fake_useragent import UserAgent
import re
import pexpect
import time
import random as random
import pyimgur
from bs4 import BeautifulSoup

try:
    from supybot.i18n import PluginInternationalization
    _ = PluginInternationalization('Weed')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class ASCII(callbacks.Plugin):
    """Uses API to retrieve information"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(ASCII, self)
        self.__parent.__init__(irc)
        self.colors = 99
        self.stopped = {}
        self.old_color = None
        self.rgbColors = [
            (255,255,255),
            (0,0,0),
            (0,0,127),
            (0,147,0),
            (255,0,0),
            (127,0,0),
            (156,0,156),
            (252,127,0),
            (255,255,0),
            (0,252,0),
            (0,147,147),
            (0,255,255),
            (0,0,252),
            (255,0,255),
            (127,127,127),
            (210,210,210),
            (71,0,0),
            (71,33,0),
            (71,71,0),
            (50,71,0),
            (0,71,0),
            (0,71,44),
            (0,71,71),
            (0,39,71),
            (0,0,71),
            (46,0,71),
            (71,0,71),
            (71,0,42),
            (116,0,0),
            (116,58,0),
            (116,116,0),
            (81,116,0),
            (0,116,0),
            (0,116,73),
            (0,116,116),
            (0,64,116),
            (0,0,116),
            (75,0,116),
            (116,0,116),
            (116,0,69),
            (181,0,0),
            (181,99,0),
            (181,181,0),
            (125,181,0),
            (0,181,0),
            (0,181,113),
            (0,181,181),
            (0,99,181),
            (0,0,181),
            (117,0,181),
            (181,0,181),
            (181,0,107),
            (255,0,0),
            (255,140,0),
            (255,255,0),
            (178,255,0),
            (0,255,0),
            (0,255,160),
            (0,255,255),
            (0,140,255),
            (0,0,255),
            (165,0,255),
            (255,0,255),
            (255,0,152),
            (255,89,89),
            (255,180,89),
            (255,255,113),
            (207,255,96),
            (111,255,111),
            (101,255,201),
            (109,255,255),
            (89,180,255),
            (89,89,255),
            (196,89,255),
            (255,102,255),
            (255,89,188),
            (255,156,156),
            (255,211,156),
            (255,255,156),
            (226,255,156),
            (156,255,156),
            (156,255,219),
            (156,255,255),
            (156,211,255),
            (156,156,255),
            (220,156,255),
            (255,156,255),
            (255,148,211),
            (0,0,0),
            (19,19,19),
            (40,40,40),
            (54,54,54),
            (77,77,77),
            (101,101,101),
            (129,129,129),
            (159,159,159),
            (188,188,188),
            (226,226,226),
            (255,255,255)]
        self.colors83= {
            (11.5497, 31.8768, 18.1739):16,
            (17.5866, 15.7066, 25.9892):17,
            (29.0208, -8.5776, 37.5533):18,
            (27.2543, -19.015, 35.3673):19,
            (25.2798, -34.2963, 32.8426):20,
            (25.8276, -27.5812, 10.7515):21,
            (26.6245, -19.1316, -5.6261):22,
            (14.986, 1.2467, -23.6473):23,
            (4.1091, 27.6851, -41.3905):24,
            (9.2862, 34.8709, -32.6869):25,
            (14.3696, 39.0991, -24.2113):26,
            (12.6512, 34.8073, -6.066):27,
            (22.699, 44.779, 34.3145):28,
            (31.2054, 21.9979, 41.7676):29,
            (47.2407, -12.0488, 52.8125):30,
            (44.5753, -27.9355, 49.6338):31,
            (41.9858, -48.1745, 46.4957):32,
            (42.7207, -39.1444, 16.0528):33,
            (43.8747, -26.8746, -7.9028):34,
            (26.5278, 3.8603, -34.8152):35,
            (11.0, 44.2673, -60.2918):36,
            (19.0423, 48.637, -46.7161):37,
            (26.6606, 54.9202, -34.0091):38,
            (24.1377, 48.6121, -6.8774):39,
            (37.5243, 61.9327, 51.9413):40,
            (50.3904, 27.7338, 58.553):41,
            (71.4677, -16.6651, 73.0447):42,
            (67.5818, -39.987, 68.408):43,
            (64.1995, -66.6294, 64.3075):44,
            (65.1526, -54.8772, 23.9922):45,
            (66.8122, -37.1703, -10.9303):46,
            (41.6262, 7.9137, -50.0682):47,
            (21.343, 61.2273, -83.3898):48,
            (32.0743, 66.9878, -65.2716):49,
            (43.0033, 75.9603, -47.0378):50,
            (39.3866, 66.9043, -7.4929):51,
            (53.2329, 80.1093, 67.2201):52,
            (69.4811, 36.8308, 75.4949):53,
            (97.1382, -21.5559, 94.4825):54,
            (92.125, -51.6335, 88.501):55,
            (87.737, -86.1846, 83.1812):56,
            (88.9499, -71.2147, 31.6061):57,
            (91.1165, -48.0796, -14.1381):58,
            (58.0145, 11.3842, -65.6058):59,
            (32.3026, 79.1967, -107.8637):60,
            (45.9331, 86.4699, -84.8483):61,
            (60.3199, 98.2542, -60.843):62,
            (55.6111, 86.4597, -9.1916):63,
            (60.8927, 62.8729, 35.0702):64,
            (78.8241, 18.6736, 56.0796):65,
            (97.6208, -17.6977, 66.4162):66,
            (94.1539, -37.4631, 68.7023):67,
            (89.8813, -66.1541, 56.3842):68,
            (91.0093, -53.1765, 13.8066):69,
            (92.571, -38.7824, -11.8131):70,
            (70.8615, -4.4808, -45.0866):71,
            (47.6091, 49.3215, -82.3961):72,
            (58.1323, 68.3853, -64.8302):73,
            (68.0079, 76.2368, -48.6298):74,
            (63.3723, 71.7112, -18.3923):75,
            (74.4686, 36.8822, 15.7988):76,
            (87.1187, 8.2035, 33.0227):77,
            (98.1056, -13.9188, 47.2642):78,
            (96.0337, -24.7493, 44.2003):79,
            (92.1264, -48.2196, 38.3812):80,
            (93.3211, -36.9827, 8.0947):81,
            (94.2302, -28.9926, -9.1665):82,
            (82.3123, -6.9657, -27.1167):83,
            (68.0684, 23.3938, -49.2364):84,
            (73.6833, 41.0464, -40.0349):85,
            (77.4342, 51.3197, -33.9217):86,
            (74.2811, 48.1595, -14.7725):87,
            (0.0, 0.0, 0.0):88,
            (5.8822, 0.0022, -0.0022):89,
            (16.1144, 0.0022, -0.0033):90,
            (22.6151, 0.0018, -0.004):91,
            (32.7476, 0.0018, -0.0044):92,
            (42.7837, 0.0032, -0.0055):93,
            (53.9767, 0.0034, -0.0063):94,
            (65.4912, 0.0036, -0.0074):95,
            (76.2461, 0.0044, -0.0083):96,
            (89.8837, 0.0048, -0.0094):97,
            (100.0, 0.0053, -0.0104):98}
        self.colors16 = {
            (100.0, 0.0053, -0.0104):0,
            (0.0, 0.0, 0.0):1,
            (12.8119, 47.2407, -64.3396):2,
            (52.8041, -57.1624, 55.1703):3,
            (53.2329, 80.1093, 67.2201):4,
            (25.2966, 47.7847, 37.7562):5,
            (36.8705, 68.0659, -42.1489):6,
            (66.4237, 42.1616, 73.4335):7,
            (97.1382, -21.5559, 94.4825):8,
            (86.8105, -85.4149, 82.4382):9,
            (55.0455, -31.8888, -9.3772):10,
            (91.1165, -48.0796, -14.1381):11,
            (31.8712, 78.4892, -106.9003):12,
            (60.3199, 98.2542, -60.843):13,
            (53.1928, 0.0029, -0.0061):14,
            (84.1985, 0.0045, -0.0089):15}
        self.colors99= {
            (100.0, 0.0053, -0.0104):0,
            (0.0, 0.0, 0.0):1,
            (12.8119, 47.2407, -64.3396):2,
            (52.8041, -57.1624, 55.1703):3,
            (53.2329, 80.1093, 67.2201):4,
            (25.2966, 47.7847, 37.7562):5,
            (36.8705, 68.0659, -42.1489):6,
            (66.4237, 42.1616, 73.4335):7,
            (97.1382, -21.5559, 94.4825):8,
            (86.8105, -85.4149, 82.4382):9,
            (55.0455, -31.8888, -9.3772):10,
            (91.1165, -48.0796, -14.1381):11,
            (31.8712, 78.4892, -106.9003):12,
            (60.3199, 98.2542, -60.843):13,
            (53.1928, 0.0029, -0.0061):14,
            (84.1985, 0.0045, -0.0089):15,
            (11.5497, 31.8768, 18.1739):16,
            (17.5866, 15.7066, 25.9892):17,
            (29.0208, -8.5776, 37.5533):18,
            (27.2543, -19.015, 35.3673):19,
            (25.2798, -34.2963, 32.8426):20,
            (25.8276, -27.5812, 10.7515):21,
            (26.6245, -19.1316, -5.6261):22,
            (14.986, 1.2467, -23.6473):23,
            (4.1091, 27.6851, -41.3905):24,
            (9.2862, 34.8709, -32.6869):25,
            (14.3696, 39.0991, -24.2113):26,
            (12.6512, 34.8073, -6.066):27,
            (22.699, 44.779, 34.3145):28,
            (31.2054, 21.9979, 41.7676):29,
            (47.2407, -12.0488, 52.8125):30,
            (44.5753, -27.9355, 49.6338):31,
            (41.9858, -48.1745, 46.4957):32,
            (42.7207, -39.1444, 16.0528):33,
            (43.8747, -26.8746, -7.9028):34,
            (26.5278, 3.8603, -34.8152):35,
            (11.0, 44.2673, -60.2918):36,
            (19.0423, 48.637, -46.7161):37,
            (26.6606, 54.9202, -34.0091):38,
            (24.1377, 48.6121, -6.8774):39,
            (37.5243, 61.9327, 51.9413):40,
            (50.3904, 27.7338, 58.553):41,
            (71.4677, -16.6651, 73.0447):42,
            (67.5818, -39.987, 68.408):43,
            (64.1995, -66.6294, 64.3075):44,
            (65.1526, -54.8772, 23.9922):45,
            (66.8122, -37.1703, -10.9303):46,
            (41.6262, 7.9137, -50.0682):47,
            (21.343, 61.2273, -83.3898):48,
            (32.0743, 66.9878, -65.2716):49,
            (43.0033, 75.9603, -47.0378):50,
            (39.3866, 66.9043, -7.4929):51,
            (69.4811, 36.8308, 75.4949):53,
            (92.125, -51.6335, 88.501):55,
            (87.737, -86.1846, 83.1812):56,
            (88.9499, -71.2147, 31.6061):57,
            (58.0145, 11.3842, -65.6058):59,
            (32.3026, 79.1967, -107.8637):60,
            (45.9331, 86.4699, -84.8483):61,
            (55.6111, 86.4597, -9.1916):63,
            (60.8927, 62.8729, 35.0702):64,
            (78.8241, 18.6736, 56.0796):65,
            (97.6208, -17.6977, 66.4162):66,
            (94.1539, -37.4631, 68.7023):67,
            (89.8813, -66.1541, 56.3842):68,
            (91.0093, -53.1765, 13.8066):69,
            (92.571, -38.7824, -11.8131):70,
            (70.8615, -4.4808, -45.0866):71,
            (47.6091, 49.3215, -82.3961):72,
            (58.1323, 68.3853, -64.8302):73,
            (68.0079, 76.2368, -48.6298):74,
            (63.3723, 71.7112, -18.3923):75,
            (74.4686, 36.8822, 15.7988):76,
            (87.1187, 8.2035, 33.0227):77,
            (98.1056, -13.9188, 47.2642):78,
            (96.0337, -24.7493, 44.2003):79,
            (92.1264, -48.2196, 38.3812):80,
            (93.3211, -36.9827, 8.0947):81,
            (94.2302, -28.9926, -9.1665):82,
            (82.3123, -6.9657, -27.1167):83,
            (68.0684, 23.3938, -49.2364):84,
            (73.6833, 41.0464, -40.0349):85,
            (77.4342, 51.3197, -33.9217):86,
            (74.2811, 48.1595, -14.7725):87,
            (5.8822, 0.0022, -0.0022):89,
            (16.1144, 0.0022, -0.0033):90,
            (22.6151, 0.0018, -0.004):91,
            (32.7476, 0.0018, -0.0044):92,
            (42.7837, 0.0032, -0.0055):93,
            (53.9767, 0.0034, -0.0063):94,
            (65.4912, 0.0036, -0.0074):95,
            (76.2461, 0.0044, -0.0083):96,
            (89.8837, 0.0048, -0.0094):97}
        self.x256colors99 = [1,5,32,30,2,38,34,96,94,4,56,8,60,13,11,0,1,36,2,48,48,60,32,34,47,47,47,72,3,33,10,59,59,59,44,45,45,46,71,71,9,68,45,69,46,83,56,68,57,57,69,11,28,38,37,49,49,60,30,93,47,72,72,72,31,33,10,59,59,59,43,45,45,46,71,71,9,68,57,69,70,83,56,68,68,57,69,70,5,39,38,49,49,61,41,93,50,50,72,72,30,30,94,84,84,84,43,43,45,46,71,71,43,68,80,81,82,83,55,68,68,80,81,70,40,51,6,50,50,61,41,64,63,50,73,73,30,41,76,87,85,84,42,42,95,96,84,84,55,67,79,81,82,83,55,67,80,80,81,82,40,51,51,50,50,73,41,64,63,75,13,73,53,7,76,87,85,85,42,65,77,76,87,85,42,66,78,78,15,97,55,67,79,79,81,82,4,64,63,63,13,13,7,64,63,75,75,74,53,64,76,87,87,86,65,65,65,76,87,86,8,77,77,77,97,86,8,66,66,78,78,0,1,89,89,90,91,91,92,92,92,93,93,14,94,94,95,95,95,96,96,96,15,97,97,97]
        self.x256colors16 = [1,5,3,3,2,6,10,15,14,4,9,8,12,13,11,0,1,2,2,2,12,12,3,10,12,12,12,12,3,10,10,10,14,14,3,3,10,10,10,10,9,9,9,11,11,11,9,9,9,9,11,11,5,6,2,12,12,12,3,14,14,12,12,12,3,3,10,14,14,14,3,3,10,10,10,15,9,9,9,11,11,11,9,9,9,9,11,11,5,6,6,6,6,12,14,14,6,6,6,13,3,14,14,14,14,13,3,3,3,11,11,11,9,9,9,11,11,11,9,9,9,9,11,11,5,6,6,6,6,6,7,4,6,13,13,13,7,7,14,14,13,13,8,8,15,15,15,15,8,9,9,15,15,15,9,9,9,9,11,11,4,6,6,6,13,13,7,4,13,13,13,13,7,7,4,13,13,13,8,7,7,15,15,13,8,8,8,15,15,15,8,8,8,9,0,0,4,4,13,13,13,13,7,4,13,13,13,13,7,7,4,13,13,13,7,7,7,15,15,13,8,8,8,15,15,15,8,8,8,8,0,0,1,1,1,1,1,1,1,14,14,14,14,14,14,14,14,14,15,15,15,15,15,15,15,0]
        self.x256colors83 = [88,28,32,30,36,38,34,96,94,52,56,54,60,62,58,98,88,36,36,48,48,60,32,34,47,47,47,72,32,33,34,59,59,59,44,45,45,46,71,71,44,68,45,69,46,83,56,68,57,57,69,58,28,38,37,49,49,60,30,93,47,72,72,72,31,33,34,59,59,59,43,45,45,46,71,71,56,68,57,69,70,83,56,68,68,57,69,70,28,39,38,49,49,61,41,93,50,50,72,72,30,30,94,84,84,84,43,43,45,46,71,71,43,68,80,81,82,83,55,68,68,80,81,70,40,51,51,50,50,61,41,64,63,50,73,73,30,41,76,87,85,84,42,42,95,96,84,84,55,67,79,81,82,83,55,67,80,80,81,82,40,51,51,50,50,73,41,64,63,75,62,73,53,53,76,87,85,85,42,65,77,76,87,85,42,66,78,78,97,97,55,67,79,79,81,82,52,64,63,63,62,62,52,64,63,75,75,74,53,64,76,87,87,86,65,65,65,76,87,86,54,77,77,77,97,86,54,66,66,78,78,98,88,89,89,90,91,91,92,92,92,93,93,94,94,94,95,95,95,96,96,96,97,97,97,97]
        self.x16colors = {
            '30':'01',
            '31':'04',
            '32':'03',
            '33':'08',
            '34':'02',
            '35':'06',
            '36':'10',
            '37':'15',
            '30;1':'14',
            '31;1':'07',
            '32;1':'09',
            '33;1':'08',
            '34;1':'12',
            '35;1':'13',
            '36;1':'11',
            '37;1':'00',
            '40':'01',
            '41':'04',
            '42':'03',
            '43':'08',
            '44':'02',
            '45':'06',
            '46':'10',
            '47':'15',
            '40;1':'14',
            '41;1':'07',
            '42;1':'09',
            '43;1':'08',
            '44;1':'12',
            '45;1':'13',
            '46;1':'11',
            '47;1':'00'}

    def doPrivmsg(self, irc, msg):
        channel = msg.args[0]
        self.stopped.setdefault(channel, None)
        if msg.args[1].lower().strip()[1:] == 'cq':
            self.stopped[channel] = True

    def doPaste(self, description, paste):
        try:
            apikey = self.registryValue('pasteAPI')
            payload = {'description':description,'sections':[{'contents':paste}]}
            headers = {'X-Auth-Token':apikey}
            post_response = requests.post(url='https://api.paste.ee/v1/pastes', json=payload, headers=headers)
            response = post_response.json()
            return response['link'].replace('/p/', '/r/')
        except:
            return "Error. Did you set a valid Paste.ee API Key? https://paste.ee/account/api"

    def renderImage(self, text, size=18, defaultBg = 1, defaultFg = 0):
        try:
            if utf8 and not isinstance(text, unicode):
                text = text.decode('utf-8')
        except:
            pass
        text = text.replace('\t', ' ')
        self.strip_colors_regex = re.compile('(\x03([0-9]{1,2})(,[0-9]{1,2})?)|[\x0f\x02\x1f\x03\x16]').sub
        path = os.path.dirname(os.path.abspath(__file__))
        defaultFont = "{0}/DejaVu.ttf".format(path)
        def strip_colors(string):
            return self.strip_colors_regex('', string)
        _colorRegex = re.compile('(([0-9]{1,2})(,([0-9]{1,2}))?)')
        IGNORE_CHRS = ('\x16','\x1f','\x02', '\x03', '\x0f')
        lineLens = [len(line) for line in strip_colors(text).splitlines()]
        maxWidth, height = max(lineLens), len(lineLens)
        font = ImageFont.truetype(defaultFont, size)
        fontX = 10
        fontY = 20
        imageX, imageY = maxWidth * fontX, height * fontY
        image = Image.new('RGB', (imageX, imageY), self.rgbColors[defaultBg])
        draw = ImageDraw.Draw(image)
        dtext, drect, match, x, y, fg, bg = draw.text, draw.rectangle, _colorRegex.match, 0, 0, defaultFg, defaultBg
        start = time.time()
        for text in text.split('\n'):
            ll, i = len(text), 0
            while i < ll:
                chr = text[i]
                if chr == "\x03":
                    m = match(text[i+1:i+6])
                    if m:
                        i+= len(m.group(1))
                        fg = int(m.group(2))
                        if m.group(4) is not None:
                            bg = int(m.group(4))
                    else:
                        bg, fg = defaultBg, defaultFg
                elif chr == "\x0f":
                    fg, bg = defaultFg, defaultBg
                elif chr not in IGNORE_CHRS:
                    if bg != defaultBg: # bg is not white, render it
                        drect((x, y, x+fontX, y+fontY), fill=self.rgbColors[bg])
                    if bg != fg: # text will show, render it. this saves a lot of time!
                        dtext((x, y), chr, font=font, fill=self.rgbColors[fg])
                    x += fontX
                i += 1
            y += fontY
            fg, bg, x = defaultFg, defaultBg, 0
        return image, imageX, imageY

    def getColor(self, pixel, speed):
        pixel = tuple(pixel)
        if self.colors == 16:
            colors = list(self.colors16.keys())
        elif self.colors == 99:
            colors = list(self.colors99.keys())
        else:
            colors = list(self.colors83.keys())
        try:
            return self.matches[pixel]
        except KeyError:
            closest_colors = sorted(colors, key=lambda color: self.distance(color, self.rgb2lab(pixel), speed))
            closest_color = closest_colors[0]
            if self.colors == 16:
                self.matches[pixel] = self.colors16[closest_color]
            elif self.colors == 99:
                self.matches[pixel] = self.colors99[closest_color]
            else:
                self.matches[pixel] = self.colors83[closest_color]
            return self.matches[pixel]

    def rgb2lab (self, inputColor) :
        num = 0
        RGB = [0, 0, 0]
        for value in inputColor :
            value = float(value) / 255
            if value > 0.04045 :
                value = ( ( value + 0.055 ) / 1.055 ) ** 2.4
            else :
                value = value / 12.92
            RGB[num] = value * 100
            num = num + 1
        XYZ = [0, 0, 0,]
        X = RGB [0] * 0.4124 + RGB [1] * 0.3576 + RGB [2] * 0.1805
        Y = RGB [0] * 0.2126 + RGB [1] * 0.7152 + RGB [2] * 0.0722
        Z = RGB [0] * 0.0193 + RGB [1] * 0.1192 + RGB [2] * 0.9505
        XYZ[ 0 ] = round( X, 4 )
        XYZ[ 1 ] = round( Y, 4 )
        XYZ[ 2 ] = round( Z, 4 )
        XYZ[ 0 ] = float( XYZ[ 0 ] ) / 95.047         # ref_X =  95.047   Observer= 2°, Illuminant= D65
        XYZ[ 1 ] = float( XYZ[ 1 ] ) / 100.0          # ref_Y = 100.000
        XYZ[ 2 ] = float( XYZ[ 2 ] ) / 108.883        # ref_Z = 108.883
        num = 0
        for value in XYZ :
            if value > 0.008856 :
                value = value ** ( 0.3333333333333333 )
            else :
                value = ( 7.787 * value ) + ( 16 / 116 )
            XYZ[num] = value
            num = num + 1
        Lab = [0, 0, 0]
        L = ( 116 * XYZ[ 1 ] ) - 16
        a = 500 * ( XYZ[ 0 ] - XYZ[ 1 ] )
        b = 200 * ( XYZ[ 1 ] - XYZ[ 2 ] )
        Lab [ 0 ] = round( L, 4 )
        Lab [ 1 ] = round( a, 4 )
        Lab [ 2 ] = round( b, 4 )
        return Lab

    def ciede2000(self, color1, color2):
        """
        Calculates color difference according to the `CIEDE 2000`_ formula. This is
        the most accurate algorithm currently implemented but also the most complex
        and slowest. Like CIE1994 it is largely based in CIE L*C*h* space, but with
        several modifications to account for perceptual uniformity flaws.
        .. _CIEDE 2000: https://en.wikipedia.org/wiki/Color_difference#CIEDE2000
        """
        # See WP article and Sharma 2005 for important implementation notes:
        # http://www.ece.rochester.edu/~gsharma/ciede2000/ciede2000noteCRNA.pdf
        #
        # Yes, there's lots of locals; but this is easiest to understand as it's a
        # near straight translation of the math
        # pylint: disable=too-many-locals
        C_ = (
            math.sqrt(color1[1] ** 2 + color1[2] ** 2) +
            math.sqrt(color2[1] ** 2 + color2[2] ** 2)
        ) / 2

        G = (1 - math.sqrt(C_ ** 7 / (C_ ** 7 + 25 ** 7))) / 2
        a1_prime = (1 + G) * color1[1]
        a2_prime = (1 + G) * color2[1]
        C1_prime = math.sqrt(a1_prime ** 2 + color1[2] ** 2)
        C2_prime = math.sqrt(a2_prime ** 2 + color2[2] ** 2)
        L_ = (color1[0] + color2[0]) / 2
        C_ = (C1_prime + C2_prime) / 2
        h1 = (
            0.0 if color1[2] == a1_prime == 0 else
            math.degrees(math.atan2(color1[2], a1_prime)) % 360
        )
        h2 = (
            0.0 if color2[2] == a2_prime == 0 else
            math.degrees(math.atan2(color2[2], a2_prime)) % 360
        )
        if C1_prime * C2_prime == 0.0:
            dh = 0.0
            h_ = h1 + h2
        elif abs(h1 - h2) <= 180:
            dh = h2 - h1
            h_ = (h1 + h2) / 2
        else:
            if h2 > h1:
                dh = h2 - h1 - 360
            else:
                dh = h2 - h1 + 360
            if h1 + h2 >= 360:
                h_ = (h1 + h2 - 360) / 2
            else:
                h_ = (h1 + h2 + 360) / 2

        dL = color2[0] - color1[0]
        dC = C2_prime - C1_prime
        dH = 2 * math.sqrt(C1_prime * C2_prime) * math.sin(math.radians(dh / 2))
        T = (
            1 -
            0.17 * math.cos(math.radians(h_ - 30)) +
            0.24 * math.cos(math.radians(2 * h_)) +
            0.32 * math.cos(math.radians(3 * h_ + 6)) -
            0.20 * math.cos(math.radians(4 * h_ - 63))
        )
        SL = 1 + (0.015 * (L_ - 50) ** 2) / math.sqrt(20 + (L_ - 50) ** 2)
        SC = 1 + 0.045 * C_
        SH = 1 + 0.015 * C_ * T
        RT = (
            -2 * math.sqrt(C_ ** 7 / (C_ ** 7 + 25 ** 7)) *
            math.sin(math.radians(60 * math.exp(-(((h_ - 275) / 25) ** 2))))
        )
        delta_e =  math.sqrt(
            (dL / SL) ** 2 +
            (dC / SC) ** 2 +
            (dH / SH) ** 2 +
            RT * (dC / SC) * (dH / SH)
        )
        return delta_e

    def distance(self, c1, c2, speed):
        if speed == 'fast':
            delta_e =  math.sqrt((c1[0] - c2[0]) **2 + (c1[1] - c2[1]) ** 2 + (c1[2] - c2[2]) **2)
        elif speed == 'slow':
            delta_e = self.ciede2000(c1, c2)
        return delta_e

    def process_ansi(self, ansi):
        if self.colors == 16:
            colors = self.x256colors16
        elif self.colors == 99:
            colors = self.x256colors99
        else:
            colors = self.x256colors83
        x16color1 = None
        x16color2 = None
        x256color1 = None
        x256color2 = None
        effect = None
        ansi = ansi.lower().strip('\x1b[').strip('m').split(';')
        if len(ansi) > 1:
            i = 0
            while i < len(ansi):
                if i >= len(ansi):
                    break
                elif ansi[i]== '0':
                    effect = 0
                    i += 1
                    continue
                elif ansi[i] == '1':
                    effect = 1
                    i += 1
                    continue
                elif ansi[i] == '4':
                    effect = 4
                    i += 1
                    continue
                elif ansi[i] == '2':
                    effect = 2
                    i += 1
                    continue
                elif int(ansi[i]) > 29 and int(ansi[i]) < 38:
                    if effect == 1 or ansi[-1] == '1':
                        x16color1 = self.x16colors['{0};1'.format(ansi[i])]
                        effect = None
                        i += 1
                        continue
                    else:
                        x16color1 = self.x16colors[ansi[i]]
                        i += 1
                        continue
                elif int(ansi[i]) > 39 and int(ansi[i]) < 48:
                    if effect == 1 or ansi[-1] == '1':
                        x16color2 = self.x16colors['{0};1'.format(ansi[i])]
                        effect = None
                        i += 1
                        continue
                    else:
                        x16color2 = self.x16colors[ansi[i]]
                        i += 1
                        continue
                elif ansi[i] == '38':
                    x256color1 = colors[int(ansi[i+2])]
                    i += 3
                    continue
                elif ansi[i] == '48':
                    x256color2 = colors[int(ansi[i+2])]
                    i += 3
                    continue
                else:
                    i += 1
                    continue
            if x16color1 and x16color2:
                color = '\x03{0},{1}'.format(x16color1, x16color2)
            elif x256color1 and x256color2:
                color = '\x03{0},{1}'.format('%02d' % x256color1, '%02d' % x256color2)
            elif x16color1:
                color = '\x03{0}'.format(x16color1)
            elif x16color2:
                color = '\x0399,{0}'.format(x16color2)
            elif x256color1:
                color = '\x03{0}'.format('%02d' % x256color1)
            elif x256color2:
                color = '\x0399,{0}'.format('%02d' % x256color2)
            else:
                color = ''
            if effect == 1:
                color += '\x02'
            if effect == 4:
                color += '\x1F'
        elif len(ansi[0]) > 0:
            if ansi[0] == '0':
                color = '\x0F'
            elif ansi[0] == '1' or ansi[0] == '2':
                color = '\x02'
            elif ansi[0] == '4':
                color = '\x1F'
            elif int(ansi[0]) > 29 and int(ansi[0]) < 38:
                color = '\x03{0}'.format(self.x16colors[ansi[0]])
            elif int(ansi[0]) > 39 and int(ansi[0]) < 48:
                color = '\x0399,{0}'.format(self.x16colors[ansi[0]])
            elif ansi[0][-1] == 'c':
                color = ' ' * int(ansi[0][:-1])
            else:
                color = ''
        else:
            color = ''
        if color != self.old_color:
            self.old_color = color
            return color
        else:
            return ''

    def ansi2irc(self, output):
        output = output.replace('\x1b[0m\x1b', '\x1b')
        output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', lambda m: self.process_ansi(m.group(0)), output)
        output = re.sub('\x0399,(\d\d)\x03(\d\d)', '\x03\g<2>,\g<1>', output)
        return output

    def png(self, irc, msg, args, optlist, url):
        """[--bg] [--fg] <url>
        Generate PNG from text file
        """
        optlist = dict(optlist)
        if 'bg' in optlist:
            bg = optlist.get('bg')
        else:
            bg = 1
        if 'fg' in optlist:
            fg = optlist.get('fg')
        else:
            fg = 0
        if url.startswith("https://paste.ee/p/"):
            url = re.sub("https://paste.ee/p/", "https://paste.ee/r/", url)
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        if "text/plain" in r.headers["content-type"]:
            file = requests.get(url, headers=header)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        try:
            file = file.content.decode()
        except:
            file = file.content.decode('cp437')
        file = re.sub('(\x03(\d+).*)\x03,', '\g<1>\x03\g<2>,', file).replace('\r\n','\n') 
        im, x, y = self.renderImage(file, 18, bg, fg)
        path = os.path.dirname(os.path.abspath(__file__))
        filepath = "{0}/tmp/tldr.png".format(path)
        im.save(filepath, "PNG")
        CLIENT_ID = self.registryValue('imgurAPI')
        imgur = pyimgur.Imgur(CLIENT_ID)
        uploaded_image = imgur.upload_image(filepath, title=url)
        irc.reply(uploaded_image.link, noLengthCheck=True, private=False, notice=False)
    png = wrap(png, [getopts({'bg':'int', 'fg':'int'}), ('text')])

    def ascii(self, irc, msg, args, channel, optlist, text):
        """[<channel>] [--font <font>] [--color <color1,color2>] [<text>]
        Text to ASCII art
        """
        if not channel:
            channel = msg.args[0]
        channel = msg.args[0]
        optlist = dict(optlist)
        font = None
        words = []
        if text:
            text = text.strip()
            if '|' in text:
                words = text.split('|')
        if 'color' in optlist:
            color = optlist.get('color')
            if "," in color:
                color = color.split(",")
                color1 = color[0].strip()
                color2 = color[1].strip()
            else:
                color1 = color
                color2 = None
        else:
            color1 = None
            color2 = None
        if 'font' in optlist:
             font = optlist.get('font')
             if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(word.strip(), font))
                         for line in data.text.splitlines():
                             if line.strip():
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False)
             else:
                 data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(text, font))
                 for line in data.text.splitlines():
                     if line.strip():
                         irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)
        elif 'font' not in optlist:
            if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(word.strip()))
                         for line in data.text.splitlines():
                             if line.strip():
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)
            else:
                data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(text))
                for line in data.text.splitlines():
                    if line.strip():
                        irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)

    ascii = wrap(ascii, [optional('channel'), getopts({'font':'text', 'color':'text'}), ('text')])

    def fontlist(self, irc, msg, args):
        """
        get list of fonts for text-to-ascii-art
        """
        fontlist = requests.get("https://artii.herokuapp.com/fonts_list")
        response = sorted(fontlist.text.split('\n'))
        irc.reply(str(response).replace('\'', '').replace('[', '').replace(']', ''))
    fontlist = wrap(fontlist)

    def img(self, irc, msg, args, channel, optlist, url):
        """[<#channel>] [--delay #.#] [--w <###>] [--s <#.#] [--16] [--99] [--83] [--ascii] [--block] [--1/2] [--1/4] [--chars <text>] [--ramp <text>] [--bg <0-98>] [--fg <0-98>] [--no-color] [--invert] [--dither] [--no-dither] <url>
        Image to ASCII Art.
        --w columns.
        --s saturation (1.0).
        --16 colors 0-15.
        --99 colors 0-98.
        --83 colors 16-98.
        --ascii color ascii.
        --block space block.
        --1/4 for 1/4 block.
        --1/2 for 1/2 block
        --chars <TEXT> color text.
        --ramp <TEXT> set ramp (".:-=+*#%@").
        --bg <0-98> set bg.
        --fg <0-99> set fg.
        --no-color greyscale ascii.
        --invert inverts ramp.
        --dither to reduce source colors.
        --no-dither for no color reduction.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        gscale = "\xa0"
        if '16' in optlist:
            self.colors = 16
        elif '83' in optlist:
            self.colors = 83
        elif '99' in optlist:
            self.colors = 99
        else:
            self.colors = self.registryValue('colors', msg.args[0])
        if 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        else:
            speed =  self.registryValue('speed', msg.args[0]).lower()
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if 'dither' in optlist:
            dither = True
        elif 'no-dither' in optlist:
            dither = False
        else:
            dither = self.registryValue('dither', msg.args[0])
        if 'bg' in optlist:
            bg = optlist.get('bg')
        else:
            bg = 1
        if 'fg' in optlist:
            fg = optlist.get('fg')
        else:
            fg = 99
        if 'chars' in optlist:
            type = 'ascii'
            gscale = optlist.get('chars')
        elif 'ramp' in optlist:
            type = 'ascii'
            gscale = optlist.get('ramp')
        elif 'ascii' in optlist and bg == 0 or bg == 98:
            type = 'ascii'
            gscale = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:\"^`'."
        elif 'ascii' in optlist:
            type = 'ascii'
            gscale = ".'`^\":;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
        elif '1/4' in optlist:
            type = '1/4'
        elif '1/2' in optlist:
            type = '1/2'
        elif 'block' in optlist:
            type = 'ascii'
            gscale = '\xa0'
        else:
            type = self.registryValue('imgDefault', msg.args[0]).lower()
        if 'no-color' in optlist and 'ramp' not in optlist and bg == 0 or bg == 98:
            type = 'no-color'
            gscale = "@%#*+=-:. "
        elif 'no-color' in optlist and 'ramp' not in optlist:
            type = 'no-color'
            gscale = " .:-=+*#%@"
        elif 'no-color' in optlist and 'chars' not in optlist:
            type = 'no-color'
        if not gscale.strip():
            gscale = '\xa0'
        if 'invert' in optlist and 'chars' not in optlist and gscale != '\xa0':
            gscale = gscale[::-1]
        if 'w' in optlist:
            cols = optlist.get('w')
        elif type == 'ascii' or type == 'no-color' or type == 'block':
            cols = self.registryValue('asciiWidth', msg.args[0])
        else:
            cols = self.registryValue('blockWidth', msg.args[0])
        if type == '1/4':
            cols = cols * 2
        if 's' in optlist:
            s = float(optlist.get('s'))
        path = os.path.dirname(os.path.abspath(__file__))
        filepath = "{0}/tmp".format(path)
        filename = "{0}/{1}".format(filepath, url.split('/')[-1])
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = requests.head(url, headers=header)
        if r.headers["content-type"] in image_formats:
            response = requests.get(url, headers=header)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        if response.status_code == 200:
            with open("{0}".format(filename), 'wb') as f:
                f.write(response.content)
        # open image and convert to grayscale
        image = Image.open(filename)
        if image.mode == 'RGBA':
            image = Image.alpha_composite(Image.new("RGBA", image.size, self.rgbColors[bg] + (255,)), image)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        try:
            os.remove(filename)
        except:
            pass
        # store dimensions
        W, H = image.size[0], image.size[1]
        # compute width of tile
        w = W/cols
        # compute tile height based on aspect ratio and scale
        if type == '1/2':
            scale = 1.0
        else:
            scale = 0.5
        h = w/scale
        # compute number of rows
        rows = int(H/h)
        image = ImageOps.autocontrast(image)
        if type != 'no-color':
            image2 = image.resize((cols, rows), Image.LANCZOS)
            if 's' in optlist:
                image2 = ImageEnhance.Color(image2).enhance(s)
            if dither:
                image2 = image2.convert('P', palette=Image.ADAPTIVE)
                image2 = image2.convert('RGB')
            colormap = np.array(image2)
            self.matches = {}
        # ascii image is a list of character strings
        aimg = []
        if type == '1/2':
            k = 0
            for j in range(0, rows - 1, 2):
                # append an empty string
                aimg.append("")
                old_color1 = "99"
                old_color2 = "99"
                old_char = None
                for i in range(cols):
                    color1 = '%02d' % self.getColor(colormap[j][i].tolist(), speed)
                    color2 = '%02d' % self.getColor(colormap[j+1][i].tolist(), speed)
                    if color1 == color2:
                        gsval = " "
                    else:
                        gsval = "▀"
                    if color1 == old_color1 and color2 == old_color2:
                        aimg[k] += gsval
                        old_char = gsval
                    elif gsval == " " and color1 == old_color2:
                        aimg[k] += " "
                        old_char = gsval
                    elif gsval == " " and color1 == old_color1 and old_char != '█':
                        aimg[k] += "█"   
                        old_char = '█'
                    elif gsval == " " and color1 == old_color1 and old_char == '█':
                        aimg[k] = aimg[k][:-1]
                        aimg[k] += "\x0301,{0}  ".format(color2)
                        old_color1 = "01"
                        old_color2 = color2
                        old_char = gsval
                    elif gsval == " ":
                        aimg[k] += "\x0301,{0} ".format(color2)
                        old_color1 = "01"
                        old_color2 = color2
                        old_char = gsval
                    elif gsval == "▀" and color1 == old_color2 and color2 == old_color1 and 'tops' not in optlist:
                        aimg[k] += "▄"
                        old_char = gsval
                    elif gsval == "▀" and color1 == old_color2 and 'tops' not in optlist:
                        aimg[k] += "\x03{0}▄".format(color2)
                        old_color1 = color2
                        old_char = gsval
                    elif color1 != old_color1 and color2 == old_color2:
                        aimg[k] += "\x03{0}{1}".format(color1, gsval)
                        old_color1 = color1
                        old_char = gsval
                    else:
                        aimg[k] += "\x03{0},{1}{2}".format(color1, color2, gsval)
                        old_color1 = color1
                        old_color2 = color2
                        old_char = gsval
                aimg[k] = re.sub("\x0301,(\d\d)(\s+)\x03(\d\d)([^,])".format(i), "\x03\g<3>,\g<1>\g<2>\g<4>".format(i), aimg[k])
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = aimg[k].replace("{0}".format(i), "{0}".format(int(i)))
                k += 1
        elif type == '1/4':
            k = 0
            for j in range(0, rows - 1, 2):
                # append an empty string
                aimg.append("")
                old_color = "99,99"
                for i in range(0, cols - 1, 2):
                    color1 = '%02d' % self.getColor(colormap[j][i].tolist(), speed)
                    color2 = '%02d' % self.getColor(colormap[j+1][i].tolist(), speed)
                    color3 = '%02d' % self.getColor(colormap[j][i+1].tolist(), speed)
                    color4 = '%02d' % self.getColor(colormap[j+1][i+1].tolist(), speed)
                    if color1 == color2 and color1 == color3 and color1 == color4:
                        gsval = " "
                        color = "0,{0}".format(color1)
                    elif color1 == color4 and color2 == color3:
                        gsval = "▚"
                        color = "{0},{1}".format(color1, color2)
                    elif color1 == color2 and color1 == color3 and color1 != color4:
                        gsval = "▛"
                        color = "{0},{1}".format(color1, color4)
                    elif color3 == color4 and color2 == color4 and color3 != color1:
                        gsval = "▟"
                        color = "{0},{1}".format(color2, color1)
                    elif color1 == color2 and color1 == color4 and color1 != color3:
                        gsval = "▙"
                        color = "{0},{1}".format(color1, color3)
                    elif color1 == color3 and color1 == color4 and color1 != color2:
                        gsval = "▜"
                        color = "{0},{1}".format(color1, color2)
                    elif color1 == color3 and color2 == color4 and color1 != color2 and color3 != color4:
                        gsval = "▀"
                        color = "{0},{1}".format(color1, color4)
                    elif color1 == color2 and color3 == color4 and color1 != color3 and color2 != color4:
                        gsval = "▌"
                        color = "{0},{1}".format(color1, color4)
                    else:
                        row1 = '%02d' % self.getColor(np.average([tuple(colormap[j][i].tolist()), tuple(colormap[j][i+1].tolist())], axis=0).tolist(), speed)
                        row2 = '%02d' % self.getColor(np.average([tuple(colormap[j+1][i+1].tolist()), tuple(colormap[j][i+1].tolist())], axis=0).tolist(), speed)
                        if row2 == color1 and row2 != color3:
                            gsval = "▙"
                            color = "{0},{1}".format(row2, color3)
                        elif row1 == color2 and row1 != color4:
                            gsval = "▛"
                            color = "{0},{1}".format(row1, color4)
                        elif row2 == color3 and row2 != color1:
                            gsval = "▟"
                            color = "{0},{1}".format(row2, color1)
                        elif row1 == color4 and row1 != color2:
                            gsval = "▜"
                            color = "{0},{1}".format(row1, color2)
                        else:
                            col1 = '%02d' % self.getColor(np.average([tuple(colormap[j][i].tolist()), tuple(colormap[j+1][i].tolist())], axis=0).tolist(), speed)
                            col2 = '%02d' % self.getColor(np.average([tuple(colormap[j][i+1].tolist()), tuple(colormap[j+1][i+1].tolist())], axis=0).tolist(), speed)
                            if col1 == color4 and col1 != color3:
                                gsval = "▙"
                                color = "{0},{1}".format(col1, color3)
                            elif col1 == color3 and col1 != color4:
                                gsval = "▛"
                                color = "{0},{1}".format(col1, color4)
                            elif col2 == color2 and col2 != color1:
                                gsval = "▟"
                                color = "{0},{1}".format(col2, color1)
                            elif col2 == color1 and col2 != color2:
                                gsval = "▜"
                                color = "{0},{1}".format(col2, color2)
                            elif row1 != row2:
                                gsval = "▀"
                                color = "{0},{1}".format(row1, row2)
                            elif col1 != col2:
                                gsval = "▌"
                                color = "{0},{1}".format(col1, col2)
                            elif row1 == row2:
                                gsval = " "
                                color = "0,{0}".format(row1)
                            elif col1 == col2:
                                gsval = " "
                                color = "0,{0}".format(col1)
                    if color != old_color:
                        if gsval == " " and "{0}".format(color.split(',')[1]) == "{0}".format(old_color.split(',')[1]):
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▚" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▞"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▀" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▄"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▌" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▐"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▛" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▟"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▟" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▛"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▜" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▙"
                            aimg[k] += "{0}".format(gsval)
                        elif gsval == "▙" and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            gsval = "▜"
                            aimg[k] += "{0}".format(gsval)
                        else:
                            old_color = color
                            # append char to string
                            aimg[k] += "\x03{0}{1}".format(color, gsval)
                    else:
                        aimg[k] += "{0}".format(gsval)
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = re.sub("\x030,{0}(\s+)\x03(\d\d),{0}".format(i), "\x03\g<2>,{0}\g<1>".format(i), aimg[k])
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = aimg[k].replace("{0}".format(i), "{0}".format(int(i)))
                k += 1
        else:
            if 'chars' not in optlist and gscale != '\xa0':
                image = image.resize((cols, rows), Image.LANCZOS)
                image = image.convert('L')
                lumamap = np.array(image)
            # generate list of dimensions
            char = 0
            for j in range(rows):
                # append an empty string
                aimg.append("")
                old_color = None
                for i in range(cols):
                    if 'chars' not in optlist and gscale != '\xa0':
                        # get average luminance
                        avg = int(np.average(lumamap[j][i]))
                        # look up ascii char
                        gsval = gscale[int((avg * (len(gscale) - 1))/255)]
                    elif 'chars' in optlist and gscale != '\xa0':
                        if char < len(gscale):
                            gsval = gscale[char]
                            char += 1
                        else:
                            char = 0
                            gsval = gscale[char]
                            char += 1
                    else:
                        gsval = '\xa0'
                    # get color value
                    if type != 'no-color' and i == 0:
                        color = self.getColor(colormap[j][i].tolist(), speed)
                        old_color = color
                        if 'bg' not in optlist:
                            if gsval != '\xa0':
                                if gsval.isdigit():
                                    color = "{:02d}".format(int(color))
                                    aimg[j] += "\x03{0}{1}".format(color, gsval)
                                else:
                                    aimg[j] += "\x03{0}{1}".format(int(color), gsval)
                            else:
                                aimg[j] += "\x030,{0} ".format(int(color))
                        else:
                            if gsval != '\xa0':
                                if gsval.isdigit():
                                    newbg = "{:02d}".format(int(bg))
                                    aimg[j] += "\x03{0},{1}{2}".format(int(color), newbg, gsval)
                                else:
                                    aimg[j] += "\x03{0},{1}{2}".format(int(color), int(bg), gsval)
                            else:
                                aimg[j] += "\x030,{0} ".format(int(color))
                    elif type != 'no-color' and gsval != ' ':
                        color = self.getColor(colormap[j][i].tolist(), speed)
                        if color != old_color:
                            old_color = color
                            # append ascii char to string
                            if 'bg' not in optlist:
                                if gsval != '\xa0':
                                    if gsval.isdigit():
                                        color = "{:02d}".format(int(color))
                                        aimg[j] += "\x03{0}{1}".format(color, gsval)
                                    else:
                                        aimg[j] += "\x03{0}{1}".format(int(color), gsval)
                                else:
                                    aimg[j] += "\x030,{0} ".format(int(color))
                            else:
                                if gsval != '\xa0':
                                    if gsval.isdigit():
                                        newbg = "{:02d}".format(int(bg))
                                        aimg[j] += "\x03{0},{1}{2}".format(int(color), newbg, gsval)
                                    else:
                                        aimg[j] += "\x03{0},{1}{2}".format(int(color), int(bg), gsval)
                                else:
                                    aimg[j] += "\x030,{0} ".format(int(color))
                        else:
                            aimg[j] += "{0}".format(gsval)
                    else:
                        aimg[j] += "{0}".format(gsval)
        # return txt image
        output = aimg
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output:
            if type == 'no-color' and 'fg' in optlist and 'bg' in optlist:
                newbg = "{:02d}".format(int(bg))
                line = "\x03{0},{1}{2}".format(int(fg), newbg, line)
            elif type == 'no-color' and 'fg' in optlist:
                newfg = "{:02d}".format(int(fg))
                line = "\x03{0}{1}".format(newfg, line)
            elif type == 'no-color' and 'bg' in optlist:
                newbg = "{:02d}".format(int(bg))
                line = "\x0399,{0}{1}".format(newbg, line)
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick=False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
    img = wrap(img,[optional('channel'), getopts({'w':'int', 'invert':'', 'fast':'', 'slow':'', '16':'', '99':'', '83':'', 'delay':'float', 'dither':'', 'no-dither':'', 'chars':'text', 'bg':'int', 'fg':'int', 'ramp':'text', 'no-color':'', 'block':'', 'ascii':'', '1/4':'', '1/2':'', 's':'float', 'tops':''}), ('text')])

    def scroll(self, irc, msg, args, channel, optlist, url):
        """[<channel>] [--delay] <url>
        Play ASCII/ANSI art text files from web links.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        self.stopped[msg.args[0]] = False
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if url.startswith("https://paste.ee/p/"):
            url = re.sub("https://paste.ee/p/", "https://paste.ee/r/", url)
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        if "text/plain" in r.headers["content-type"]:
            file = requests.get(url, headers=header)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        file = file.content.decode()
        for line in file.splitlines():
            if line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
    scroll = wrap(scroll, [optional('channel'), getopts({'delay':'float'}), ('text')])

    def a2m(self, irc, msg, args, channel, optlist, url):
        """[<channel>] [--delay] [--l] [--r] [--n] [--p] [--t] [--w] <url>
        Convert ANSI files to IRC formatted text. https://github.com/tat3r/a2m
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        opts = ''
        if 'l' in optlist:
            l = optlist.get('l')
            opts += '-l {0} '.format(l)
        if 'r' in optlist:
            r = optlist.get('r')
            opts += '-r {0} '.format(r)
        if 'n' in optlist:
            opts += '-n '.format(n)
        if 'p' in optlist:
            opts += '-p '.format(p)
        if 't' in optlist:
            t = optlist.get('t')
            opts += '-t {0} '.format(t)
        if 'w' in optlist:
            w = optlist.get('w')
            opts += '-w {0} '.format(w)
        else:
            opts += '-w 80 '
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        try:
            if "text/plain" in r.headers["content-type"] or "application/octet-stream" in r.headers["content-type"] and int(r.headers["content-length"]) < 1000000:
                path = os.path.dirname(os.path.abspath(__file__))
                filepath = "{0}/tmp".format(path)
                filename = "{0}/{1}".format(filepath, url.split('/')[-1])
                r = requests.get(url, headers=header)
                open(filename, 'wb').write(r.content)
                try:
                    output = pexpect.run('a2m {0} {1}'.format(opts.strip(), str(filename)))
                    try:
                        os.remove(filename)
                    except:
                        pass
                except:
                    irc.reply("Error. Have you installed A2M? https://github.com/tat3r/a2m", private=False, notice=False)
                    return
            else:
                irc.reply("Invalid file type.")
                return
        except:
            irc.reply("Invalid file type.")
            return
        paste = ""
        self.stopped[msg.args[0]] = False
        output = re.sub('(\x03(\d+).*)\x03,', '\g<1>\x03\g<2>,', output.decode())
        for line in output.splitlines():
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
    a2m = wrap(a2m, [optional('channel'), getopts({'l':'int', 'r':'int', 't':'int', 'w':'int', 'delay':'float'}), ('text')])

    def p2u(self, irc, msg, args, channel, optlist, url):
        """[<channel>] [--b] [--f] [--p] [--s] [--t] [--w] [--delay] <url>
        Picture to Unicode. https://git.trollforge.org/p2u/about/
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        opts = ''
        if 'b' in optlist:
            b = optlist.get('b')
            opts += '-b {0} '.format(b)
        if 'f' in optlist:
            f = optlist.get('f')
            opts += '-f {0} '.format(f)
        else:
            opts += '-f m '
        if 'p' in optlist:
            p = optlist.get('p')
            opts += '-p {0} '.format(p)
        else:
            opts += '-p x '
        if 's' in optlist:
            s = optlist.get('s')
            opts += '-s {0} '.format(s)
        if 't' in optlist:
            t = optlist.get('t')
            opts += '-t {0} '.format(t)
        if 'w' in optlist:
            w = optlist.get('w')
            opts += '-w {0} '.format(w)
        else:
            w = self.registryValue('blockWidth', msg.args[0])
            opts += '-w {0} '.format(w)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        path = os.path.dirname(os.path.abspath(__file__))
        filepath = "{0}/tmp".format(path)
        filename = "{0}/{1}".format(filepath, url.split('/')[-1])
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = requests.head(url, headers=header)
        if r.headers["content-type"] in image_formats:
            response = requests.get(url, headers=header)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        if response.status_code == 200:
            with open("{0}".format(filename), 'wb') as f:
                f.write(response.content)
            try:
                output = pexpect.run('p2u -f m {0} {1}'.format(opts.strip(), str(filename)))
                try:
                    os.remove(filename)
                except:
                    pass
            except:
                irc.reply("Error. Have you installed p2u? https://git.trollforge.org/p2u", private=False, notice=False)
                return
            paste = ""
            self.stopped[msg.args[0]] = False
            for line in output.splitlines():
                line = line.decode()
                line = re.sub('^\x03 ', ' ', line)
                if self.registryValue('pasteEnable', msg.args[0]):
                    paste += line + "\n"
                if line.strip() and not self.stopped[msg.args[0]]:
                    time.sleep(delay)
                    irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            if self.registryValue('pasteEnable', msg.args[0]):
                irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
        else:
            irc.reply("Unexpected file type or link format", private=False, notice=False)
    p2u = wrap(p2u, [optional('channel'), getopts({'b':'int', 'f':'text', 'p':'text', 's':'int', 't':'int', 'w':'int', 'delay':'float'}), ('text')])

    def tdf(self, irc, msg, args, channel, optlist, text):
        """[<channel>] [--f] [--j] [--w] [--e] [--r] [--i][--delay] <text>
        Text to TheDraw ANSI Fonts. http://www.roysac.com/thedrawfonts-tdf.html
        --f [font] Specify font file used.
        --j l|r|c  Justify left, right, or center.  Default is left.
        --w n      Set screen width.  Default is 80.
        --c a|m    Color format ANSI or mirc.  Default is ANSI.
        --i        Print font details.
        --r        Use random font.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        opts = ''
        if 'f' in optlist:
            f = optlist.get('f')
            opts += '-f {0} '.format(f.lower())
        else:
            opts += '-r '
        if 'j' in optlist:
            j = optlist.get('j')
            opts += '-j {0} '.format(j)
        if 'w' in optlist:
            w = optlist.get('w')
            opts += '-w {0} '.format(w)
        else:
            opts += '-w 80 '
        if 'e' in optlist:
            e = optlist.get('e')
            opts += '-e {0} '.format(e)
        if 'r' in optlist:
            opts += '-r '
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if 'i' in optlist:
            opts += '-i '
        try:
            output = pexpect.run('tdfiglet -c m {0} {1}'.format(opts.strip(), r'{}'.format(text)))
        except:
            irc.reply("Error. Have you installed tdfiglet? https://github.com/tat3r/tdfiglet", private=False, notice=False)
            return
        paste = ""
        self.stopped[msg.args[0]] = False
        output = output.decode().replace('\r\r\n', '\r\n')
        for line in output.splitlines():
            line = re.sub('\x03\x03\s*', '\x0F ', line)
            line = re.sub('\x0F\s*\x03$', '', line)
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(text, paste), private=False, notice=False, to=channel)
    tdf = wrap(tdf, [optional('channel'), getopts({'f':'text', 'j':'text', 'w':'int', 'e':'text', 'r':'', 'i':'', 'delay':'float'}), ('text')])

    def toilet(self, irc, msg, args, channel, optlist, text):
        """[<channel>] [--f fontname] [--F filter1,filter2,etc.] [--w] [--delay] <text>
        Toilet. -f to select font. -F to select filters. Separate multiple filters with a comma.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        opts = ''
        if 'f' in optlist:
            f = optlist.get('f')
            opts += '-f {0} '.format(f)
        if 'F' in optlist:
            filter = optlist.get('F')
            if ',' in filter:
                filter = filter.split(',')
                for i in range(len(filter)):
                    opts += '-F {0} '.format(filter[i])
            else:
                opts += '-F {0} '.format(filter)
        if 'w' in optlist:
            w = optlist.get('w')
            opts += '-w {0} '.format(w)
        elif 'W' in optlist:
            opts += '-W '
        else:
            opts += '-w 100 '
        if 's' in optlist:
            opts += '-s '
        elif 'k' in optlist:
            opts += '-k '
        elif 'o' in optlist:
            opts += '-o '
        elif 'S' in optlist:
            opts += '-S '
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        try:
            output = pexpect.run('toilet --irc {0} {1}'.format(opts.strip(), text))
        except:
            irc.reply("Error. Have you installed toilet?", private=False, notice=False)
            return
        paste = ""
        self.stopped[msg.args[0]] = False
        output = output.decode().replace('\r\r\n', '\r\n')
        for line in output.splitlines():
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(text, paste), private=False, notice=False, to=channel)
    toilet = wrap(toilet, [optional('channel'), getopts({'f':'text', 'F':'text', 's':'', 'S':'', 'k':'', 'w':'int', 'W':'', 'o':'', 'delay':'float'}), ('text')])

    def fonts(self, irc, msg, args, optlist):
        """[--toilet]
        List figlets. Default list are tdf fonts. --toilet for toilet fonts
        """
        optlist = dict(optlist)
        if 'toilet' in optlist:
            try:
                reply = ", ".join(sorted(os.listdir("/usr/share/figlet")))
                irc.reply(reply, prefixNick=False)
            except:
                irc.reply("Sorry, unable to access font directory /usr/share/figlet")
        else:
            try:
                reply = ", ".join(sorted(os.listdir("/usr/local/share/tdfiglet/fonts/")))
                irc.reply("http://www.roysac.com/thedrawfonts-tdf.html", prefixNick=False)
                irc.reply(reply, prefixNick=False)
            except FileNotFoundError:
                reply = ", ".join(sorted(os.listdir("/usr/share/figlet")))
                irc.reply(reply, prefixNick=False)
            except:
                irc.reply("Sorry, unable to access font directories /usr/local/share/tdfiglet/fonts/ or /usr/share/figlet")
    fonts = wrap(fonts, [getopts({'toilet':''})])

    def wttr(self, irc, msg, args, channel, optlist, location):
        """[<channel>] [--16] [--99] <location/moon>
        ASCII weather report from wttr.in for <location>.
        --16 for 16 colors (default).
        --99 for 99 colors.
        Get moon phase with 'wttr moon'.
        <location>?u (use imperial units).
        <location>?m (metric).
        <location>?<1-3> (number of days)
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if '16' in optlist:
            self.colors = 16
        elif '99' in optlist:
            self.colors = 99
        else:
            self.colors = self.registryValue('colors', msg.args[0])
        if 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        else:
            speed = 'fast'
        file = requests.get("http://wttr.in/{0}".format(location))
        output = file.content.decode()
        self.matches = {}
        output = self.ansi2irc(output)
        output = re.sub('⚡', '☇ ', output)
        output = re.sub('‘‘', '‘ ', output)
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output.splitlines():
            line = line.strip('\x0F')
            if not line.strip() and not self.stopped[msg.args[0]]:
                if self.registryValue('pasteEnable', msg.args[0]):
                    paste += line + "\n"
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif line.strip() and not self.stopped[msg.args[0]] and not line.startswith("Follow"):
                if self.registryValue('pasteEnable', msg.args[0]):
                    paste += line + "\n"
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(location, paste), private=False, notice=False, to=channel)
    wttr = wrap(wttr, [optional('channel'), getopts({'delay':'float', '16':'', '99':'', 'fast':'', 'slow':''}), ('text')])

    def rate(self, irc, msg, args, channel, optlist, coin):
        """[<channel>] [--16] [--99] [--sub <text>] [coin]
        Crypto exchange rate info from rate.sx. http://rate.sx/:help. Use --sub to set subdomain e.g. eur, btc, etc.
        Get a graph with [coin] e.g. 'rate btc'.
        --16 for 16 colors (default).
        --99 for 99 colors.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if '16' in optlist:
            self.colors = 16
        elif '99' in optlist:
            self.colors = 99
        else:
            self.colors = self.registryValue('colors', msg.args[0])
        if 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        else:
            speed = 'fast'
        if 'sub' in optlist:
            sub = optlist.get('sub')
        else:
            sub = 'usd'
        if not coin:
            coin = ''
        self.matches= {}
        file = requests.get("http://{0}.rate.sx/{1}".format(sub, coin))
        output = file.content.decode()
        output = self.ansi2irc(output)
        output = output.replace('\x1b(B', '')
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output.splitlines():
            line = line.strip('\x0F')
            if not line.strip() and not self.stopped[msg.args[0]]:
                if self.registryValue('pasteEnable', msg.args[0]):
                    paste += line + "\n"
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif line.strip() and not self.stopped[msg.args[0]] and "Follow @igor_chubin" not in line:
                if self.registryValue('pasteEnable', msg.args[0]):
                    paste += line + "\n"
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(coin, paste), private=False, notice=False, to=channel)
    rate = wrap(rate, [optional('channel'), getopts({'delay':'float', '16':'', '99':'', 'sub':'text', 'fast':'', 'slow':''}), optional('text')])

    def cow(self, irc, msg, args, channel, optlist, text):
        """[<channel>] [--delay] [--type <character>] <text>
        Cowsay
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if 'type' in optlist:
            type = optlist.get('type')
        else:
            type = 'default'
        data = requests.get("https://easyapis.soue.tk/api/cowsay?text={0}&type={1}".format(text, type))
        self.stopped[msg.args[0]] = False
        paste = ''
        for line in data.text.splitlines():
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif line.strip() and not self.stopped[msg.args[0]] and "Follow @igor_chubin" not in line:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(text, paste), private=False, notice=False, to=channel)
    cow = wrap(cow, [optional('channel'), getopts({'delay':'float', 'type':'text'}), ('text')])

    def fortune(self, irc, msg, args, channel, optlist):
        """[<channel>]
        Returns a random ASCII from http://www.asciiartfarts.com/fortune.txt
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        self.stopped[msg.args[0]] = False
        data = requests.get("http://www.asciiartfarts.com/fortune.txt")
        fortunes = data.text.split('%\n')
        fortune = random.randrange(0, len(fortunes))
        for line in fortunes[fortune].splitlines():
            if not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif line.strip() and not self.stopped[msg.args[0]] and "Follow @igor_chubin" not in line:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
    fortune = wrap(fortune, [optional('channel'), getopts({'delay':'float'})])
    
    def mircart(self, irc, msg, args, channel, optlist, search):
        """[<channel>] (search text)
        Search https://mircart.org/ and scroll first result
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        self.stopped[msg.args[0]] = False
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        data = requests.get("https://mircart.org/?s={0}".format(search), headers=header)
        soup = BeautifulSoup(data.text)
        url = soup.find(href=re.compile(".txt"))
        data = requests.get(url.get('href'), headers=header)
        output = data.content.decode()
        for line in output.splitlines():
            if not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            elif line.strip() and not self.stopped[msg.args[0]] and "Follow @igor_chubin" not in line:
                time.sleep(delay)
                irc.reply(line, prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
        irc.reply(url.get('href'))
    mircart = wrap(mircart, [optional('channel'), getopts({'delay':'float'}), ('text')])

    def cq(self, irc, msg, args):
        """
        Stop the scroll.
        """
        if not self.stopped[msg.args[0]]:
            self.stopped[msg.args[0]] = True
            irc.reply("Stopping.")
    cq = wrap(cq)

Class = ASCII
