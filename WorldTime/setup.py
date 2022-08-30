from supybot.setup import plugin_setup

plugin_setup(
    'WorldTime',
    install_requires=[
        'pendulum',
    ],
)
