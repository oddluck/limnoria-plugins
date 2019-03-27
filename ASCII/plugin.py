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
from PIL import Image, ImageOps
import numpy as np
import sys, math
from fake_useragent import UserAgent
from colour.difference import *
import re

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
        self.ircColors= {
            (71,0,0):16,
            (71,33,0):17,
            (71,71,0):18,
            (50,71,0):19,
            (0,71,0):20,
            (0,71,44):21,
            (0,71,71):22,
            (0,39,71):23,
            (0,0,71):24,
            (46,0,71):25,
            (71,0,71):26,
            (71,0,42):27,
            (116,0,0):28,
            (116,58,0):29,
            (116,116,0):30,
            (81,116,0):31,
            (0,116,0):32,
            (0,116,73):33,
            (0,116,116):34,
            (0,64,116):35,
            (0,0,116):36,
            (75,0,116):37,
            (116,0,116):38,
            (116,0,69):39,
            (181,0,0):40,
            (181,99,0):41,
            (181,181,0):42,
            (125,181,0):43,
            (0,181,0):44,
            (0,181,113):45,
            (0,181,181):46,
            (0,99,181):47,
            (0,0,181):48,
            (117,0,181):49,
            (181,0,181):50,
            (181,0,107):51,
            (255,0,0):52,
            (255,140,0):53,
            (255,255,0):54,
            (178,255,0):55,
            (0,255,0):56,
            (0,255,160):57,
            (0,255,255):58,
            (0,140,255):59,
            (0,0,255):60,
            (165,0,255):61,
            (255,0,255):62,
            (255,0,152):63,
            (255,89,89):64,
            (255,180,89):65,
            (255,255,113):66,
            (207,255,96):67,
            (111,255,111):68,
            (101,255,201):69,
            (109,255,255):70,
            (89,180,255):71,
            (89,89,255):72,
            (196,89,255):73,
            (255,102,255):74,
            (255,89,188):75,
            (255,156,156):76,
            (255,211,156):77,
            (255,255,156):78,
            (226,255,156):79,
            (156,255,156):80,
            (156,255,219):81,
            (156,255,255):82,
            (156,211,255):83,
            (156,156,255):84,
            (220,156,255):85,
            (255,156,255):86,
            (255,148,211):87,
            (0,0,0):88,
            (19,19,19):89,
            (40,40,40):90,
            (54,54,54):91,
            (77,77,77):92,
            (101,101,101):93,
            (129,129,129):94,
            (159,159,159):95,
            (188,188,188):96,
            (226,226,226):97,
            (255,255,255):98}

    def ascii(self, irc, msg, args, optlist, text):
        """[--font <font>] [--color <color1,color2>] [<text>]
        Text to ASCII art
        """
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
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False)
             else:
                 data = requests.get("https://artii.herokuapp.com/make?text={0}&font={1}".format(text, font))
                 for line in data.text.splitlines():
                     if line.strip():
                         irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False)
        elif 'font' not in optlist:
            if words:
                 for word in words:
                     if word.strip():
                         data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(word.strip()))
                         for line in data.text.splitlines():
                             if line.strip():
                                 irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False)
            else:
                data = requests.get("https://artii.herokuapp.com/make?text={0}&font=univers".format(text))
                for line in data.text.splitlines():
                    if line.strip():
                        irc.reply(ircutils.mircColor(line, color1, color2), prefixNick=False)

    ascii = wrap(ascii, [getopts({'font':'text', 'color':'text'}), ('text')])

    def getAverageC(self, pixel, speed):
        """
        Given PIL Image, return average RGB value
        """
        speed = speed
        colors = list(self.ircColors.keys())
        closest_colors = sorted(colors, key=lambda color: self.distance(self.rgb2lab(color), self.rgb2lab(pixel), speed))
        closest_color = closest_colors[0]
        return self.ircColors[closest_color]

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
        if speed == 'fast':
            delta_e = delta_E_CIE1976(c1, c2)
        elif speed == 'medium':
            delta_e = delta_E_CMC(c1, c2)
        else:
            delta_e = delta_E_CIE2000(c1, c2)
        return delta_e

    def img(self, irc, msg, args, optlist, url):
        """[--cols <number of columns>] [--invert] (<url>)
        Image to Color ASCII Art. --cols to set number of columns wide. --invert to invert the greyscale. 
        """
        optlist = dict(optlist)
        if 'slow' in optlist:
            speed = 'medium'
        elif 'insane' in optlist:
            speed = 'insane'
        else:
            speed = 'fast'
        if 'cols' in optlist:
            cols = optlist.get('cols')
        else:
            cols = 100
        if 'invert' in optlist:
            gscale = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'."
        else:
            gscale = ".'`^\",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
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
            irc.reply("Invalid file type.")
            return
        if response.status_code == 200:
            with open("{0}".format(filename), 'wb') as f:
                f.write(response.content)
        # open image and convert to grayscale
        image = Image.open(filename).convert('L')
        image2 = Image.open(filename)
        try:
            os.remove(filename)
        except:
            pass
        irc.reply("Please be patient while I render the image into ASCII characters and colorize the output.")
        # store dimensions
        W, H = image.size[0], image.size[1]
        # compute width of tile
        w = W/cols
        # compute tile height based on aspect ratio and scale
        scale = 0.5
        h = w/scale
        # compute number of rows
        rows = int(H/h)
        # check if image size is too small
        if cols > W or rows > H:
            print("Image too small for specified cols!")
            exit(0)
        image = ImageOps.autocontrast(image)
        image = image.resize((cols, rows), Image.LANCZOS)
        image2 = image2.convert('RGBA')
        image2 = image2.convert(mode="P", matrix=None, dither=Image.FLOYDSTEINBERG, palette=Image.ADAPTIVE)
        image2 = image2.convert('RGB')
        image2 = image2.resize((cols, rows), Image.LANCZOS)
        lumamap = np.array(image)
        colormap = np.array(image2)
        # ascii image is a list of character strings
        aimg = []
        # generate list of dimensions
        for j in range(rows):
            y1 = int(j*h)
            y2 = int((j+1)*h)
            # correct last tile
            if j == rows-1:
                y2 = H
            # append an empty string
            aimg.append("")
            old_color = None
            for i in range(cols):
                # get average luminance
                avg = int(np.average(lumamap[j][i]))
                # look up ascii char
                gsval = gscale[int((avg*68)/255)]
                # get color value
                color = self.getAverageC(colormap[j][i].tolist(),speed)
                #color = self.getAverageC(img2,speed)
                if color != old_color:
                    old_color = color
                    # append ascii char to string
                    aimg[j] += "\x03{0}{1}".format(color, gsval)
                else:
                    aimg[j] += "{0}".format(gsval)
        # return txt image
        output = aimg
        del image
        del image2
        del colormap
        for line in output:
            irc.reply(line, prefixNick=False, noLengthCheck=True)
    img = wrap(img,[getopts({'cols':'int', 'invert':'', 'slow':'', 'insane':''}), ('text')])

    def ansi(self, irc, msg, args, optlist, url):
        """[--cols <number of columns>] [--invert] <url>
        Converts image to ANSI art
        """
        optlist = dict(optlist)
        if 'slow' in optlist:
            speed = 'medium'
        elif 'insane' in optlist:
            speed = 'insane'
        else:
            speed = 'fast'
        if 'cols' in optlist:
            cols = optlist.get('cols')
        else:
            cols = 80
        if 'invert' in optlist:
            gscale = "█▓▒░"
        else:
            gscale = "░▒▓█"
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
            irc.reply("Invalid file type.")
            return
        if response.status_code == 200:
            with open("{0}".format(filename), 'wb') as f:
                f.write(response.content)
        # open image and convert to grayscale
        image = Image.open(filename).convert('L')
        image2 = Image.open(filename)
        try:
            os.remove(filename)
        except:
            pass
        irc.reply("Please be patient while I render the image into ASCII characters and colorize the output.")
        # store dimensions
        W, H = image.size[0], image.size[1]
        # compute width of tile
        w = W/cols
        # compute tile height based on aspect ratio and scale
        scale = 0.5
        h = w/scale
        # compute number of rows
        rows = int(H/h)
        # check if image size is too small
        if cols > W or rows > H:
            print("Image too small for specified cols!")
            exit(0)
        image = ImageOps.autocontrast(image)
        image = image.resize((cols, rows), Image.LANCZOS)
        image2 = image2.convert('RGBA')
        image2 = image2.convert(mode="P", matrix=None, dither=Image.FLOYDSTEINBERG, palette=Image.ADAPTIVE)
        image2 = image2.convert('RGB')
        image2 = image2.resize((cols, rows), Image.LANCZOS)
        lumamap = np.array(image)
        colormap = np.array(image2)
        # ascii image is a list of character strings
        aimg = []
        # generate list of dimensions
        for j in range(rows):
            y1 = int(j*h)
            y2 = int((j+1)*h)
            # correct last tile
            if j == rows-1:
                y2 = H
            # append an empty string
            aimg.append("")
            old_color = None
            for i in range(cols):
                # get average luminance
                avg = int(np.average(lumamap[j][i]))
                # look up ascii char
                gsval = gscale[int((avg*3)/255)]
                # get color value
                color = self.getAverageC(colormap[j][i].tolist(),speed)
                #color = self.getAverageC(img2,speed)
                if color != old_color:
                    old_color = color
                    # append ascii char to string
                    aimg[j] += "\x03{0}{1}".format(color, gsval)
                else:
                    aimg[j] += "{0}".format(gsval)
        # return txt image
        output = aimg
        del image
        del image2
        del colormap
        for line in output:
            irc.reply(line, prefixNick=False, noLengthCheck=True)
    ansi = wrap(ansi, [getopts({'cols':'int', 'invert':'', 'slow':'', 'insane':''}), ('text')])

    def fontlist(self, irc, msg, args):
        """
        get list of fonts for text-to-ascii-art
        """
        fontlist = requests.get("https://artii.herokuapp.com/fonts_list")
        response = sorted(fontlist.text.split('\n'))
        irc.reply(str(response).replace('\'', '').replace('[', '').replace(']', ''))
    fontlist = wrap(fontlist)

    def scroll(self, irc, msg, args, url):
        """
        Play ASCII/ANSI art files from web links
        """
        if url.startswith("https://paste.ee/p/"):
            url = re.sub("https://paste.ee/p/", "https://paste.ee/r/", url)
        file = requests.get(url)
        if "html" in file.text:
            irc.reply("Error: Scroll requires a text file as input.")
        elif url.endswith(".txt") or url.startswith("https://pastebin.com/raw/") or url.startswith("https://paste.ee/r/"):
            for line in file.text.splitlines():
                if line.strip():
                    irc.reply(line, prefixNick = False)
        else:
            irc.reply("Unexpected file type or link format")
    scroll = wrap(scroll, ['text'])

Class = ASCII
