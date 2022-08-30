from supybot.setup import plugin_setup

plugin_setup(
    'CBB',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
