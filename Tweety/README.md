Forked from https://github.com/reticulatingspline/Tweety

# Limnoria plugin for Twitter.

## Introduction

This began with [Hoaas](https://github.com/Hoaas) making a slimmed down version of
ProgVal's [Twitter plugin](https://github.com/ProgVal/Supybot-Plugins/Twitter). He
was just interested in reading Tweets and showing information about the account, not
having any write cabaility. I started adding features to it and had to do an entire
rewrite after Twitter introduced the v1.1 API.

This plugin is able to display information on accounts, display specific tweets, search for tweets, and display trends.

If you are looking for anything outside of this, I suggest you do not run this plugin and instead install
ProgVal's version that I linked to above.


## Install

You will need a Limnoria bot on Python 3 for this to work.

```
load plugindownloader
install oddluck Tweety
```

To install additional requirements, run:

```
cd /your/bot/plugin/directory/Tweety
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load Tweety
```

[Fetch the API keys for Twitter](http://dev.twitter.com) by signing up (free).
Create an application. Fill out the requested information. Name does not matter
but the name of the application must be unique. Default is read-only, which is fine.
Once complete, they'll issue you 4 different "strings" that you need to input
into the bot, matching up with the config variable names.

```
/msg <bot> config plugins.Tweety.consumerKey xxxxx
/msg <bot> config plugins.Tweety.consumerSecret xxxxx
/msg <bot> config plugins.Tweety.accessKey xxxxx
/msg <bot> config plugins.Tweety.accessSecret xxxxx
```

Now, reload the bot and you should be good to go:

```
/msg bot reload Tweety
```

Optional: There are some config variables that can be set for the bot. They mainly control output stuff.

```
/msg bot config search Tweety
```

## Example Usage

```
<me> trends
<bot> Top 10 Twitter Trends in United States :: #BeforeIDieIWantTo | #ThingsIMissAboutMyChildhood | Happy Memorial Day | #RG13 | #USA | #america | BBQ | WWII | God Bless | Facebook

<me> tsearch news
<bot> @ray_gallego (Ray Gallego): http://t.co/ftNbDEzXaR (Researchers say Western IQs dropped 14 points over last century) (14s ago)
<bot> @surfing93 (emilyhenderson): @MariaaEveline Hay here is the Crestillion Interview. http://t.co/CEiDpboeMX (15s ago)

<me> twitter --num 3 @ESPNStatsInfo
<bot> @ESPNStatsInfo (ESPN Stats & Info): In 1st-round win vs Daniel Brands, Rafael Nadal lost 19 games. He lost a total of 19 games in the 1st 4 rounds at last year's French Open. (30m ago)
<bot> @ESPNStatsInfo (ESPN Stats & Info): Key stats from Miami's win yesterday. Haslem's jump shot, LeBron's post-up and more: http://t.co/a4CcUnKJMi (53m ago)
<bot> @ESPNStatsInfo (ESPN Stats & Info): Heat avoid losing consecutive games. They haven't lost 2 straight in more than 5 months (January 8-10) (1h ago)
```

## Extras

Want the bot to function like others do parsing out Twitter links and displaying? (Thanks to Hoaas)

```
<@snackle> https://twitter.com/JSportsnet/status/348114324004413440
<@milo> @JSportsnet (John Shannon): Am told that Tippett's new deal is for 5 years, and he's "committed to the franchise where ever it ends up". (44m ago)
```

```
<@Hoaas> Should work on links to profiles aswell: https://twitter.com/EricFrancis
<@Bunisher> @EricFrancis (Eric Francis): HNIC-turned-Sportsnet analyst, Calgary Sun columnist...
```

Load the messageparser plugin:

```
/msg <bot> load MessageParser
/msg <bot> messageparser add global "https?://.*\.?twitter\.com/([^ \t/]+)(?:$|[ \t])" "echo ^ [Tweety twitter --info $1]"
/msg <bot> messageparser add global "https?://.*\.?twitter\.com/([A-Za-z0-9_]+)/status/([0-9]+)" "echo ^ [Tweety twitter --id $2]"
```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.
