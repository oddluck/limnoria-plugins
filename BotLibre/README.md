Retrieve responses from the Bot Libre API.

## BotLibre

Register for an account: https://www.botlibre.com/api.jsp (FREE)

```
config plugins.BotLibre.application (YOUR_APP_KEY_HERE)
config plugins.BotLibre.instance (BOT_INSTANCE_ID_HERE)
```
make the bot respond to invalid commands:
```
config plugins.BotLibre.invalidcommand True
```
or:
```
config channel #channel plugins.BotLibre.invalidcommand True
```
Use messapeparser to make the bot respond to messages containing its nick:
```
messageparser add "(?i)(.*)([echo $botnick])(.*)" "echo [botlibre $1$3]"
```
