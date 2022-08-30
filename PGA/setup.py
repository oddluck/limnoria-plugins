from supybot.setup import plugin_setup

plugin_setup(
    'PGA',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
