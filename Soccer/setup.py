from supybot.setup import plugin_setup

plugin_setup(
    'Soccer',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
