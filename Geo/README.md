Provides geographical information from an IP address, hostmask, nick (must be in channel), or URL.

Forked from https://github.com/SpiderDave/spidey-supybot-plugins/tree/master/Plugins/Geo

Requires GeoIP2-python:
```
pip install geoip2
```

Requires a MaxMind license key to update the database.

Sign up for a MaxMind account at https://www.maxmind.com/en/geolite2/signup

Create a license key at https://www.maxmind.com/en/accounts/current/license-key

```
config plugins.geo.licenseKey <Your_Key_Here>
```

Usage:
```
geo <nick/host/ip> (geolocate <nick> (must be in channel) <host>, or <ip> address
```
```
geo update (force update of geoip database)
```

If you wish to manually update the geoip database, plugin looks for the file at <bot_directory>/data/geo/GeoLite2-City.mmdb
