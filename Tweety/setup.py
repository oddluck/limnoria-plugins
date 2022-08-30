from supybot.setup import plugin_setup

plugin_setup(
    'Tweety',
    install_requires=[
        'requests',
        'requests_oauthlib',
    ],
)
