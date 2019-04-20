Use the Bot Libre API (Free) https://www.botlibre.com/api.jsp
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
messageparser add (#channel/global) "(?i)(.*)(your_bot_nick)(.*)" "botlibre $1$3"
```
