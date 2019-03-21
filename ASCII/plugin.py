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
from colormath.color_objects import sRGBColor, LabColor
from colormath.color_conversions import convert_color
from colormath.color_diff import delta_e_cie1976

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

    def getAverageC(self, pixel,speed):
        """
        Given PIL Image, return average RGB value
        """
        speed = speed
        ircColors = {LabColor(lab_l=1993.20515351498,lab_a=2324.0983231476234,lab_b=1950.0779087841693):16,
             LabColor(lab_l=2302.159132332113,lab_a=1476.5998328806731,lab_b=2094.817440516089):17,
             LabColor(lab_l=3267.109569734987,lab_a=-625.5719921685046,lab_b=2741.5824054551854):18,
             LabColor(lab_l=3117.7906623358294,lab_a=-1524.3182007475084,lab_b=2563.4872768819705):19,
             LabColor(lab_l=2994.225776415631,lab_a=-2500.8929369695743,lab_b=2413.738641368567):20,
             LabColor(lab_l=3026.0461300232373,lab_a=-2106.053265646869,lab_b=1016.9116217498115):21,
             LabColor(lab_l=3092.2778750318885,lab_a=-1395.2984432353226,lab_b=-410.2808083391245):22,
             LabColor(lab_l=2082.37407522394,lab_a=439.80707297830793,lab_b=-1983.2971244240234):23,
             LabColor(lab_l=1385.5715072995845,lab_a=2298.009119093381,lab_b=-3130.08523478244):24,
             LabColor(lab_l=1761.7248957199076,lab_a=2495.1524432892943,lab_b=-2494.7963736847237):25,
             LabColor(lab_l=2198.7916393341657,lab_a=2850.6336820262986,lab_b=-1765.3360075524952):26,
             LabColor(lab_l=2055.801787008181,lab_a=2491.6677227532045,lab_b=-158.86279448684633):27,
             LabColor(lab_l=2958.9498780747585,lab_a=3441.1996261238046,lab_b=2887.4025267278366):28,
             LabColor(lab_l=3490.7754041570597,lab_a=1995.586399321347,lab_b=3144.023619818683):29,
             LabColor(lab_l=4845.169302249827,lab_a=-926.259480557718,lab_b=4059.3516438937377):30,
             LabColor(lab_l=4620.482019554244,lab_a=-2281.747228870049,lab_b=3791.325963678294):31,
             LabColor(lab_l=4441.121161001645,lab_a=-3702.9723544655367,lab_b=3573.926467529447):32,
             LabColor(lab_l=4489.963665823597,lab_a=-3098.035370892731,lab_b=1453.7194043799368):33,
             LabColor(lab_l=4586.302989902044,lab_a=-2065.9627148173527,lab_b=-607.4864175067376):34,
             LabColor(lab_l=3098.2589552331815,lab_a=634.8559351078204,lab_b=-2924.8401977939):35,
             LabColor(lab_l=2059.250990402592,lab_a=3402.5703829703853,lab_b=-4634.592277094812):36,
             LabColor(lab_l=2613.821127903904,lab_a=3692.817296863682,lab_b=-3697.953525308647):37,
             LabColor(lab_l=3263.3535821224173,lab_a=4220.81951658537,lab_b=-2613.862567115958):38,
             LabColor(lab_l=3052.7880497642973,lab_a=3692.3353415279757,lab_b=-255.20463970260963):39,
             LabColor(lab_l=4230.166177007632,lab_a=4911.647610760525,lab_b=4121.209247509218):40,
             LabColor(lab_l=5140.420692098141,lab_a=2469.29414128601,lab_b=4576.863521782283):41,
             LabColor(lab_l=6922.379978784402,lab_a=-1322.0564509214903,lab_b=5793.940186325644):42,
             LabColor(lab_l=6595.196756134379,lab_a=-3301.6293161796852,lab_b=5403.579861388848):43,
             LabColor(lab_l=6345.679321104374,lab_a=-5285.277604778105,lab_b=5101.0895334333245):44,
             LabColor(lab_l=6414.068737559316,lab_a=-4437.401859025286,lab_b=2114.577589536168):45,
             LabColor(lab_l=6552.8983320653,lab_a=-2948.7626219415083,lab_b=-867.069491832234):46,
             LabColor(lab_l=4407.084374518514,lab_a=955.4196746325267,lab_b=-4210.022191539629):47,
             LabColor(lab_l=2946.0198408020497,lab_a=4856.511829505751,lab_b=-6614.98505109478):48,
             LabColor(lab_l=3737.0822740921226,lab_a=5270.450895642849,lab_b=-5278.9196336943):49,
             LabColor(lab_l=4664.64365234563,lab_a=6024.404378260297,lab_b=-3730.783804336487):50,
             LabColor(lab_l=4362.152983533213,lab_a=5264.9896683827,lab_b=-330.4757953207826):51,
             LabColor(lab_l=5569.417504595725,lab_a=6460.793430576633,lab_b=5421.048850085641):52,
             LabColor(lab_l=6775.61797290782,lab_a=3226.238340029962,lab_b=6025.75867889489):53,
             LabColor(lab_l=9110.762206548767,lab_a=-1739.0363295306556,lab_b=7621.363269416317):54,
             LabColor(lab_l=8688.56571353183,lab_a=-4286.355755413659,lab_b=7117.728526067228):55,
             LabColor(lab_l=8352.168733274038,lab_a=-6952.267249978224,lab_b=6709.985804801282):56,
             LabColor(lab_l=8443.195089050523,lab_a=-5824.430407957365,lab_b=2749.492570275423):57,
             LabColor(lab_l=8624.745133456714,lab_a=-3878.809655324538,lab_b=-1140.5453567984496):58,
             LabColor(lab_l=5814.154106925882,lab_a=1229.6993153257815,lab_b=-5518.472254545321):59,
             LabColor(lab_l=3880.248233844353,lab_a=6388.267687373855,lab_b=-8701.367717798912):60,
             LabColor(lab_l=4922.735757149115,lab_a=6934.097154957253,lab_b=-6940.674046100774):61,
             LabColor(lab_l=6140.930251611103,lab_a=7924.516438217041,lab_b=-4907.482255272506):62,
             LabColor(lab_l=5746.387693687689,lab_a=6934.366712732735,lab_b=-492.7614873204078):63,
             LabColor(lab_l=6074.110810805622,lab_a=5313.137095279206,lab_b=3103.1603383735187):64,
             LabColor(lab_l=7549.6166232716405,lab_a=1638.3506351207516,lab_b=4766.116472071773):65,
             LabColor(lab_l=9144.22544761627,lab_a=-1470.995605268513,lab_b=5615.164875231808):66,
             LabColor(lab_l=8851.666121034279,lab_a=-3149.3613711592443,lab_b=5791.451685441684):67,
             LabColor(lab_l=8500.557984917883,lab_a=-5550.555360677123,lab_b=4790.802527852141):68,
             LabColor(lab_l=8594.087862835102,lab_a=-4460.502732282599,lab_b=1202.8053973127812):69,
             LabColor(lab_l=8724.82598229055,lab_a=-3235.6496256362348,lab_b=-980.5575778174244):70,
             LabColor(lab_l=6874.520048611572,lab_a=-289.5387261981774,lab_b=-3821.4400161526414):71,
             LabColor(lab_l=4916.297192060128,lab_a=4307.513997705836,lab_b=-6974.795972582456):72,
             LabColor(lab_l=5819.517276565197,lab_a=5772.740696787963,lab_b=-5464.249084289627):73,
             LabColor(lab_l=6666.663989554589,lab_a=6410.850719920749,lab_b=-4071.3110342969558):74,
             LabColor(lab_l=6280.324414591433,lab_a=6015.204491438752,lab_b=-1476.4275931956176):75,
             LabColor(lab_l=7180.305703653475,lab_a=3151.7678127953095,lab_b=1373.1975029781495):76,
             LabColor(lab_l=8248.198938024443,lab_a=714.6748507078441,lab_b=2817.036007030724):77,
             LabColor(lab_l=9182.988945110867,lab_a=-1167.764518966436,lab_b=4015.5942289850245):78,
             LabColor(lab_l=9007.020388812489,lab_a=-2093.713817441767,lab_b=3756.923645906545):79,
             LabColor(lab_l=8680.802265994806,lab_a=-4081.390060312401,lab_b=3273.7168714125773):80,
             LabColor(lab_l=8780.409047221645,lab_a=-3130.134177574469,lab_b=700.5659508608431):81,
             LabColor(lab_l=8857.679484481941,lab_a=-2443.415301399,lab_b=-768.5984857936376):82,
             LabColor(lab_l=7839.323835639718,lab_a=-570.9192199992401,lab_b=-2304.6246202346338):83,
             LabColor(lab_l=6625.666242680838,lab_a=2027.7311898612672,lab_b=-4194.929725399932):84,
             LabColor(lab_l=7108.652147423247,lab_a=3498.6937253971073,lab_b=-3402.110197127864):85,
             LabColor(lab_l=7434.816150050725,lab_a=4358.722695392508,lab_b=-2869.8331598451205):86,
             LabColor(lab_l=7167.213158394653,lab_a=4091.808365037888,lab_b=-1234.4936780628914):87,
             LabColor(lab_l=0.0,lab_a=0.0,lab_b=0.0):88,
             LabColor(lab_l=1158.5273281050518,lab_a=-0.004651426605661868,lab_b=-0.08668679001253565):89,
             LabColor(lab_l=2112.0476709317145,lab_a=-0.008427609405003977,lab_b=-0.15706200883656152):90,
             LabColor(lab_l=2688.734626403421,lab_a=-0.010711436251753526,lab_b=-0.19962478265682648):91,
             LabColor(lab_l=3575.6716231579267,lab_a=-0.014223932083723412,lab_b=-0.26508577224220176):92,
             LabColor(lab_l=4445.718937221886,lab_a=-0.017669540483211676,lab_b=-0.32930020728230147):93,
             LabColor(lab_l=5409.950553527043,lab_a=-0.021488142643022456,lab_b=-0.4004659789487164):94,
             LabColor(lab_l=6397.481176248715,lab_a=-0.025399014791815944,lab_b=-0.47335134966175474):95,
             LabColor(lab_l=7317.0369197362015,lab_a=-0.0290406891458872,lab_b=-0.5412197880815484):96,
             LabColor(lab_l=8480.24950353612,lab_a=-0.03364730649479952,lab_b=-0.6270714856782433):97,
             LabColor(lab_l=9341.568974319263,lab_a=-0.037058350415009045,lab_b=-0.6906417562959177):98}
        colors = list(ircColors.keys())
        closest_colors = sorted(colors, key=lambda color: self.distance(color, pixel, speed))
        closest_color = closest_colors[0]
        return ircColors[closest_color]

    def distance(self, c1, c2, speed):
        if speed == 'fast':
            rgb2 = sRGBColor(c2[0], c2[1], c2[2])
            lab1 = c1
            lab2 = convert_color(rgb2, LabColor)
            (r1,g1,b1) = lab1.lab_l, lab1.lab_a, lab1.lab_b
            (r2,g2,b2) = lab2.lab_l, lab2.lab_a, lab2.lab_b
            return math.sqrt((r1 - r2)**2 + (g1 - g2) ** 2 + (b1 - b2) **2)
        elif speed == 'medium':
            c2 = sRGBColor(c2[0],c2[1],c2[2]);
            c2 = convert_color(c2, LabColor);
            delta_e = delta_e_cie1976(c1, c2);
            return delta_e

    def img(self, irc, msg, args, optlist, url):
        """[--cols <number of columns>] [--invert] [--slow] (<url>)
        Image to ANSI Art
        """
        optlist = dict(optlist)
        if 'slow' in optlist:
            speed = 'medium'
        else:
            speed = 'fast'
        if 'cols' in optlist:
            cols = optlist.get('cols')
        else:
            cols = 100
        if 'invert' in optlist:
            gscale = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\|()1{}[]?-_+~<>i!lI;:,\"^`'. "
        else:
            gscale = " .'`^\",:;Il!i><~+_-?][}{1)(|\/tfjrxnuvczXYUJCLQ0OZmwqpdbkhao*#MW&8%B@$"
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
        os.remove(filename)
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
        image2 = image2.convert('RGBA')
        image2 = image2.resize((cols, rows), Image.LANCZOS)
        colormap = np.array(image2)
        # ascii image is a list of character strings
        aimg = []
        # generate list of dimensions
        old_color = None
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
                # get average luminance
                avg = int(self.getAverageL(img))
                # look up ascii char
                gsval = gscale[int((avg*69)/255)]
                # get color value
                color = self.getAverageC(colormap[j][i].tolist(),speed)
                if color != old_color or gsval != " ":
                    old_color = color
                    # append ascii char to string
                    aimg[j] += "\x03{0}{1}".format(color, gsval)
                else:
                    aimg[j] += "{0}".format(gsval)
        # return txt image
        output = aimg
        for line in output:
            irc.reply(line, prefixNick=False, noLengthCheck=False)
    img = wrap(img,[getopts({'cols':'int', 'invert':'', 'slow':''}), ('text')])


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


