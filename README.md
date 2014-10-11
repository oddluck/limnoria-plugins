[![Build Status](https://travis-ci.org/reticulatingspline/WorldTime.svg?branch=master)](https://travis-ci.org/reticulatingspline/WorldTime)

# Limnoria plugin for WorldTime

## Introduction

A user contacted me about making some type of plugin to display local time around the world.
Utilizing Python's TimeZone database and google, it was pretty easy to throw together.

## Install

You will need a working Limnoria bot on Python 2.7 for this to work.

Go into your Limnoria plugin dir, usually ~/supybot/plugins and run:

```
git clone https://github.com/reticulatingspline/WorldTime
```

To install additional requirements, run:

```
pip install -r requirements.txt 
```

Next, load the plugin:

```
/msg bot load WorldTime
```

## Example Usage

```
<spline> @worldtime New York, NY
<myybot> New York, NY, USA :: Current local time is: Sat, 09:38 (Eastern Daylight Time)
<spline> @worldtime 90210
<myybot> Beverly Hills, CA 90210, USA :: Current local time is: Sat, 06:38 (Pacific Daylight Time)

```

## About

All of my plugins are free and open source. When I first started out, one of the main reasons I was
able to learn was due to other code out there. If you find a bug or would like an improvement, feel
free to give me a message on IRC or fork and submit a pull request. Many hours do go into each plugin,
so, if you're feeling generous, I do accept donations via Amazon or browse my [wish list](http://amzn.com/w/380JKXY7P5IKE).

I'm always looking for work, so if you are in need of a custom feature, plugin or something bigger, contact me via GitHub or IRC.
