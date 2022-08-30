from supybot.setup import plugin_setup

plugin_setup(
    'TVMaze',
    install_requires=[
        'pendulum',
        'requests',
    ],
)
