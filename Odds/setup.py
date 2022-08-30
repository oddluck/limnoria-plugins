from supybot.setup import plugin_setup

plugin_setup(
    'Odds',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
