Use the Bot Libre API (Free) https://www.botlibre.com/api.jsp

config plugins.BotLibre.application (YOUR_APP_KEY_HERE)<br>
config plugins.BotLibre.instance (BOT_INSTANCE_ID_HERE)

Use messapeparser to make the bot respond to messages containing its nick:
```
messageparser add (#channel/global) "(?i)(.*)(your_bot_nick)(.*)" "botlibre $1$3"
```
