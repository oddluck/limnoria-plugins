Generate text art from images, text, or scroll text art links. Don't use this...


## Try the plugin out in #ircart on EFnet. 

irc://irc.efnet.org/#ircart


<b>TextArt Plugin</b><br>
Convert text to figlet fonts or image URLs to ASCII/ANSI art. Covert IRC art to PNG. Get weather, moon phase, and cryptocurrecy rates.

Requires Limnoria https://github.com/ProgVal/Limnoria and Python 3.7+

pip install -r requirements.txt

```
config plugins.TextArt.delay 0.5
```
Delay config can be set per channel. Set a value that won't get you kicked. You can also use --delay with commands to override this setting.

```
!cq
@cq
.cq
etc.
```
Stop the scroll. cq command must be prefixed by a command character. This command can not be renamed.

Support for the Paste.ee API to save art conversions for later use.
Get an API key from https://paste.ee/account/api (FREE. Not required to use plugin, disabled by default).
```
config plugins.TextArt.pasteAPI <PASTE.EE_API_KEY_HERE> (set paste.ee API key)
config channel plugins.TextArt.pasteEnable <True/False> (enable/disable paste.ee links)
```

ASCII Weather from wttr.in
```
wttr <location>
wttr moon
wttr --16 (use 16 colors. Default)
wttr --99 (use 99 colors)
wttr <location>?u (use imperial units, degrees F, miles, etc.)
wttr <location>?m (use metric units, degrees C, km, etc.)
wttr <location>?<1-3> (number of days to forecast)
```
![Image of Wttr Command Output](https://i.imgur.com/o0kf25O.png)
![Image of Wttr Command Output](https://i.imgur.com/mTHJfuI.png)<br>

ASCII crypto exchange rates from rate.sx
```
rate (get rates in united states dollars)
rate --sub <currency> (get rates in EUR, USD, BTC, etc.)
rate <coin> (get a graph showing rate fluctuation)
rate --sub <currency> <coin> (get graphs with desired currency)
```
![Image of Rate Command Output](https://i.imgur.com/tuYTQbw.png)

Return a random fortune entry from http://www.asciiartfarts.com/fortune.txt
```
fortune
```

Text-to-ASCII Art (split lines with | ex. ascii|art for large fonts):
```
artii <text> (convert <text> to ascii art)
artii --font <font> <text> (to use chosen <font>)
artii --color <color> <text> (to set a foreground <color>)
artii --color <color1,color2> <text> (to set a foreground/background <color>)
fontlist (get list of availble <fonts>)

                                   88  88  
                                   ""  ""  
,adPPYYba,  ,adPPYba,   ,adPPYba,  88  88  
""     `Y8  I8[    ""  a8"     ""  88  88  
,adPPPPP88   `"Y8ba,   8b          88  88  
88,    ,88  aa    ]8I  "8a,   ,aa  88  88  
`"8bbdP"Y8  `"YbbdP"'   `"Ybbd8"'  88  88  
```

Image URL to ASCII/ANSI Art:
```
img <url> (convert an image <url> to text art using 99 color palette)
img --w <###> <url> (how many columns wide. defauls to 100)
img --16 <url> (convert using 16 color palette)
img --ascii <url> (convert image to colored ascii art)
img --block <url> (colored space block art)
img --chars "TEXT" <url> (convert image to colorized custom text)
img --ramp "TEXT" <url> (use a custom greyscale ramp e.g. " .-:=+x#%@")
img --ramp "░▒▓█" <url> (image to colorized ansi shader blocks)
img --nocolor <url> (text only greyscale character ramp output)
img --invert <url> (invert the greyscale character ramp)
img --bg <0-99> <url> (set a background color)
img --fg <0-99> <url> (set a foreground color)
img --fast <url> (use Euclidean color difference.)
img --slow <url> (use cie2000 color difference. best quality, default)
img --quantize <url> (quantize source image to 256 colors. trades off quality for speed)
img --no-quantize <url> (don't quantize source to 256 colors)
```
Here are some images using 99 color default output:
![Image of Img Command Output](https://i.imgur.com/NrMaQdg.png)<br>
^ output of img https://i.imgur.com/aF9wihd.jpg (image command with default settings)
![Image of Img Command Output](https://i.imgur.com/ydNaDKc.png)<br>
^ output of img --block https://i.imgur.com/aF9wihd.jpg (image command with colored space blocks)
![Image of Img Command Output](https://i.imgur.com/Q2lsg3H.png)<br>
^ output of img --ascii https://i.imgur.com/aF9wihd.jpg (image command with colored space blocks)
```
***************+*++++++++++++++++++++++++++++++++++++++=++=++========================---------------
***********+++++++++++++++++++++++++++++++++++++++++++++++============================--------------
***********++++++++++++++++++++++++++++***++++**********+++++++======================---------------
********++++++++++++++++++++++++++++*******++****#********+***++++====================--------------
********++*++++++++++++++++++++++************##%%#####%#*****++***++==================--------------
******+*++++++++++++++++++++++++**+***#*+++*%@%%#*##%###****++++++++++===============---------------
******+++++++++++++++++++++++**++++####++*+##@@#+**##%%@@%##*****++++==+=========-------------------
******++++++++++++++++++++++*#*=*+####*+*++%++@*=*#%@@@@@@@%#**++++==+============------------------
****+++++++++++++++++++++++*+##++#%###+=*+-+#=*%%@@@@@@@@@@@%##*+======+========--------------------
***++++++++++++++++++++++++**###*++***+=*#+==#%#****##%%@@@@@@%#*==============---------------------
**++++++++++++++++++++++++++**#%%%##%@@@@%*+=++=+#%%%@%%@@@@@@@@@#+============-=-------------------
***++++++++==========++++++++#%@@@@@@@@#*+**#*==*%@@@%@@@@@%%@@@%@@*+===========--------------------
**+++++++**#%%@@%#*+=---===+*%%@@@@@@@**#%%@@@#*+++**=*##*****#%@@@@#+===========-------------------
*++++++++#%@@@%###%%%%#*=--=+*%@@@@@@%+#%@@@#%@#++=++++=+++*****##%@@%*=======-==-------------------
*++++++++*###%%#*++*%@@@@@#++*%@@@@@@%*%@@@@*#*=++*++=++**+++++++++*****====---=--------------------
**++++++++**###%@%%%@@@@@@@%##@@@@@@@@*%@%%#*+=+**+++++*++====++++++**##*=--------------------------
**++++++++++**##%@@#*#%%@@###%@@@@@@@@*++++==++**=+++**+=========++****#%%*-------------------------
***+++++++++++**#%%#+++#%@#+**####%%@#+=+++**++*++++*#*+=====+++==+==+*#**%#=-----------------------
*+++++++++++++++**#%%*+*#%#+****#****#*+****++**+++***+=====++=---:-==#@%**#%=----------------------
++++++++++++++++++**#%%%%*+=+**#*****%*####*++**++++**+====++=-+%%*=:-=#@@#+#%=---------------------
++++++++++++++++++++*##%%#++++*#**#*#*+*##*+++#*++++**+===+++=-*@@@@*--=+%%++##-----------------::::
+++++++++++++++++++++*###**+++**###*+++****+++#*+++++**=====+===*%@@%=-==+**+*#=----------------::::
+++++++++++++++++++++++*++++=+#####+=+++*#*+++*#+++*+*#+++==++==--=+=====++***#*---------------:::::
+++++++++++++++++++++========*####*++++++##+++*#*++*++*#++==+++=====--===++***%*---------------:::::
++++++++++++++++++++++++++**%#*##*+++==++*%#****#*****+*#*+==++*+=======++**##%+---------:::::::::::
+++++++++++++++++++++++***##**#%#+++++++++*%%#**####*****##****##**++++++*##%%*--------:::::::::::::
+++++++++++++++++++++++####**#%%#++++++++++*#%####%%######%%%*+*@@@@%###%%@@%*+==----:-:::::::::::::
+++++++++++++++++++++++#%%#####*#****++++++**#%%%%%@@@@@@@@@@%**@@@@@@@@@%%%%#*++==--:::::::::::::::
+++++++++++++++++=+++++*#%%%%%%%###****+***###%%@@@@@@@@@@@@@@@@@@@@%*#%%%%%%##*+++=-:::::::::::::::
++++++++++++++++++++++****#%%%%#############%%@@@@%#%@@@#*%@@@@@@@@@= .+%%@%%%#*++=--:::::::::::::::
+++++++++++++++++++++*+++*###******#*#%%%%%%%%%#*+++++**: :%@@@@@@@@%+*%#%%%%%%#*++===----::::::::::
++++++++++++++++==++*++**###**###*#**##%##****++====+==-===+%@@@@@@%%@######%%@@@@@@%%#**++===-:::::
++++++++++++++++++=+++***#######**##**#%#*#*####*++++=====+===+*********####%%@@@@@@@@@@%%##**+==--:
+++++++++++++++++++++++****###%##%%#**###%%%%%%%%##*++==========+++++**++**%%%@@@@@@@@@@@@@@%%##*+=-
+++++++++++++++++==+++++****###%%%%##*##%@@@%%@%%%####***+====++++***##***#%%%@@@@@@@@@@@@@@@@@%%#*+
++++++++++++++++++++++++***#######%#*###%%@@@@@@%@@%%@%%#####******##%#%%@@@@@@@@@@@@@@@@@@@@@@%%%#*
++++++++++++++++++++*****######%#########%%%@@@@@@@@@@@@@@@%%%%%%%%%@@@@@@@@@@@@@@@@@@@@@@@@@@@%####
+++++++++++++=+++++++**#%%#####%%%%%%###%%#%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%####***
++++++++++++++++++***##%%@%##%%%%%%%%%%@@%%@%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%#*******#
++++++++++++=++++*##%%%##%%%%%%%%%%%%%%%%%#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%#***++**##
++++++++++==+****#%%%%####%##%%%%%%%#**++*+*@%%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%****++*##
++++++++++**####**####%###%#%%#@%@%#*+*****#**%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%###**#***#
++++++++*#######**####%%##%##*%@@@%%##*+**+**%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%@@@@%#*****#**
+++++**########%##%%%%%%%#####%@@@@%**+*#**#%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%@%%%#**##**#
+++**###########+#%%%%%##%%%*#%@@@@#**#####%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%%####**###*
+**#%%%%%%%%##*++*#####**##***###%%####*****####**%@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@%%%%#########%#
##%%%%%%%%%#*++=+++*****+++++++++++++===========+#%%@@@@@@@@@@@@@@@@@@@@@%%%%@@@@@@@@@@@@%%%%%##*##%
%%%@@@@@@@%#*++====+*****++*+++++++++=========++***%@@@@@@@@@@@@@@@@@%%%#**###%%@@@@@@@@@@@@@@%%#**#
%@@@@@@@###**+++=+++++**#*+***++*++++++++++==+***+*%%@@@@@@@@@@@@@@@%%###**####%%%@@@@@@@@@@@@@@@%##
@@@@@@@%#++**+***+++*****+**#####***++++==+=+****+*#%%@@@@@@@@@@@@@@%%####**##%@%%%%%%%##%%@@@@@@@@@
```
^ Output of img --nocolor --invert https://i.imgur.com/aF9wihd.jpg


Scroll ASCII/ANSI Art text files
```
scroll <url> (playback of ansi/ascii art .txt files from the web)
```

Create PNG images from ascii art text files.
```
png <url>
png --size 10-99 <url> (set a font size. defaults to 15pt)
png --bg 0-99 <url> (set a background color)
png --fg 0-99 <url> (set a foreground color)
```
Get your imgur Client ID from https://imgur.com/account/settings (FREE).
```
config plugins.TextArt.imgurAPI <CLIENT_ID_HERE> (set imgur API key)
```

<b>THE COMMANDS BELOW REQUIRE ADDITIONAL INSTALLS AND ARE OPTIONAL. YOU WILL NEED TO VISIT THE GITHUB
PAGES BELOW AND INSTALL THE PROGRAMS IF YOU WANT TO USE THESE COMMANDS. </b>

ANSI Art to IRC converrter:
```
a2m <url> (conversion and playback of ansi art .ans files from the web.)
```
a2m command requires A2M https://github.com/tat3r/a2m (optional. disable command if not installing a2m.)

Picture to Unicode
```
p2u <url>
```
![Image of p2u command](https://i.imgur.com/CBarBzz.png)<br>
^ Output of p2u https://i.imgur.com/aF9wihd.jpg

p2u command requires p2u https://git.trollforge.org/p2u/about/ (optional. disable command if not installing p2u.)

TDFiglet. Text to tdfiglet
```
tdf [-f <font>] <text> (select font with -f <fontname>)
fonts (list of figlet fonts)
```
![image of tdf commad](https://i.imgur.com/Jctpbno.png)<br>
tdf command requires tdfiglet https://github.com/tat3r/tdfiglet (optional. disable command if not installing tdfiglet.)

Toilet. Requires installation of toilet. sudo apt install toilet etc. (optional as usual)
```
toilet -f <font> -F <filter1,filter2> <text> (do the text to toilet stuff)
```
get fonts. looks for fonts in /usr/share/figlet/
```
fonts --toilet
```
![Image of toilet command](https://i.imgur.com/dJChPnj.png)
