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
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
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
        self.ircColors= {(1993.20515351498,2324.0983231476234,1950.0779087841693):16,
             (2302.159132332113,1476.5998328806731,2094.817440516089):17,
             (3267.109569734987,-625.5719921685046,2741.5824054551854):18,
             (3117.7906623358294,-1524.3182007475084,2563.4872768819705):19,
             (2994.225776415631,-2500.8929369695743,2413.738641368567):20,
             (3026.0461300232373,-2106.053265646869,1016.9116217498115):21,
             (3092.2778750318885,-1395.2984432353226,-410.2808083391245):22,
             (2082.37407522394,439.80707297830793,-1983.2971244240234):23,
             (1385.5715072995845,2298.009119093381,-3130.08523478244):24,
             (1761.7248957199076,2495.1524432892943,-2494.7963736847237):25,
             (2198.7916393341657,2850.6336820262986,-1765.3360075524952):26,
             (2055.801787008181,2491.6677227532045,-158.86279448684633):27,
             (2958.9498780747585,3441.1996261238046,2887.4025267278366):28,
             (3490.7754041570597,1995.586399321347,3144.023619818683):29,
             (4845.169302249827,-926.259480557718,4059.3516438937377):30,
             (4620.482019554244,-2281.747228870049,3791.325963678294):31,
             (4441.121161001645,-3702.9723544655367,3573.926467529447):32,
             (4489.963665823597,-3098.035370892731,1453.7194043799368):33,
             (4586.302989902044,-2065.9627148173527,-607.4864175067376):34,
             (3098.2589552331815,634.8559351078204,-2924.8401977939):35,
             (2059.250990402592,3402.5703829703853,-4634.592277094812):36,
             (2613.821127903904,3692.817296863682,-3697.953525308647):37,
             (3263.3535821224173,4220.81951658537,-2613.862567115958):38,
             (3052.7880497642973,3692.3353415279757,-255.20463970260963):39,
             (4230.166177007632,4911.647610760525,4121.209247509218):40,
             (5140.420692098141,2469.29414128601,4576.863521782283):41,
             (6922.379978784402,-1322.0564509214903,5793.940186325644):42,
             (6595.196756134379,-3301.6293161796852,5403.579861388848):43,
             (6345.679321104374,-5285.277604778105,5101.0895334333245):44,
             (6414.068737559316,-4437.401859025286,2114.577589536168):45,
             (6552.8983320653,-2948.7626219415083,-867.069491832234):46,
             (4407.084374518514,955.4196746325267,-4210.022191539629):47,
             (2946.0198408020497,4856.511829505751,-6614.98505109478):48,
             (3737.0822740921226,5270.450895642849,-5278.9196336943):49,
             (4664.64365234563,6024.404378260297,-3730.783804336487):50,
             (4362.152983533213,5264.9896683827,-330.4757953207826):51,
             (5569.417504595725,6460.793430576633,5421.048850085641):52,
             (6775.61797290782,3226.238340029962,6025.75867889489):53,
             (9110.762206548767,-1739.0363295306556,7621.363269416317):54,
             (8688.56571353183,-4286.355755413659,7117.728526067228):55,
             (8352.168733274038,-6952.267249978224,6709.985804801282):56,
             (8443.195089050523,-5824.430407957365,2749.492570275423):57,
             (8624.745133456714,-3878.809655324538,-1140.5453567984496):58,
             (5814.154106925882,1229.6993153257815,-5518.472254545321):59,
             (3880.248233844353,6388.267687373855,-8701.367717798912):60,
             (4922.735757149115,6934.097154957253,-6940.674046100774):61,
             (6140.930251611103,7924.516438217041,-4907.482255272506):62,
             (5746.387693687689,6934.366712732735,-492.7614873204078):63,
             (6074.110810805622,5313.137095279206,3103.1603383735187):64,
             (7549.6166232716405,1638.3506351207516,4766.116472071773):65,
             (9144.22544761627,-1470.995605268513,5615.164875231808):66,
             (8851.666121034279,-3149.3613711592443,5791.451685441684):67,
             (8500.557984917883,-5550.555360677123,4790.802527852141):68,
             (8594.087862835102,-4460.502732282599,1202.8053973127812):69,
             (8724.82598229055,-3235.6496256362348,-980.5575778174244):70,
             (6874.520048611572,-289.5387261981774,-3821.4400161526414):71,
             (4916.297192060128,4307.513997705836,-6974.795972582456):72,
             (5819.517276565197,5772.740696787963,-5464.249084289627):73,
             (6666.663989554589,6410.850719920749,-4071.3110342969558):74,
             (6280.324414591433,6015.204491438752,-1476.4275931956176):75,
             (7180.305703653475,3151.7678127953095,1373.1975029781495):76,
             (8248.198938024443,714.6748507078441,2817.036007030724):77,
             (9182.988945110867,-1167.764518966436,4015.5942289850245):78,
             (9007.020388812489,-2093.713817441767,3756.923645906545):79,
             (8680.802265994806,-4081.390060312401,3273.7168714125773):80,
             (8780.409047221645,-3130.134177574469,700.5659508608431):81,
             (8857.679484481941,-2443.415301399,-768.5984857936376):82,
             (7839.323835639718,-570.9192199992401,-2304.6246202346338):83,
             (6625.666242680838,2027.7311898612672,-4194.929725399932):84,
             (7108.652147423247,3498.6937253971073,-3402.110197127864):85,
             (7434.816150050725,4358.722695392508,-2869.8331598451205):86,
             (7167.213158394653,4091.808365037888,-1234.4936780628914):87,
             (0.0,0.0,0.0):88,
             (1158.5273281050518,-0.004651426605661868,-0.08668679001253565):89,
             (2112.0476709317145,-0.008427609405003977,-0.15706200883656152):90,
             (2688.734626403421,-0.010711436251753526,-0.19962478265682648):91,
             (3575.6716231579267,-0.014223932083723412,-0.26508577224220176):92,
             (4445.718937221886,-0.017669540483211676,-0.32930020728230147):93,
             (5409.950553527043,-0.021488142643022456,-0.4004659789487164):94,
             (6397.481176248715,-0.025399014791815944,-0.47335134966175474):95,
             (7317.0369197362015,-0.0290406891458872,-0.5412197880815484):96,
             (8480.24950353612,-0.03364730649479952,-0.6270714856782433):97,
             (9341.568974319263,-0.037058350415009045,-0.6906417562959177):98}

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
        closest_colors = sorted(colors, key=lambda color: self.distance(color, pixel, speed))
        closest_color = closest_colors[0]
        return self.ircColors[closest_color]

    def distance(self, c1, c2, speed):
        if speed == 'fast':
            c2 = sRGBColor(c2[0],c2[1],c2[2])
            c2 = convert_color(c2, LabColor)
            c2 = (c2.lab_l, c2.lab_a, c2.lab_b)
            delta_e = delta_E_CIE1976(c1, c2)
        elif speed == 'medium':
            c2 = sRGBColor(c2[0],c2[1],c2[2])
            c2 = convert_color(c2, LabColor)
            c2 = (c2.lab_l, c2.lab_a, c2.lab_b)
            delta_e = delta_E_CMC(c1, c2)
        else:
            c2 = sRGBColor(c2[0],c2[1],c2[2])
            c2 = convert_color(c2, LabColor)
            c2 = (c2.lab_l, c2.lab_a, c2.lab_b)
            delta_e = delta_E_CIE2000(c1, c2)
        return delta_e

    def img(self, irc, msg, args, optlist, url):
        """[--cols <number of columns>] [--invert] [--slow] (<url>)
        Image to Color ASCII Art. --cols to set number of columns wide. --invert to invert the greyscale. 
        --slow for cieCMC delta-e. --insane for cie2000 delta-e. Don't use insane, it takes way too long 
        for little improvement.
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
        response = requests.get(url, headers=header)
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
        """[--cols <number of columns>] [--slow]
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
        response = requests.get(url, headers=header)
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
