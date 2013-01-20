Supybot-Tweety
======

# Twitter client for Supybot

Description
-----------
    
This is a Supybot plugin to work with Twitter. It allows a user to search for Tweets,
display specific tweets and timelines from a user's account, and display Trends.

It has been updated to work with the oAuth requirement in v1.1 API along with their
updated endpoints.

For working v1.1 API clients, I am aware of only this and ProgVal's Twitter client.
This is a much watered down version of ProgVal's Twitter client. It only includes
read-only features (no risk of accidental Tweeting) that most folks use: 
tweet display, tweet searching and trends.

Instructions
------------
1.) On an up-to-date Python 2.7+ system, one dependency is needed. 
    You can go the pip route or install via source, depending on your setup. You will need:
    1. Install oauth2: pip install oauth2

2.) You need some keys from Twitter. See http://dev.twitter.com. Steps are:
    1. If you plan to use a dedicated Twitter account, create a new twitter account.
    2. Go to dev.twitter.com and log in. 
    3. Click create an application.
    4. Fill out the information. Name does not matter. 
    5. default is read-only. Since we're not tweeting from this bot/code, you're fine here.
    6. Your 4 magic strings (2 tokens and 2 secrets) are shown.
    7. Once you /msg <bot> load Tweety, you need to set these keys:
        * /msg <bot> config plugins.Tweety.consumerKey xxxxx
        * /msg <bot> config plugins.Tweety.consumerSecret xxxxx
        * /msg <bot> config plugins.Tweety.accessKey xxxxx
        * /msg <bot> config plugins.Tweety.accessSecret xxxxx
    8. Next, I suggest you /msg <bot> config search Tweety. There are a lot of options here.
    9. Things should work fine from here providing your keys are right.

Examples
--------

Background
----------
Hoaas, on GitHub, started this plugin with basics for Twitter and I started to submit
ideas and code. After a bit, the plugin was mature but Twitter, in 2012, put out the 
notice that everything was changing with their move to v1.1 of the API. The client had
no oAuth code, was independent of any Python library, so it needed a major rewrite. I 
decided to take this part on, using chunks of code from an oAuth/Twitter wrapper and
later rewriting/refactoring many of the existing functions with the massive structural
changes.

So, as I take over, I must acknowledge the work done by Hoaas:
http://github.com/Hoaas/
Much/almost all of the oAuth code ideas came from:
https://github.com/jpittman/OAuth-Python-Twitter

Documentation
-------------

* https://dev.twitter.com/docs/api/1.1
