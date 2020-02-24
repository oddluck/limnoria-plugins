Retrieve current time and time zone information for various locations.

# Limnoria plugin for WorldTime

Forked from https://github.com/reticulatingspline/WorldTime

## Introduction

A user contacted me about making some type of plugin to display local time around the world.
Utilizing Python's TimeZone database and google, it was pretty easy to throw together.

## Install

```
pip install -r requirements.txt 
```

or if you don't have or don't want to use root,

```
pip install -r requirements.txt --user
```

Next, load the plugin:

```
/msg bot load WorldTime
```

Enable Google [Geocoding](https://console.cloud.google.com/apis/library/geocoding-backend.googleapis.com) and [Time Zone](https://console.cloud.google.com/apis/library/timezone-backend.googleapis.com) APIs. Set your [API Key](https://console.cloud.google.com/apis/credentials) using the command below

```
/msg bot config plugins.worldtime.mapsapikey <your_key_here>
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
