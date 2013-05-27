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

If you need to do any type of Twittering via the bot such as posting tweets,
responding, announcing of timelines, you will want ProgVals.

This will never contain more than what is above.

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
    8. /msg <bot> reload Tweety - THIS IS REQUIRED. YOU MUST RELOAD BEFORE USING.

    Next, I suggest you /msg <bot> config search Tweety. There are a lot of options here.

    Things should work fine from here providing your keys are right.

Examples
--------

    - Twitter Trends
    <me> trends
    <bot> Top 10 Twitter Trends in United States :: #BeforeIDieIWantTo | #ThingsIMissAboutMyChildhood | Happy Memorial Day | #RG13 | #USA | #america | BBQ | WWII | God Bless | Facebook

    - Searching Twitter
    <me> tsearch news
    <bot> @ray_gallego (Ray Gallego): http://t.co/ftNbDEzXaR (Researchers say Western IQs dropped 14 points over last century) (14s ago)
    <bot> @surfing93 (emilyhenderson): @MariaaEveline Hay here is the Crestillion Interview. http://t.co/CEiDpboeMX (15s ago)

    - Getting tweets from someones' timeline.
    <me> twitter --num 3 @ESPNStatsInfo
    <bot> @ESPNStatsInfo (ESPN Stats & Info): In 1st-round win vs Daniel Brands, Rafael Nadal lost 19 games. He lost a total of 19 games in the 1st 4 rounds at last year's French Open. (30m ago)
    <bot> @ESPNStatsInfo (ESPN Stats & Info): Key stats from Miami's win yesterday. Haslem's jump shot, LeBron's post-up and more: http://t.co/a4CcUnKJMi (53m ago)
    <bot> @ESPNStatsInfo (ESPN Stats & Info): Heat avoid losing consecutive games. They haven't lost 2 straight in more than 5 months (January 8-10) (1h ago)

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
Much/almost all of the oAuth code came from:
https://github.com/jpittman/OAuth-Python-Twitter

Documentation
-------------

* https://dev.twitter.com/docs/api/1.1
