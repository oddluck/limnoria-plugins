[![paypal](https://www.paypalobjects.com/en_US/i/btn/btn_donateCC_LG.gif)](https://www.paypal.com/cgi-bin/webscr?cmd=_s-xclick&hosted_button_id=T8E56M6SP9JH2)

#ASCII Art Plugin

Requires Limnoria https://github.com/ProgVal/Limnoria and Python3

pip install -r requirements.txt

Configure the delay between lines when outputting ASCII. Setting configurable per channel.
```
config channel plugins.ascii.delay 0.5 (set a delay of 0.5 seconds between lines, default 1.0)
```

Convert text to ASCII art or image URLs to ASCII/ANSI art. Support for the Paste.ee API to save art conversions for later use.
Get an API key from https://paste.ee/account/api (FREE. Not required to use plugin, disabled by default).
```
config plugins.ascii.pasteAPI <PASTE.EE_API_KEY_HERE> (set paste.ee API key)
config channel plugins.ascii.pasteEnable <True/False> (enable/disable paste.ee links)
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
```
img <url> (convert an image <url> to ascii art using euclidian color distance and 99 color palette)
img --16 <url> (convert image to ascii art using euclidian color distance and 16 color palette)
img --invert <url> (invert the ascii luminance character palette)
```
```
ansi <url> (convert an <url> to ansi block art using euclidian color distance and 99 color palette)
ansi --16 <url> (convert <url> to ansi block art using euclidian color distance and 16 color palette)
```
Speed Presets. Euclidian (the default, no --speed preset) is very fast. The following presets each get progressively slower but color choice should improve with slower presets.
```
img/ansi --fast <url> (use cie1976 color difference algorithm)
img/ansi --slow <url> (use cie1994 color difference algorithm)
img/ansi --slower <url> (use cieCMC color difference algorithm)
img/ansi --slowest <url> (use cie2000 color difference algorithm)
```
Scroll ASCII/ANSI Art .TXT or .ANS Files from URL
```
scroll <url> (playback of ansi/ascii art .txt files from the web)
a2m <url> (conversion and playback of ansi art .ans files from the web.)
```
a2m command requires A2M https://github.com/tat3r/a2m (optional. disable command if not installing a2m.)
```
p2u <url>
```
p2u command requires p2u https://git.trollforge.org/p2u/about/ (optional. disable command if not installing p2u.)
