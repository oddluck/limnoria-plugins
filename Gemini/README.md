GoogleAI Gemini Chat Plugin

This plugin is under development and probably shouldn't be used by anyone...

Get an API key from https://aistudio.google.com/app/apikey

@config plugins.gemini.api_key YOUR_KEY_HERE

system prompt:

@config plugins.gemini.prompt "You are $botnick the IRC bot. Be brief, helpful"

^^ Configurable per channel, etc. get creative

@config list plugins.gemini

^^ Please take a look at the various options and configure stuff before you do anything.

@chat <text>

^^ Command to send text to the chatgpt API

@messageparser add "(?i)(.*BOT_NICK_HERE)(?:[:]*)(.*)" "chat $1$2"

^^ replace BOT_NICK_HERE with your bot nick and add automatic replies to nick mentions
