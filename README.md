Supybot-Tweety
======

# Twitter client for Supybot

    Description
    
    This is a supybot client.

Instructions
------------
1.) Install the dependencies. You can go the pip route or install via source, depending on your setup. You will need:
    1. Install oauth2: sudo pip install oauth2 
    
2.) You need some keys from Twitter. See http://dev.twitter.com. Steps are:
    1. If you plan to use a dedicated Twitter account, create a new twitter account.
    2. Go to dev.twitter.com and log in. 
    3. Click create an application.
    4. Fill out the information. Name does not matter. 
    5. default is read-only. Since we're not tweeting from this bot/code, you're fine here.
    6. Your 4 magic strings (2 tokens and 2 secrets) are shown.
    7. Once you /msg yourbot load Tweety, you need to set these keys:
      /msg bot config plugins.Tweety.consumer_key xxxxx
      /msg bot config plugins.Tweety.consumer_secret xxxxx
      /msg bot config plugins.Tweety.access_key xxxxx
      /msg bot config plugins.Tweety.access_secret xxxxx

Examples
--------

# Documentation

    
