from supybot.setup import plugin_setup

plugin_setup(
    'Geo',
    install_requires=[
        'geoip2',
    ],
)
