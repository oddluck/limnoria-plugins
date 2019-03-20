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
from PIL import Image
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
        colors = {"white": (211, 215, 207),
            "black": (46, 52, 54),
            "blue":(52, 101, 164),
            "green":(78, 154, 6),
            "red":(204, 0, 0),
            "brown":(143, 57, 2),
            "purple":(92, 53, 102),
            "orange":(206, 92, 0),
            "yellow":(196, 160, 0),
            "light green":(115, 210, 22),
            "teal":(17, 168, 121),
            "light blue":(88, 161, 157),
            "dark blue":(87, 121, 158),
            "pink":(160, 67, 101),
            "dark grey":(85, 87, 83),
            "light grey":(136, 137, 133)}
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
        #image2 = image2.convert("P", dither=Image.FLOYDSTEINBERG, palette=Image.WEB)
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
                aimg[j] += ircutils.mircColor(gsval, color, None)
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

