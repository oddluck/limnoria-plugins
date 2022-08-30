from supybot.setup import plugin_setup

plugin_setup(
    'Corona',
    install_requires=[
        'beautifulsoup4',
        'requests',
    ],
)
