from supybot.setup import plugin_setup

plugin_setup(
    'CFB',
    install_requires=[
        'beautifulsoup4',
        'pendulum',
        'requests',
    ],
)
