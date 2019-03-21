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
from PIL import Image, ImageFilter
import numpy as np
import sys, math
from fake_useragent import UserAgent

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

    def getAverageL(self, image):
        """
        Given PIL Image, return average value of grayscale value
        """
        # get image as numpy array
        im = np.array(image)
        # get shape
        w,h = im.shape
        # get average
        return np.average(im.reshape(w*h))

    def getAverageC(self, pixel):
        """
        Given PIL Image, return average RGB value
        """
        pixel = pixel[:3]
        colors = {
            "16":(71,0,0),
            "17":(71,33,0),
            "18":(71,71,0),
            "19":(50,71,0),
            "20":(0,71,0),
            "21":(0,71,44),
            "22":(0,71,71),
            "23":(0,39,71),
            "24":(0,0,71),
            "25":(46,0,71),
            "26":(71,0,71),
            "27":(71,0,42),
            "28":(116,0,0),
            "29":(116,58,0),
            "30":(116,116,0),
            "31":(81,116,0),
            "32":(0,116,0),
            "33":(0,116,73),
            "34":(0,116,116),
            "35":(0,64,116),
            "36":(0,0,116),
            "37":(75,0,116),
            "38":(116,0,116),
            "39":(116,0,69),
            "40":(181,0,0),
            "41":(181,99,0),
            "42":(181,181,0),
            "43":(125,181,0),
            "44":(0,181,0),
            "45":(0,181,113),
            "46":(0,181,181),
            "47":(0,99,181),
            "48":(0,0,181),
            "49":(117,0,181),
            "50":(181,0,181),
            "51":(181,0,107),
            "52":(255,0,0),
            "53":(255,140,0),
            "54":(255,255,0),
            "55":(178,255,0),
            "56":(0,255,0),
            "57":(0,255,160),
            "58":(0,255,255),
            "59":(0,140,255),
            "60":(0,0,255),
            "61":(165,0,255),
            "62":(255,0,255),
            "63":(255,0,152),
            "64":(255,89,89),
            "65":(255,180,89),
            "66":(255,255,113),
            "67":(207,255,96),
            "68":(111,255,111),
            "69":(101,255,201),
            "70":(109,255,255),
            "71":(89,180,255),
            "72":(89,89,255),
            "73":(196,89,255),
            "74":(255,102,255),
            "75":(255,89,188),
            "76":(255,156,156),
            "77":(255,211,156),
            "78":(255,255,156),
            "79":(226,255,156),
            "80":(156,255,156),
            "81":(156,255,219),
            "82":(156,255,255),
            "83":(156,211,255),
            "84":(156,156,255),
            "85":(220,156,255),
            "86":(255,156,255),
            "87":(255,148,211),
            "88":(0,0,0),
            "89":(19,19,19),
            "90":(40,40,40),
            "91":(54,54,54),
            "92":(77,77,77),
            "93":(101,101,101),
            "94":(129,129,129),
            "95":(159,159,159),
            "96":(188,188,188),
            "97":(226,226,226),
            "98":(255,255,255)}
        manhattan = lambda x,y : abs(x[0] - y[0]) + abs(x[1] - y[1]) + abs(x[2] - y[2]) 
        distances = {k: manhattan(v, pixel) for k, v in colors.items()}
        color = min(distances, key=distances.get)
        return color


    def img(self, irc, msg, args, url):
        """
        Image to ANSI Art
        """
        path = os.path.dirname(os.path.abspath(__file__))
        filepath = "{0}/tmp".format(path)
        filename = "{0}/{1}".format(filepath, url.split('/')[-1])
        ua = UserAgent()
        header = {'User-Agent':str(ua.random)}
        response = requests.get(url, headers=header)
        if response.status_code == 200:
            with open("{0}".format(filename), 'wb') as f:
                f.write(response.content)
        gscale = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        # open image and convert to grayscale
        image = Image.open(filename).convert('L')
        image2 = Image.open(filename)
        os.remove(filename)
        # store dimensions
        W, H = image.size[0], image.size[1]
        # compute width of tile
        cols = 80
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
        if image2.mode != 'RGBA':
            image2 = image2.convert('RGBA')
        image2 = image2.resize((cols, rows), Image.LANCZOS)
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
            for i in range(cols):
                # crop image to tile
                x1 = int(i*w)
                x2 = int((i+1)*w)
                # correct last tile
                if i == cols-1:
                    x2 = W
                # crop image to extract tile
                img = image.crop((x1, y1, x2, y2))
                img2 = image2.crop((x1, y1, x2, y2))
                # get average luminance
                avg = int(self.getAverageL(img))
                # look up ascii char
                gsval = gscale[int((avg*69)/255)]
                # get color value
                color = self.getAverageC(colormap[j][i].tolist())
                # append ascii char to string
                aimg[j] += "\x03{0}{1}".format(color, gsval)
        # return txt image
        output = aimg
        for line in output:
            irc.reply(line, prefixNick=False)
    img = wrap(img, ['text'])


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
        file = requests.get(url)
        if "html" in file.text or not url.endswith(".txt"):
            irc.reply("Error: Scroll requires a text file as input.")
        else:
            for line in file.text.splitlines():
                if line.strip():
                    irc.reply(line, prefixNick = False)
    scroll = wrap(scroll, ['text'])

Class = ASCII

