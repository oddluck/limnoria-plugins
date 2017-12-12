[![Build Status](https://travis-ci.org/reticulatingspline/WolframAlpha.svg?branch=master)](https://travis-ci.org/reticulatingspline/WolframAlpha)

# Limnoria plugin for WolframAlpha

## Introduction

There are at least 3 plugins floating around for WA. One of the big differences with each variant from users
is the differences in output due to the verbosity from how WA answers questions. Some answers can be
10+ lines and easily flood a channel, either having the bot flood off or getting it banned from a channel.
WA's API also has some input options that can be handy, along with some verbose "error" messages that can help
the user, which the other plugins do not utilize. I wanted to use the getopts power and make some configuration
options to display the data in a more friendly manner.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/WolframAlpha
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

or if you don't have or don't want to use root, 

```
pip install -r requirements.txt --user
```

Next, load the plugin:

```
/msg bot load WolframAlpha
```

[Fetch an API key for WA](http://products.wolframalpha.com/developers/) by signing up (free).
Once getting this key, you will need to set it on your bot before things will work.
Reload once you perform this operation to start using it.

```
/msg bot config plugins.WolframAlpha.apiKey APIKEY
```

Now, reload the bot and you should be good to go:

```
/msg bot reload WolframAlpha
```

Optional: There are some config variables that can be set for the bot. They mainly control output stuff.

```
/msg bot config search WolframAlpha
```

## Example Usage

```
<spline> @wolframalpha 2+2
<myybot> Input :: 2+2
<myybot> Result :: 4
<myybot> Number name :: four
<myybot> Manipulatives illustration ::  | + |  |  =  |  2 |  | 2 |  | 4
<spline> @wolframalpha --shortest 2+2
<myybot> 2+2 :: 4
```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.
