Retrieve info from WolframAlpha based on your queries.

Forked from https://github.com/ormanya/Supyiel/tree/master/WolframAlpha

# Limnoria plugin for WolframAlpha

## Introduction

There are at least 3 plugins floating around for WA. One of the big differences with each variant from users
is the differences in output due to the verbosity from how WA answers questions. Some answers can be
10+ lines and easily flood a channel, either having the bot flood off or getting it banned from a channel.
WA's API also has some input options that can be handy, along with some verbose "error" messages that can help
the user, which the other plugins do not utilize. I wanted to use the getopts power and make some configuration
options to display the data in a more friendly manner.

Load the plugin:

```
@load WolframAlpha
```

[Create a 'Full Results' API key for WA](https://developer.wolframalpha.com/access) (free with signup)

Hit the 'Get an App ID' Button. Enter Name, Description, API: "Full Results API". Once getting this 'App ID', you will need to set it on your bot before things will work. See below:


```
@config plugins.WolframAlpha.apiKey APPID
```

Replace APPID with your 'App ID' created above and then reload the plugin:

```
@reload WolframAlpha
```

You should now be good to go...

Optional: There are some config variables that can be set for the bot. They mainly control output stuff.

```
@config search WolframAlpha
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
