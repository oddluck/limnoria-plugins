Use the OpenAI ChatGPT API

This plugin is under development and probably shouldn't be used by anyone...

Get an API key from https://platform.openai.com/account/api-keys (free)

@config plugins.chatgpt.api_key YOUR_KEY_HERE

@config plugins.chatgpt.prompt "You are $botnick the IRC bot. Be brief, helpful"

^^ Configurable per channel, etc. get creative

@chat <text>

^^ Command to send text to the chatgpt API

@messageparser add "(?i)(.*BOT_NICK_HERE.*)" "chat $1"

^^ replace BOT_NICK_HERE with your bot nick and add automatic replies to nick mentions
