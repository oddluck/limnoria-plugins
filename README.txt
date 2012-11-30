Overview:
Supply a username and get the latest tweet(s). Or an ID to a tweet. Or search on twitter. Or view latest trends. Does not require a user account or apikey or anything like that. Just point and shoot.
This plugin does NOT relay tweets in real time. It only fetches data from Twitter when commands are called.

This is forked from Hoaas' Tweety plugin at: http://github.com/Hoaas/Supybot-Plugins to support Twitter API v1.1 and add in a few features:

Instructions:
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

Examples:
12:38:02 <@Hoaas> !twitter cnn
12:38:03 <@Bunisher> @CNN (CNN): RT @AC360 Because of #AC360's investigation, Senate Finance Committee is demanding answers from a charity for disabled vets. Find out why 8p (10 hours ago)

12:38:48 <@Hoaas> !twitter --num 5 RealTimeWWII
12:38:49 <@Bunisher> @RealTimeWWII (WW2 Tweets from 1940): All French ships left in Mediterranean being ordered to attack UK warships on sight, thanks to yesterday's British attack at Mers-El-Kébir. (1 hour ago)
12:38:51 <@Bunisher> @RealTimeWWII (WW2 Tweets from 1940): After negotiation, French ships at Alexandria have peacefully surrendered to Royal Navy- they've yet to hear of attack at Mers-el-Kébir. (16 hours ago)
12:38:54 <@Bunisher> @RealTimeWWII (WW2 Tweets from 1940): As part of peace treaty, France must give Madagascar to Germany, so that all European Jews can be deported there: http://t.co/GiRq06O1 (15 hours ago)
12:38:55 <@Bunisher> @RealTimeWWII (WW2 Tweets from 1940): 6.05PM British ships have stopped firing. 1,297 French sailors are dead. 4th largest Navy in the world is decimated. http://t.co/8Iob4NlK (17 hours ago)
12:38:56 <@Bunisher> @RealTimeWWII (WW2 Tweets from 1940): Trapped at anchor, French ships can't evade brutal shelling; only 2 in range to fire back. They can do nothing but die. http://t.co/6NDT5hDp (17 hours ago)

12:39:43 <@Hoaas> !twitter --id 220454083016921088
12:39:45 <@Bunisher> @TheScienceGuy (Bill Nye): The Higgs is real !?! The results are good to 5 standard deviations. Yikes. Whoa. Wow. This could change the world... (51 minutes ago)

12:40:05 <@Hoaas> !twitter --info TheScienceGuy
12:40:07 <@Bunisher> @TheScienceGuy (Bill Nye): http://billnye.com Science Educator seeks to change the world... 29 friends, 319377 followers. Los Angeles, CA, USA

