import os.path

from supybot.setup import plugin_setup

REQUIREMENTS_PATH = os.path.join(os.path.dirname(__file__), "requirements.txt")

with open(REQUIREMENTS_PATH, "rt") as fd:
    install_requires = fd.read().split()

plugin_setup(
    'SpiffyTitles',
    install_requires=install_requires,
)

