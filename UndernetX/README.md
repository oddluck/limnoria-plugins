Logs into UnderNet's X Service.

Python3 compatible. Forked from https://github.com/IotaSpencer/supyplugins/tree/master/UndernetX

## Setup

* configure the plugin by setting `plugins.UndernetX.auth.password` and `plugins.UndernetX.auth.username`

* If you want your bot to /mode +x on login, make sure to set
  `plugins.UndernetX.modeXonID` to `True` if it isn't already.

* To prevent channel joins before authorized with X set
  `plugins.UndernetX.auth.noJoinsUntilAuthed` to `True` if it isn't already.
