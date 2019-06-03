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
from PIL import Image, ImageOps, ImageFont, ImageDraw
import numpy as np
import sys, math
from fake_useragent import UserAgent
from colour.difference import *
import re
import pexpect
import time
import random as random
from x256 import x256
import pyimgur

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
        self.colors = 83
        self.stopped = {}
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
        self.ircColors= {
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
        defaultFont = "{0}/DejaVuSansMono.ttf".format(path)
        def strip_colors(string):
            return self.strip_colors_regex('', string)
        _colorRegex = re.compile('(([0-9]{1,2})(,([0-9]{1,2}))?)')
        IGNORE_CHRS = ('\x16','\x1f','\x02', '\x03', '\x0f')
        lineLens = [len(line) for line in strip_colors(text).splitlines()]
        maxWidth, height = max(lineLens), len(lineLens)
        font = ImageFont.truetype(defaultFont, size)
        fontX, fontY = font.getsize(' ')
        fontX -= 1
        fontY += 3
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
            colors = list(self.ircColors.keys())[:16]
        else:
            colors = list(self.ircColors.keys())
        if pixel not in self.matches:
            closest_colors = sorted(colors, key=lambda color: self.distance(color, self.rgb2lab(pixel), speed))
            closest_color = closest_colors[0]
            self.matches[pixel] = self.ircColors[closest_color]
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

    def distance(self, c1, c2, speed):
        if speed == 'faster':
            (r1,g1,b1) = (c1[0], c1[1], c1[2])
            (r2,g2,b2) = (c2[0], c2[1], c2[2])
            delta_e =  math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)
        elif speed == 'fast':
            delta_e = delta_E_CIE1976(c1, c2)
        elif speed == 'slow':
            delta_e = delta_E_CIE1994(c1, c2)
        elif speed == 'slower':
            delta_e = delta_E_CMC(c1, c2)
        elif speed == 'slowest':
            delta_e = delta_E_CIE2000(c1, c2)
        elif speed == 'insane':
            delta_e = delta_E_DIN99(c1, c2)
        return delta_e

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
        file = file.content.decode()
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
        """[<channel>] [--w <int>] [--16] [--ascii] [--block] [--1/4] [--chars <text>] [--ramp <text>] [--bg <0-98>] [--fg <0-99>] [--nocolor] [--invert] <url>
        Image to ASCII Art.
        --w num columns wide.
        --16 for 16 colors.
        --ascii for color ascii.
        --block for space blcck.
        --1/4 for 1/4 block
        --chars <TEXT> color text.
        --ramp <TEXT> set ramp (".:-=+*#%@").
        --bg <0-98> set bg.
        --fg <0-99> set fg.
        --nocolor text only greyscale.
        --invert inverts ramp.
        """
        if not channel:
            channel = msg.args[0]
        optlist = dict(optlist)
        gscale = ""
        if '16' in optlist:
            self.colors = 16
        else:
            self.colors = 93
        if 'faster' in optlist:
            speed = 'faster'
        elif 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        elif 'slower' in optlist:
            speed = 'slower'
        elif 'slowest' in optlist:
            speed = 'slowest'
        elif 'insane' in optlist:
            speed = 'insane'
        else:
            speed = 'slowest'
        if 'chars' in optlist:
            gscale = optlist.get('chars')
        elif 'ramp' in optlist:
            gscale = optlist.get('ramp')
        if 'delay' in optlist:
            delay = optlist.get('delay')
        else:
            delay = self.registryValue('delay', msg.args[0])
        if 'bg' in optlist:
            bg = optlist.get('bg')
        else:
            bg = 1
        if 'fg' in optlist:
            fg = optlist.get('fg')
        else:
            fg = 99
        if 'ascii' in optlist and bg == 0 or bg == 98:
            gscale = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:\"^`'."
        elif 'ascii' in optlist:
            gscale = ".'`^\":;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
        if 'nocolor' in optlist and 'chars' in optlist:
            return
        elif 'nocolor' in optlist and 'ramp' not in optlist and bg == 0 or bg == 98:
            gscale = "@%#*+=-:. "
        elif 'nocolor' in optlist and 'ramp' not in optlist:
            gscale = " .:-=+*#%@"
        if not gscale.strip() or 'block' in optlist:
            gscale = '\xa0'
        if 'invert' in optlist and 'chars' not in optlist and gscale != '\xa0':
            gscale = gscale[::-1]
        if 'w' in optlist:
            cols = optlist.get('w')
        elif 'ascii' not in optlist and 'ramp' not in optlist and 'nocolor' not in optlist and 'chars' not in optlist and 'block' not in optlist and 'w' not in optlist:
            cols = 70
        elif 'w' not in optlist and '1/4' in optlist:
            cols = 70
        else:
            cols = 100
        if '1/4' in optlist:
            cols = cols *2
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
        if 'ascii' not in optlist and 'ramp' not in optlist and 'nocolor' not in optlist and 'chars' not in optlist and 'block' not in optlist and '1/4' not in optlist:
            scale = 1.0
        else:
            scale = 0.5
        h = w/scale
        # compute number of rows
        rows = int(H/h)
        image = ImageOps.autocontrast(image)
        image = image.resize((cols, rows), Image.LANCZOS)
        if 'nocolor' not in optlist:
            if 'dither' in optlist:
                image2 = image.convert('P', dither=Image.FLOYDSTEINBERG, palette=Image.ADAPTIVE)
            else:
                image2 = image.convert('P', dither=None, palette=Image.ADAPTIVE)
            image2 = image2.convert('RGB')
            colormap = np.array(image2)
            self.matches = {}
        image = image.convert('L')
        lumamap = np.array(image)
        # ascii image is a list of character strings
        aimg = []
        # generate list of dimensions
        char = 0
        if 'ascii' not in optlist and 'ramp' not in optlist and 'nocolor' not in optlist and 'chars' not in optlist and 'block' not in optlist and '1/4' not in optlist:
            k = 0
            for j in range(0, rows - 1, 2):
                # append an empty string
                aimg.append("")
                old_color = "99,99"
                for i in range(cols):
                    color1 = '%02d' % self.getColor(colormap[j][i].tolist(), speed)
                    color2 = '%02d' % self.getColor(colormap[j+1][i].tolist(), speed)
                    color = "{0},{1}".format(color1, color2)
                    if color != old_color:
                        if color1 == color2:
                            gsval = " "
                            color = "0,{0}".format(color1)
                        else:
                            gsval = "▀"
                            alt_gsval = "▄"
                        if gsval != " " and color == "{0},{1}".format(old_color.split(',')[1], old_color.split(',')[0]):
                            aimg[k] += alt_gsval
                        elif gsval == " " and "{0}".format(color1) == "{0}".format(old_color.split(',')[1]):
                            aimg[k] += " "
                        elif 'max' in optlist and gsval == " " and "{0}".format(color1) == "{0}".format(old_color.split(',')[0]):
                            aimg[k] += "█"
                        else:
                            aimg[k] += "\x03{0}{1}".format(color, gsval)
                            old_color = color
                    else:
                        if color1 == color2:
                            aimg[k] += " "
                        else:
                            aimg[k] += "▀"
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = re.sub("\x030,{0}(\s+)\x03(\d\d),{0}".format(i), "\x03\g<2>,{0}\g<1>".format(i), aimg[k])
                for i in range(0,98):
                    i = '%02d' % i
                    aimg[k] = aimg[k].replace("{0}".format(i), "{0}".format(int(i)))
                k += 1
        elif '1/4' in optlist:
            k = 0
            for j in range(0, rows - 1, 2):
                # append an empty string
                aimg.append("")
                old_color = None
                for i in range(0, cols - 1, 2):
                    color1 = self.getColor(colormap[j][i].tolist(), speed)
                    color2 = self.getColor(colormap[j+1][i].tolist(), speed)
                    color3= self.getColor(colormap[j][i+1].tolist(), speed)
                    color4 = self.getColor(colormap[j+1][i+1].tolist(), speed)
                    if color1 == color2 and color1 == color3 and color1 == color4:
                        gsval = " "
                        color = "\x030,{0}".format(int(color1))
                    elif color1 == color4 and color2 == color3:
                        gsval = "▚"
                        color = "\x03{0},{1}".format(int(color1), int(color2))
                    elif color1 == color2 and color1 == color3 and color1 != color4:
                        gsval = "▛"
                        color = "\x03{0},{1}".format(int(color1), int(color4))
                    elif color3 == color4 and color2 == color4 and color3 != color1:
                        gsval = "▟"
                        color = "\x03{0},{1}".format(int(color2), int(color1))
                    elif color1 == color2 and color1 == color4 and color1 != color3:
                        gsval = "▙"
                        color = "\x03{0},{1}".format(int(color1), int(color3))
                    elif color1 == color3 and color1 == color4 and color1 != color2:
                        gsval = "▜"
                        color = "\x03{0},{1}".format(int(color1), int(color2))
                    elif color1 == color3 and color2 == color4 and color1 != color2 and color3 != color4:
                        gsval = "▀"
                        color = "\x03{0},{1}".format(int(color1), int(color4))
                    elif color1 == color2 and color3 == color4 and color1 != color3 and color2 != color4:
                        gsval = "▌"
                        color = "\x03{0},{1}".format(int(color1), int(color4))
                    else:
                        row1 = self.getColor(np.average([tuple(colormap[j][i].tolist()), tuple(colormap[j][i+1].tolist())], axis=0).tolist(), speed)
                        row2 = self.getColor(np.average([tuple(colormap[j+1][i+1].tolist()), tuple(colormap[j][i+1].tolist())], axis=0).tolist(), speed)
                        if row2 == color1:
                            gsval = "▙"
                            color = "\x03{0},{1}".format(int(row2), int(color3))
                        elif row1 == color2:
                            gsval = "▛"
                            color = "\x03{0},{1}".format(int(row1), int(color4))
                        elif row2 == color3:
                            gsval = "▟"
                            color = "\x03{0},{1}".format(int(row2), int(color1))
                        elif row1 == color4:
                            gsval = "▜"
                            color = "\x03{0},{1}".format(int(row1), int(color2))
                        elif row1 != row2:
                            gsval = "▀"
                            color = "\x03{0},{1}".format(int(row1), int(row2))
                        elif row1 == row2:
                            gsval = " "
                            color = "\x030,{0}".format(int(row1))
                        else:
                            col1 = self.getColor(np.average([tuple(colormap[j][i].tolist()), tuple(colormap[j+1][i].tolist())], axis=0).tolist(), speed)
                            col2 = self.getColor(np.average([tuple(colormap[j][i+1].tolist()), tuple(colormap[j+1][i+1].tolist())], axis=0).tolist(), speed)
                            if col1 == color4:
                                gsval = "▙"
                                color = "\x03{0},{1}".format(int(col1), int(color3))
                            elif col1 == color3:
                                gsval = "▛"
                                color = "\x03{0},{1}".format(int(col1), int(color4))
                            elif col2 == color2:
                                gsval = "▟"
                                color = "\x03{0},{1}".format(int(col2), int(color1))
                            elif col2 == color1:
                                gsval = "▜"
                                color = "\x03{0},{1}".format(int(col2), int(color2))
                            elif col1 != col2:
                                gsval = "▌"
                                color = "\x03{0},{1}".format(int(col1), int(col2))
                            elif col1 == col2:
                                gsval = " "
                                color = "\x030,{0}".format(int(col1))
                    if color != old_color:
                        old_color = color
                        # append char to string
                        aimg[k] += "{0}{1}".format(color, gsval)
                    else:
                        aimg[k] += "{0}".format(gsval)
                k += 1
        else:
            for j in range(rows):
                # append an empty string
                aimg.append("")
                old_color = None
                for i in range(cols):
                    # get average luminance
                    avg = int(np.average(lumamap[j][i]))
                    # look up ascii char
                    if 'chars' not in optlist:
                        gsval = gscale[int((avg * (len(gscale) - 1))/255)]
                    else:
                        if char < len(gscale):
                            gsval = gscale[char]
                            char += 1
                        else:
                            char = 0
                            gsval = gscale[char]
                            char += 1
                    # get color value
                    if 'nocolor' not in optlist and i == 0:
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
                    elif 'nocolor' not in optlist and gsval != ' ':
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
        del image
        try:
            del image2
            del colormap
        except:
            pass
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output:
            if 'nocolor' in optlist and 'fg' in optlist and 'bg' in optlist:
                newbg = "{:02d}".format(int(bg))
                line = "\x03{0},{1}{2}".format(int(fg), newbg, line)
            elif 'nocolor' in optlist and 'fg' in optlist:
                newfg = "{:02d}".format(int(fg))
                line = "\x03{0}{1}".format(newfg, line)
            elif 'nocolor' in optlist and 'bg' in optlist:
                newbg = "{:02d}".format(int(bg))
                line = "\x0399,{0}{1}".format(newbg, line)
            if self.registryValue('pasteEnable', msg.args[0]):
                paste += line + "\n"
            if not self.stopped[msg.args[0]]:
                time.sleep(delay)
                irc.reply(line, prefixNick=False, noLengthCheck=True, private=False, notice=False, to=channel)
        if self.registryValue('pasteEnable', msg.args[0]):
            irc.reply(self.doPaste(url, paste), private=False, notice=False, to=channel)
    img = wrap(img,[optional('channel'), getopts({'w':'int', 'invert':'', 'fast':'', 'faster':'', 'slow':'', 'slower':'', 'slowest':'', 'insane':'', '16':'', 'delay':'float', 'dither':'', 'chars':'text', 'bg':'int', 'fg':'int', 'ramp':'text', 'nocolor':'', 'block':'', 'ascii':'', '1/4':'', 'max':''}), ('text')])

    def scroll(self, irc, msg, args, channel, optlist, url):
        """[<channel>] <url>
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
        """[<channel>] [--l] [--r] [--n] [--p] [--t] [--w] [--delay] <url>
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
        for line in output.splitlines():
            line = line.decode()
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
            opts += '-w 70 '
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
        """[<channel>] [--f] [--j] [--w] [--e] [--r] [--delay] <text>
        Text to Figlet. Uses tdfiglet: https://github.com/tat3r/tdfiglet. Fonts: http://www.roysac.com/thedrawfonts-tdf.html
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
        try:
            output = pexpect.run('tdfiglet -c m {0} {1}'.format(opts.strip(), text))
            try:
                os.remove(filename)
            except:
                pass
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
    tdf = wrap(tdf, [optional('channel'), getopts({'f':'text', 'j':'text', 'w':'int', 'e':'text', 'r':'', 'delay':'float'}), ('text')])

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
            self.colors = 93
        else:
            self.colors = 16
        if 'faster' in optlist:
            speed = 'faster'
        elif 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        elif 'slower' in optlist:
            speed = 'slower'
        elif 'slowest' in optlist:
            speed = 'slowest'
        elif 'insane' in optlist:
            speed = 'insane'
        else:
            speed = 'slower'
        self.matches = {}
        file = requests.get("http://wttr.in/{0}".format(location))
        output = file.content.decode()
        for i in range(0, 256):
            j = '%03d' % i
            output = re.sub('\x1b\[38;5;{0}m|\[38;5;{0};\d+m'.format(j), '\x03{:02d}'.format(self.getColor(x256.to_rgb(int(j)), speed)), output)
            output = re.sub('\x1b\[38;5;{0}m|\[38;5;{0};\d+m'.format(i), '\x03{:02d}'.format(self.getColor(x256.to_rgb(int(i)), speed)), output)
        output = output.replace('\x1b[0m', '\x0F')
        output = re.sub('\x1b|\x9b|\[\d+m', '', output)
        output = re.sub('\x0F(\s*)\x03', '\g<1>\x03', output)
        for i in range(0, 99):
            if i < 17:
                i = '%02d' % i
            output = re.sub('(?<=\x03{0}.)\x03{0}'.format(i), '', output)
        paste = ""
        self.stopped[msg.args[0]] = False
        for line in output.splitlines():
            line = line.strip('\x0F')
            line = line.replace('⚡', '☇☇')
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
    wttr = wrap(wttr, [optional('channel'), getopts({'delay':'float', '16':'', '99':'', 'fast':'', 'faster':'', 'slow':'', 'slower':'', 'slowest':'', 'insane':''}), ('text')])

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
            self.colors = 93
        else:
            self.colors = 16
        if 'faster' in optlist:
            speed = 'faster'
        elif 'fast' in optlist:
            speed = 'fast'
        elif 'slow' in optlist:
            speed = 'slow'
        elif 'slower' in optlist:
            speed = 'slower'
        elif 'slowest' in optlist:
            speed = 'slowest'
        elif 'insane' in optlist:
            speed = 'insane'
        else:
            speed = 'slower'
        if 'sub' in optlist:
            sub = optlist.get('sub')
        else:
            sub = 'usd'
        if not coin:
            coin = ''
        self.matches = {}
        file = requests.get("http://{0}.rate.sx/{1}".format(sub, coin))
        output = file.content.decode()
        output = output.replace('\x1b[0m', '\x0F')
        output = output.replace('\x1b[2m', '')
        output = output.replace('\x1b[47m\x1b[30m', '\x031,0')
        output = output.replace('\x1b[30m', '\x0301')
        output = output.replace('\x1b[31m', '\x0304')
        output = output.replace('\x1b[32m', '\x0309')
        output = output.replace('\x1b[33m', '\x0308')
        output = output.replace('\x1b[34m', '\x0312')
        output = output.replace('\x1b[35m', '\x0306')
        output = output.replace('\x1b[36m', '\x0311')
        output = output.replace('\x1b[37m', '\x0300')
        output = re.sub('\x0F(\s*)\x03', '\g<1>\x03', output)
        output = re.sub('\x03\d\d(\s*)\x03', '\g<1>\x03', output)
        if coin.strip():
            output = output.replace('\x1b(B\x1b[m', '')
            for i in range(0,99):
                i = '%02d' % i
                output = re.sub('\x1b\[38;5;{0}m'.format(i), '\x03{:02d}'.format(self.getColor(x256.to_rgb(int(i)), speed)), output)
            for i in range(100,255):
                output = re.sub('\x1b\[38;5;{0}m'.format(i), '\x03{:02d}'.format(self.getColor(x256.to_rgb(int(i)), speed)), output)
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
    rate = wrap(rate, [optional('channel'), getopts({'delay':'float', '16':'', '99':'', 'sub':'text', 'fast':'', 'faster':'', 'slow':'', 'slower':'', 'slowest':'', 'insane':''}), optional('text')])

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

    def cq(self, irc, msg, args):
        """
        Stop the scroll.
        """
        if not self.stopped[msg.args[0]]:
            self.stopped[msg.args[0]] = True
            irc.reply("Stopping.")
    cq = wrap(cq)

Class = ASCII
