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
import urllib
import requests
from PIL import Image, ImageEnhance
import numpy as np
import sys, math
from colormath.color_objects import LabColor, sRGBColor
from colormath.color_conversions import convert_color

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

    def distance(self, c1, c2):
        rgb1 = sRGBColor(c1[0], c1[1], c1[2])
        rgb2 = sRGBColor(c2[0], c2[1], c2[2])
        lab1 = convert_color(rgb1, LabColor)
        lab2 = convert_color(rgb2, LabColor)
        (r1,g1,b1) = lab1.lab_l, lab1.lab_a, lab1.lab_b
        (r2,g2,b2) = lab2.lab_l, lab2.lab_a, lab2.lab_b
        return math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)

    def load_and_resize_image(self, imgname):
        aspectRatio = 1.0
        maxLen = 55.0 # default maxlen: 100px
        img = Image.open(imgname)
        # force image to RGBA - deals with palettized images (e.g. gif) etc.
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        # need to change the size of the image?
        if maxLen is not None or aspectRatio != 1.0:
            native_width, native_height = img.size
            new_width = native_width
            new_height = native_height
            # First apply aspect ratio change (if any) - just need to adjust one axis
            # so we'll do the height.
            if aspectRatio != 1.0:
                new_height = int(float(aspectRatio) * new_height)
            # Now isotropically resize up or down (preserving aspect ratio) such that
            # longer side of image is maxLen
            if maxLen is not None:
                rate = float(maxLen) / max(new_width, new_height)
                new_width = int(rate * new_width)
                new_height = int(rate * new_height)
            if native_width != new_width or native_height != new_height:
                img = img.resize((new_width, new_height), Image.NEAREST)
        return img

    def img(self, irc, msg, args, url):
        """
        Image to ASCII Art
        """
        path = os.path.dirname(os.path.abspath(__file__))
        filepath = "{0}/tmp".format(path)
        filename = "{0}/{1}".format(filepath, url.split('/')[-1])
        urllib.request.urlretrieve(url, filename)
        img = self.load_and_resize_image(filename)
        arr = np.array(np.asarray(img).astype('float'))
        ircColors = {(211, 215, 207): 0,
             (46, 52, 54): 1,
             (52, 101, 164): 2,
             (78, 154, 6): 3,
             (204, 0, 0): 4,
             (143, 57, 2): 5,
             (92, 53, 102): 6,
             (206, 92, 0): 7,
             (196, 160, 0): 8,
             (115, 210, 22): 9,
             (17, 168, 121): 10,
             (88, 161, 157): 11,
             (87, 121, 158): 12,
             (160, 67, 101): 13,
             (85, 87, 83): 14,
             (136, 137, 133): 15}
        colors = list(ircColors.keys())
        for line in arr:
            row = ""
            for pixel in line:
                if pixel[3] == 0:
                    row += "\003  " # \003 to close any potential open color tag
                else:
                    closest_colors = sorted(colors, key=lambda color: self.distance(color, pixel))
                    closest_color = closest_colors[0]
                    row += "\003{0},{0}  ".format(ircColors[closest_color])
            irc.reply(row, prefixNick=False)
        os.remove(filename)
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
