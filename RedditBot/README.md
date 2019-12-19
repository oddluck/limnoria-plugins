needs nltk and punkt installed

nltk.download('punkt')

This plugin downloads comment data from subreddits to generate chat replies via markov chains.

```redditbot csv [subreddit1] [subreddit2] [etc.]``` - download data from subreddits as csv files

```redditbot model [channel] [subreddit1] [subreddit2] [etc.]``` - generate channel markov model from subreddit csv files

```config channel [channel] plugins.redditbot.enable``` - Enable RedditBot for the channel

```config channel [channel] plugins.redditbot.probability``` - Probability of reply on channel message 0.0 - 1.0

```config channel [channel] plugins.redditbot.probabilityWhenAddressed``` - Probability of reply on channel message containing bot's nick. 0.0 - 1.0
