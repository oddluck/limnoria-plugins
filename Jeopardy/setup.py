from supybot.setup import plugin_setup

plugin_setup(
    'Jeopardy',
    install_requires=[
        'beautifulsoup4',
        'ftfy',
        'jinja2',
        'requests',
        'textdistance',
        'unidecode',
    ],
)
