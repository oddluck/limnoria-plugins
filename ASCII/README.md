#ASCII Art Plugin

pip install -r requirements.txt

ascii (text) convert text to ascii art

img (url) convert an image to ascii art - now in color!

ansi (url) convert an image to ansi art

The img/ansi commands use the 99 color extended irc color set.
Be sure your client supports 99 color output.
Three presets: fast (default), slow, and insane.
Fast uses the cie1976 color difference algorithm,
slow uses the cie_cmc algorithm and insane uses the
cie2000 algorithm. Which looks best is a matter of preference,
slower settings generally result in more colorful images
but take considerably longer to generate a color map.

scroll (url) playback of ansi art files from the web

fontlist to get list of fonts

ascii --font (font) (text) to use chosen font.

ascii --color (color) (text) to set a foeground color

ascii --color (color1,color2) (text) to set a foreground and/or background color

split lines with | ex. ascii|art for large fonts
