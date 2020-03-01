###
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

import supybot.ansi as ansi
import supybot.utils as utils
from supybot.commands import *
import supybot.plugins as plugins
import supybot.ircutils as ircutils
import supybot.ircdb as ircdb
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
    _ = PluginInternationalization('TextArt')
except ImportError:
    # Placeholder that allows to run the plugin on a bot
    # without the i18n module
    _ = lambda x: x

class TextArt(callbacks.Plugin):
    """TextArt: Make Text Art"""
    threaded = True

    def __init__(self, irc):
        self.__parent = super(TextArt, self)
        self.__parent.__init__(irc)
        self.colors = 99
        self.stopped = {}
        self.old_color = None
        self.source_colors = 0
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
        self.x256colors99 = ['01','05','32','30','02','38','34','96','94','04','56','08','60','13','11','00','01','36','02','48','48','60','32','34','47','47','47','72','03','33','10','59','59','59','44','45','45','46','71','71','09','68','45','69','46','83','56','68','57','57','69','11','28','38','37','49','49','60','30','93','47','72','72','72','31','33','10','59','59','59','43','45','45','46','71','71','09','68','57','69','70','83','56','68','68','57','69','70','05','39','38','49','49','61','41','93','50','50','72','72','30','30','94','84','84','84','43','43','45','46','71','71','43','68','80','81','82','83','55','68','68','80','81','70','40','51','06','50','50','61','41','64','63','50','73','73','30','41','76','87','85','84','42','42','95','96','84','84','55','67','79','81','82','83','55','67','80','80','81','82','40','51','51','50','50','73','41','64','63','75','13','73','53','07','76','87','85','85','42','65','77','76','87','85','42','66','78','78','15','97','55','67','79','79','81','82','04','64','63','63','13','13','07','64','63','75','75','74','53','64','76','87','87','86','65','65','65','76','87','86','08','77','77','77','97','86','08','66','66','78','78','00','01','89','89','90','91','91','92','92','92','93','93','14','94','94','95','95','95','96','96','96','15','97','97','97']
        self.x256colors16 = ['01','05','03','03','02','06','10','15','14','04','09','08','12','13','11','00','01','02','02','02','12','12','03','10','12','12','12','12','03','10','10','10','14','14','03','03','10','10','10','10','09','09','09','11','11','11','09','09','09','09','11','11','05','06','02','12','12','12','03','14','14','12','12','12','03','03','10','14','14','14','03','03','10','10','10','15','09','09','09','11','11','11','09','09','09','09','11','11','05','06','06','06','06','12','14','14','06','06','06','13','03','14','14','14','14','13','03','03','03','11','11','11','09','09','09','11','11','11','09','09','09','09','11','11','05','06','06','06','06','06','07','04','06','13','13','13','07','07','14','14','13','13','08','08','15','15','15','15','08','09','09','15','15','15','09','09','09','09','11','11','04','06','06','06','13','13','07','04','13','13','13','13','07','07','04','13','13','13','08','07','07','15','15','13','08','08','08','15','15','15','08','08','08','09','00','00','04','04','13','13','13','13','07','04','13','13','13','13','07','07','04','13','13','13','07','07','07','15','15','13','08','08','08','15','15','15','08','08','08','08','00','00','01','01','01','01','01','01','01','14','14','14','14','14','14','14','14','14','15','15','15','15','15','15','15','00']
        self.x256colors83 = ['88','28','32','30','36','38','34','96','94','52','56','54','60','62','58','98','88','36','36','48','48','60','32','34','47','47','47','72','32','33','34','59','59','59','44','45','45','46','71','71','44','68','45','69','46','83','56','68','57','57','69','58','28','38','37','49','49','60','30','93','47','72','72','72','31','33','34','59','59','59','43','45','45','46','71','71','56','68','57','69','70','83','56','68','68','57','69','70','28','39','38','49','49','61','41','93','50','50','72','72','30','30','94','84','84','84','43','43','45','46','71','71','43','68','80','81','82','83','55','68','68','80','81','70','40','51','51','50','50','61','41','64','63','50','73','73','30','41','76','87','85','84','42','42','95','96','84','84','55','67','79','81','82','83','55','67','80','80','81','82','40','51','51','50','50','73','41','64','63','75','62','73','53','53','76','87','85','85','42','65','77','76','87','85','42','66','78','78','97','97','55','67','79','79','81','82','52','64','63','63','62','62','52','64','63','75','75','74','53','64','76','87','87','86','65','65','65','76','87','86','54','77','77','77','97','86','54','66','66','78','78','98','88','89','89','90','91','91','92','92','92','93','93','94','94','94','95','95','95','96','96','96','97','97','97','97']
        self.x16colors = {
            '30':'01',
            '31':'05',
            '32':'03',
            '33':'07',
            '34':'02',
            '35':'06',
            '36':'10',
            '37':'15',
            '30;1':'14',
            '31;1':'04',
            '32;1':'09',
            '33;1':'08',
            '34;1':'12',
            '35;1':'13',
            '36;1':'11',
            '37;1':'00',
            '40':'01',
            '41':'05',
            '42':'03',
            '43':'07',
            '44':'02',
            '45':'06',
            '46':'10',
            '47':'15',
            '40;1':'14',
            '41;1':'04',
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
            description = description.split('/')[-1]
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
        try:
            return self.matches[pixel]
        except KeyError:
            if self.colors == 16:
                colors = list(self.colors16.keys())
            elif self.colors == 99:
                colors = list(self.colors99.keys())
            else:
                colors = list(self.colors83.keys())
            closest_colors = sorted(colors, key=lambda color: self.distance(color, self.rgb2lab(pixel), speed))
            closest_color = closest_colors[0]
            if self.colors == 16:
                self.matches[pixel] = self.colors16[closest_color]
            elif self.colors == 99:
                self.matches[pixel] = self.colors99[closest_color]
            else:
                self.matches[pixel] = self.colors83[closest_color]
            self.source_colors += 1
            return self.matches[pixel]

    def rgb2lab (self, inputColor) :
        try:
            return self.labmatches[inputColor]
        except:
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
            self.labmatches[inputColor] = Lab
            return self.labmatches[inputColor]

    def ciede2000(self, lab1, lab2):
        """ CIEDE2000 color difference formula. https://peteroupc.github.io/colorgen.html"""
        dl=lab2[0]-lab1[0]
        hl=lab1[0]+dl*0.5
        sqb1=lab1[2]*lab1[2]
        sqb2=lab2[2]*lab2[2]
        c1=math.sqrt(lab1[1]*lab1[1]+sqb1)
        c2=math.sqrt(lab2[1]*lab2[1]+sqb2)
        hc7=math.pow((c1+c2)*0.5,7)
        trc=math.sqrt(hc7/(hc7+6103515625))
        t2=1.5-trc*0.5
        ap1=lab1[1]*t2
        ap2=lab2[1]*t2
        c1=math.sqrt(ap1*ap1+sqb1)
        c2=math.sqrt(ap2*ap2+sqb2)
        dc=c2-c1
        hc=c1+dc*0.5
        hc7=math.pow(hc,7)
        trc=math.sqrt(hc7/(hc7+6103515625))
        h1=math.atan2(lab1[2],ap1)
        if h1<0:
          h1=h1+math.pi*2
        h2=math.atan2(lab2[2],ap2)
        if h2<0:
          h2=h2+math.pi*2
        hdiff=h2-h1
        hh=h1+h2
        if abs(hdiff)>math.pi:
                hh=hh+math.pi*2
                if h2<=h1:
                   hdiff=hdiff+math.pi*2
                else:
                   hdiff=hdiff-math.pi*2
        hh=hh*0.5
        t2=1-0.17*math.cos(hh-math.pi/6)+0.24*math.cos(hh*2)
        t2=t2+0.32*math.cos(hh*3+math.pi/30)
        t2=t2-0.2*math.cos(hh*4-math.pi*63/180)
        dh=2*math.sqrt(c1*c2)*math.sin(hdiff*0.5)
        sqhl=(hl-50)*(hl-50)
        fl=dl/(1+(0.015*sqhl/math.sqrt(20+sqhl)))
        fc=dc/(hc*0.045+1)
        fh=dh/(t2*hc*0.015+1)
        dt=30*math.exp(-math.pow(36*hh-55*math.pi,2)/(25*math.pi*math.pi))
        r=-2*trc*math.sin(2*dt*math.pi/180)
        return math.sqrt(fl*fl+fc*fc+fh*fh+r*fc*fh)

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
                color = '\x03{0},{1}'.format(x256color1, x256color2)
            elif x16color1:
                color = '\x03{0}'.format(x16color1)
            elif x16color2:
                color = '\x0399,{0}'.format(x16color2)
            elif x256color1:
                color = '\x03{0}'.format(x256color1)
            elif x256color2:
                color = '\x0399,{0}'.format(x256color2)
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
        output = output.replace('\x1b(B\x1b[m', '\x1b[0m')
        output = output.replace('\x1b\x1b', '\x1b')
        output = re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', lambda m: self.process_ansi(m.group(0)), output)
        output = re.sub('\x0399,(\d\d)\x03(\d\d)', '\x03\g<2>,\g<1>', output)
        output = output.replace('\x0F\x03', '\x03')
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
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        if "text/plain" in r.headers["content-type"] or url.startswith('https://paste.ee/r/'):
            file = requests.get(url, headers=header, timeout=10)
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

    def artii(self, irc, msg, args, channel, optlist, text):
        """[<channel>] [--font <font>] [--color <color1,color2>] [<text>]
        Text to ASCII figlet fonts using the artii API
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
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(word.strip(), font), timeout=10)
                         for line in data.content.decode().splitlines():
                             if line.strip():
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False)
             else:
                 data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(text, font), timeout=10)
                 for line in data.content.decode().splitlines():
                     if line.strip():
                         irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)
        elif 'font' not in optlist:
            if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(word.strip()), timeout=10)
                         for line in data.content.decode().splitlines():
                             if line.strip():
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)
            else:
                data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(text), timeout=10)
                for line in data.content.decode().splitlines():
                    if line.strip():
                        irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False, private=False, notice=False, to=channel)

    artii = wrap(artii, [optional('channel'), getopts({'font':'text', 'color':'text'}), ('text')])

    def fontlist(self, irc, msg, args):
        """
        Get list of artii figlet fonts.
        """
        fontlist = requests.get("https://artii.herokuapp.com/fonts_list", timeout=10)
        response = sorted(fontlist.content.decode().split('\n'))
        irc.reply(str(response).replace('\'', '').replace('[', '').replace(']', ''))
    fontlist = wrap(fontlist)

    def img(self, irc, msg, args, channel, optlist, url):
        """[<#channel>] [--delay #.#] [--w <###>] [--s <#.#] [--16] [--99] [--83] [--ascii] [--block] [--1/2] [--chars <text>] [--ramp <text>] [--bg <0-98>] [--fg <0-98>] [--no-color] [--invert] <url>
        Image to IRC art.
        --w columns.
        --s saturation (1.0).
        --16 colors 0-15.
        --99 colors 0-98.
        --83 colors 16-98.
        --ascii color ascii.
        --block space block.
        --1/2 for 1/2 block
        --chars <TEXT> color text.
        --ramp <TEXT> set ramp (".:-=+*#%@").
        --bg <0-98> set bg.
        --fg <0-99> set fg.
        --no-color greyscale ascii.
        --invert inverts ramp.
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        if 'quantize' in optlist:
            quantize = True
        elif 'no-quantize' in optlist:
            quantize = False
        else:
            quantize = self.registryValue('quantize', msg.args[0])
        if 'bg' in optlist:
            bg = optlist.get('bg')
        else:
            bg = self.registryValue('bg', msg.args[0])
        if 'fg' in optlist:
            fg = optlist.get('fg')
        else:
            fg = self.registryValue('fg', msg.args[0])
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
        if 's' in optlist:
            s = float(optlist.get('s'))
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = requests.head(url, headers=header)
        if r.headers["content-type"] in image_formats:
            response = requests.get(url, stream=True, timeout=10, headers=header)
        else:
            irc.reply("Error: Invalid file type.", private=False, notice=False)
            return
        if response.status_code == 200:
            response.raw.decode_content = True
            image = Image.open(response.raw)
        else:
            irc.reply("Error: Unable to open image.", private=False, notice=False)
        # open image and convert to grayscale
        start_time = time.time()
        self.source_colors = 0
        if image.mode == 'RGBA':
            if bg == 99:
                newbg = 1
            else:
                newbg = bg
            image = Image.alpha_composite(Image.new("RGBA", image.size, self.rgbColors[newbg] + (255,)), image)
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
        if 'resize' in optlist:
            resize = optlist.get('resize')
        else:
            resize = self.registryValue('resize', msg.args[0])
        if type != 'no-color':
            image2 = image.resize((cols, rows), resize)
            if 's' in optlist:
                image2 = ImageEnhance.Color(image2).enhance(s)
            if quantize:
                image2 = image2.quantize(dither=None)
                image2 = image2.convert('RGB')
            colormap = np.array(image2)
            self.matches = {}
            self.labmatches = {}
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
                    elif gsval == " " and color1 == old_color1 and old_char == '█':
                        aimg[k] = aimg[k][:-1]
                        aimg[k] += "\x0301,{0}  ".format(color1)
                        old_color1 = "01"
                        old_color2 = color1
                        old_char = gsval
                    elif gsval == " " and color1 == old_color1 and old_char == '^█':
                        aimg[k] = aimg[k][:-4]
                        aimg[k] += "\x0301,{0}  ".format(color1)
                        old_color1 = "01"
                        old_color2 = color1
                        old_char = gsval
                    elif gsval == " " and color1 == old_color1 and old_char == "^^▀" and 'tops' not in optlist:
                        aimg[k] = aimg[k][:-7]
                        aimg[k] += "\x03{0},{1}▄ ".format(old_color2, color1)
                        old_color1 = old_color2
                        old_color2 = color1
                        old_char = gsval
                    elif gsval == " " and color1 == old_color1 and old_char != '█' and 'tops' not in optlist:
                        aimg[k] += "█"
                        old_char = '█'
                    elif gsval == " " and 'tops' not in optlist:
                        aimg[k] += "\x03{0}█".format(color1)
                        old_color1 = color1
                        old_char = '^█'
                    elif gsval != " " and color1 == old_color1 and old_char == '^█' and 'tops' not in optlist:
                        aimg[k] = aimg[k][:-4]
                        aimg[k] += "\x03{0},{1} ▄".format(color2, color1)
                        old_color1 = color2
                        old_color2 = color1
                        old_char = '▄'
                    elif gsval != " " and color2 == old_color1 and old_char == '^█':
                        aimg[k] = aimg[k][:-4]
                        aimg[k] += "\x03{0},{1} ▀".format(color1, color2)
                        old_color1 = color1
                        old_color2 = color2
                        old_char = gsval
                    elif gsval != " " and color1 == old_color2 and color2 == old_color1 and old_char == "^^▀" and 'tops' not in optlist:
                        aimg[k] = aimg[k][:-7]
                        aimg[k] += "\x03{0},{1}▄▀".format(color1, color2)
                        old_color1 = color1
                        old_color2 = color2
                        old_char = gsval
                    elif gsval != " " and color1 == old_color1 and color2 != old_color2 and old_char == "^^▀" and 'tops' not in optlist:
                        aimg[k] = aimg[k][:-7]
                        aimg[k] += "\x03{0},{1}▄\x03{2}▄".format(old_color2, color1, color2)
                        old_color1 = color2
                        old_color2 = color1
                        old_char = '▄'
                    elif gsval != " " and color1 == old_color1 and color2 != old_color2 and old_char == "^▀" and 'tops' not in optlist:
                        aimg[k] = aimg[k][:-4]
                        aimg[k] += "\x03{0},{1}▄\x03{2}▄".format(old_color2, color1, color2)
                        old_color1 = color2
                        old_color2 = color1
                        old_char = '▄'
                    elif gsval != " " and color1 == old_color2 and color2 == old_color1 and 'tops' not in optlist:
                        aimg[k] += "▄"
                        old_char = '▄'
                    elif gsval != " " and color1 == old_color2 and 'tops' not in optlist:
                        aimg[k] += "\x03{0}▄".format(color2)
                        old_color1 = color2
                        old_char = '▄'
                    elif color1 != old_color1 and color2 == old_color2:
                        aimg[k] += "\x03{0}{1}".format(color1, gsval)
                        old_color1 = color1
                        if gsval == ' ':
                            old_char = gsval
                        else:
                            old_char = '^▀'
                    else:
                        aimg[k] += "\x03{0},{1}{2}".format(color1, color2, gsval)
                        old_color1 = color1
                        old_color2 = color2
                        if gsval == ' ':
                            old_char = gsval
                        else:
                            old_char = '^^▀'
                if 'tops' in optlist:
                    aimg[k] = re.sub("\x03\d\d,(\d\d\s+\x03)", "\x0301,\g<1>", aimg[k])
                    aimg[k] = re.sub("\x03\d\d,(\d\d\s+$)", "\x0301,\g<1>", aimg[k])
                    aimg[k] = re.sub("\x03\d\d,(\d\d\s\x03)", "\x0301,\g<1>", aimg[k])
                aimg[k] = re.sub("\x0301,(\d\d)(\s+)\x03(\d\d)([^,])", "\x03\g<3>,\g<1>\g<2>\g<4>", aimg[k])
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = aimg[k].replace("{0}".format(i), "{0}".format(int(i)))
                k += 1
        else:
            if 'chars' not in optlist and gscale != '\xa0':
                image = image.resize((cols, rows), resize)
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
                    if type != 'no-color' and gscale != '\xa0' and i == 0:
                        color = self.getColor(colormap[j][i].tolist(), speed)
                        old_color = color
                        if bg != 99:
                            color = "{0},{1}".format(color, "{:02d}".format(int(bg)))
                        if gsval != '\xa0':
                            aimg[j] += "\x03{0}{1}".format(color, gsval)
                        else:
                            aimg[j] += "\x030,{0} ".format(int(color))
                    elif type == 'no-color' and i == 0:
                        if bg != 99 and fg != 99:
                            aimg[j] += "\x03{0},{1}{2}".format("{:02d}".format(int(fg)), "{:02d}".format(int(bg)), gsval)
                        elif fg != 99:
                            aimg[j] += "\x03{0}{1}".format("{:02d}".format(int(fg)), gsval)
                        elif bg != 99:
                            aimg[j] += "\x03{0},{1}{2}".format("{:02d}".format(int(fg)), "{:02d}".format(int(bg)), gsval)
                    elif type != 'no-color' and gsval != ' ':
                        color = self.getColor(colormap[j][i].tolist(), speed)
                        if color != old_color:
                            old_color = color
                            # append ascii char to string
                            if gsval != '\xa0':
                                if gsval.isdigit():
                                    color = "{:02d}".format(int(color))
                                    aimg[j] += "\x03{0}{1}".format(color, gsval)
                                else:
                                    aimg[j] += "\x03{0}{1}".format(int(color), gsval)
                            else:
                                aimg[j] += "\x030,{0} ".format(int(color))
                        else:
                            aimg[j] += "{0}".format(gsval)
                    else:
                        aimg[j] += "{0}".format(gsval)
        output = aimg
        paste = ""
        self.stopped[msg.args[0]] = False
        end_time = time.time()
        for line in output:
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick=False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('showStats', msg.args[0]):
            longest = len(max(output, key=len).encode('utf-8'))
            render_time = "{0:.2f}".format(end_time - start_time)
            irc.reply("[Source Colors: {0}, Render Time: {1} seconds, Longest Line: {2} bytes]".format(self.source_colors, render_time, longest), prefixNick=False)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
    img = wrap(img,[optional('channel'), getopts({'w':'int', 'invert':'', 'fast':'', 'slow':'', '16':'', '99':'', '83':'', 'delay':'float', 'resize':'int', 'quantize':'', 'no-quantize':'', 'chars':'text', 'bg':'int', 'fg':'int', 'ramp':'text', 'no-color':'', 'block':'', 'ascii':'', '1/2':'', 's':'float', 'tops':''}), ('text')])

    def scroll(self, irc, msg, args, channel, optlist, url):
        """[<channel>] [--delay] <url>
        Play IRC art files from web links.
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
        optlist = dict(optlist)
        self.stopped[msg.args[0]] = False
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if url.startswith("https://paste.ee/p/"):
            url = url.replace("https://paste.ee/p/", "https://paste.ee/r/")
        elif url.startswith("https://pastebin.com/") and '/raw/' not in url:
            url = url.replace("https://pastebin.com/", "https://pastebin.com/raw/")
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        if "text/plain" in r.headers["content-type"]:
            file = requests.get(url, timeout=10, headers=header)
        else:
            irc.reply("Invalid file type.", private=False, notice=False)
            return
        file = file.content.decode().replace('\r\n','\n')
        for line in file.split('\n'):
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
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
            opts += '-p '
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
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        r = requests.head(url, headers=header)
        try:
            if "text/plain" in r.headers["content-type"] or "application/octet-stream" in r.headers["content-type"] and int(r.headers["content-length"]) < 1000000:
                path = os.path.dirname(os.path.abspath(__file__))
                filepath = "{0}/tmp".format(path)
                filename = "{0}/{1}".format(filepath, url.split('/')[-1])
                r = requests.get(url, timeout=10, headers=header)
                open(filename, 'wb').write(r.content.replace(b';5;', b';'))
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
            elif not line.strip() and not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply('\xa0', prefixNick = False, noLengthCheck=True, private=False, notice=False, to=channel)
            else:
                return
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
    a2m = wrap(a2m, [optional('channel'), getopts({'l':'int', 'r':'int', 't':'int', 'w':'int', 'p':'', 'delay':'float'}), ('text')])

    def p2u(self, irc, msg, args, channel, optlist, url):
        """[<channel>] [--b] [--f] [--p] [--s] [--t] [--w] [--delay] <url>
        Picture to Unicode. https://git.trollforge.org/p2u/about/
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        image_formats = ("image/png", "image/jpeg", "image/jpg", "image/gif")
        r = requests.head(url, headers=header)
        if r.headers["content-type"] in image_formats:
            response = requests.get(url, timeout=10, headers=header)
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
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        Text to toilet figlets. -f to select font. -F to select filters. Separate multiple filters with a comma.
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        IRC art weather report from wttr.in for <location>.
        --16 for 16 colors (default).
        --99 for 99 colors.
        Get moon phase with 'wttr moon'.
        <location>?u (use imperial units).
        <location>?m (metric).
        <location>?<1-3> (number of days)
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        file = requests.get("http://wttr.in/{0}".format(location), timeout=10)
        output = file.content.decode()
        output = self.ansi2irc(output)
        output = re.sub('⚡', '☇ ', output)
        output = re.sub('‘‘', '‘ ', output)
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output.splitlines():
            line = line.strip('\x0F')
            if not line.strip():
                line = '\xa0'
            if self.registryValue('pasteEnable', msg.args[0]) and not line.startswith("Follow"):
                paste += line + "\n"
            if line.strip() and not self.stopped[msg.args[0]] and not line.startswith("Follow"):
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
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
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
        file = requests.get("http://{0}.rate.sx/{1}".format(sub, coin), timeout=10)
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
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if 'type' in optlist:
            type = optlist.get('type')
        else:
            type = 'default'
        data = requests.get("https://easyapis.soue.tk/api/cowsay?text={0}&type={1}".format(text, type), tiemout=10)
        self.stopped[msg.args[0]] = False
        paste = ''
        for line in data.content.decode().splitlines():
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
        Returns random art fortune from http://www.asciiartfarts.com/fortune.txt
        """
        if not channel:
            channel = msg.args[0]
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        self.stopped[msg.args[0]] = False
        data = requests.get("http://www.asciiartfarts.com/fortune.txt", timeout=10)
        fortunes = data.content.decode().split('%\n')
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
        if channel != msg.args[0] and not ircdb.checkCapability(msg.prefix, 'admin'):
            irc.errorNoCapability('admin')
            return
        optlist = dict(optlist)
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        self.stopped[msg.args[0]] = False
        ua = UserAgent(fallback="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:74.0) Gecko/20100101 Firefox/74.0")
        header = {'User-Agent':str(ua.random)}
        data = requests.get("https://mircart.org/?s={0}".format(search), headers=header, timeout=10)
        soup = BeautifulSoup(data.content)
        url = soup.find(href=re.compile(".txt"))
        data = requests.get(url.get('href'), headers=header, timeout=10)
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
            irc.reply("Stopping.")
        self.stopped[msg.args[0]] = True
    cq = wrap(cq)

    def codes(self, irc, msg, args):
        """
        Show a grid of IRC color codes.
        """
        irc.reply("\x031,0000\x031,0101\x031,0202\x031,0303\x031,0404\x031,0505\x031,0606\x031,0707\x031,0808\x031,0909\x031,1010\x031,1111\x031,1212\x031,1313\x031,1414\x031,1515", prefixNick=False)
        irc.reply("\x031,1616\x031,1717\x031,1818\x031,1919\x031,2020\x031,2121\x031,2222\x031,2323\x031,2424\x031,2525\x031,2626\x031,2727", prefixNick=False)
        irc.reply("\x031,2828\x031,2929\x031,3030\x031,3131\x031,3232\x031,3333\x031,3434\x031,3535\x031,3636\x031,3737\x031,3838\x031,3939", prefixNick=False)
        irc.reply("\x031,4040\x031,4141\x031,4242\x031,4343\x031,4444\x031,4545\x031,4646\x031,4747\x031,4848\x031,4949\x031,5050\x031,5151", prefixNick=False)
        irc.reply("\x031,5252\x031,5353\x031,5454\x031,5555\x031,5656\x031,5757\x031,5858\x031,5959\x031,6060\x031,6161\x031,6262\x031,6363", prefixNick=False)
        irc.reply("\x031,6464\x031,6565\x031,6666\x031,6767\x031,6868\x031,6969\x031,7070\x031,7171\x031,7272\x031,7373\x031,7474\x031,7575", prefixNick=False)
        irc.reply("\x031,7676\x031,7777\x031,7878\x031,7979\x031,8080\x031,8181\x031,8282\x031,8383\x031,8484\x031,8585\x031,8686\x031,8787", prefixNick=False)
        irc.reply("\x031,8888\x031,8989\x031,9090\x031,9191\x031,9292\x031,9393\x031,9494\x031,9595\x031,9696\x031,9797\x031,9898\x031,9999", prefixNick=False)
    codes = wrap(codes)

Class = TextArt
