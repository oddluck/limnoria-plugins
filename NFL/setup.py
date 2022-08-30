from supybot.setup import plugin_setup

plugin_setup(
    'NFL',
    install_requires=[
        'pendulum',
        'roman_numerals',
    ],
)
