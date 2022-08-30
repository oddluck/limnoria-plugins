from supybot.setup import plugin_setup

plugin_setup(
    'TextArt',
    install_requires=[
        'beautifulsoup4',
        'numpy',
        'pexpect',
        'pillow',
        'pyimgur',
        'requests',
    ],
)
