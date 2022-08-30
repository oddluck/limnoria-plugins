from supybot.setup import plugin_setup

plugin_setup(
    'NHL',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
