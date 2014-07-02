Cobe
===============

This is a plugin for Supybot that allows your bot to use [Cobe](https://github.com/pteichman/cobe)

A description of cobe: http://teichman.org/blog/2011/02/cobe.html

Description

    "What bot is complete without some type of plugin to make it talk?"

Instructions

    You need to install cobe first for this plugin to work. After doing that, just place the Cobe folder into your plugin
    folder ( or run "install waratte Cobe" if you have the PluginDownloader plugin) and "load Cobe". 
    
    The default options in the config file are set to ensure that the bot does not talk on its own without 
    someone mentioning it. Take care, because the bot could easily go crazy if you set the wrong options. ;)

    I have not wrote a commanded to lobotomize a brain on command yet, so you'll have to do it remove the brain manually 
    in the console. 
    
    Each channel at the moment has a separate brain, I am looking into having an option that allows one
    to only have one brain. 
    
    These are the current commands:
    
     * brainsize: Gives the size of the brain for a given channel on the disk.
     * teach: Teaches the bot a phrase.
     * reply: Tells the bot to respond to a command without teaching it anything.


Inspiration: https://github.com/reticulatingspline/Supybot-MegaHAL


