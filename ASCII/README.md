[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=T8E56M6SP9JH2)


<b>ASCII Art Plugin</b><br>
Convert text to ASCII art or image URLs to ASCII/ANSI art. Covert ASCII art to PNG. Get ASCII weather, moon phase, and cryptocurrecy rates.

Requires Limnoria https://github.com/ProgVal/Limnoria and Python3

pip install -r requirements.txt

```
config protocols.irc.throttletime 0.0
config plugins.ascii.delay 0.5
```
If you want delays < 1.0 seconds then disable Limnoria's throttling and use this plugin's delay option. 0.5 is 2 lines per second for example. You can also use --delay with commands and override the delay with your own. Default delay config can 
be set per channel. Set a value that won't get you kicked.

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
config plugins.ascii.pasteAPI <PASTE.EE_API_KEY_HERE> (set paste.ee API key)
config channel plugins.ascii.pasteEnable <True/False> (enable/disable paste.ee links)
```

ASCII Weather from wttr.in
![Image of Wttr Command Output](https://i.imgur.com/Ld6zl0W.png)
```
wttr <location>
wttr moon
wttr --16 <location>/moon
```
Use --16 for 16 colors. Defaults to 99 color extended.

ASCII crypto exchange rates from rate.sx
![Image of Rate Command Output](https://i.imgur.com/tuYTQbw.png)
```
rate (get rates in united states dollars)
rate --sub <currency> (get rates in EUR, USD, BTC, etc.)
rate <coin> (get a graph showing rate fluctuation)
rate --sub <currency> <coin> (get graphs with desired currency)
```
Use --16 for 16 colors. Defaults to 99 color extended

Return a random fortune entry from http://www.asciiartfarts.com/fortune.txt
```
fortune
```

Cowsay. Generate a cowsay ascii. choose character with --type. https://easyapis.soue.tk/api/cowsay
![Image of Cow Command Output](https://i.imgur.com/H7nUJ4w.png)
```
cow --type <type> <text> (make a cowsay message. type is optional. defaults to cow)
```

Text-to-ASCII Art (split lines with | ex. ascii|art for large fonts):
```
ascii <text> (convert <text> to ascii art)
ascii --font <font> <text> (to use chosen <font>)
ascii --color <color> <text> (to set a foreground <color>)
ascii --color <color1,color2> <text> (to set a foreground/background <color>)
fontlist (get list of availble <fonts>)
```

Image URL to ASCII/ANSI Art:
![Image of Img Command Output](https://i.imgur.com/MbdajhH.png)
```
img <url> (convert an image <url> to ascii art using 99 color palette)
img --16 <url> (convert image to ascii art using 16 color palette)
img --invert <url> (invert the ascii luminance character palette)
img --chars "TEXT" <url> (convert image to colorized custom text)
img --ramp "TEXT" <url> (use a custom luma ramp e.g. " .-:=+x#%@")
img --bg <0-99> --chars " " <url> (convert image to colorized space block)
img --ramp "░▒▓█" <url> (image to colorized shader blocks)
img --bg <0-99> <url> (set a background color)
img --w <###> <url> (how many columns wide. defauls to 100)
```
Speed Presets. Defaults to slowest. It's actually pretty fast.
```
img --faster <url> (use Euclidean color difference algorithm)
img --fast <url> (use cie1976 color difference algorithm)
img --slow <url> (use cie1994 color difference algorithm)
img --slower <url> (use cieCMC color difference algorithm)
img --slowest <url> (use cie2000 color difference algorithm)
```
Different presets will yeild slightly different results, try them if you want. Slowest (the default)
is usually pretty good.

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
config plugins.ascii.imgurAPI <CLIENT_ID_HERE> (set imgur API key)
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
p2u command requires p2u https://git.trollforge.org/p2u/about/ (optional. disable command if not installing p2u.)

TDFiglet. Text to tdfiglet
```
tdf [-f <font>] <text> (select font with -f <fontname>)
fonts (list of figlet fonts)
```
tdf command requires tdfiglet https://github.com/tat3r/tdfiglet (optional. disable command if not installing tdfiglet.)

Toilet. Requires installation of toilet. sudo apt install toilet etc. (optional as usual)
```
toilet -f <font> -F <filter1,filter2> <text> (do the text to toilet stuff)
```
get fonts. looks for fonts in /usr/share/figlet/
```
fonts --toilet
```
