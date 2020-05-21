Search for YouTube videos and return link + info. 

Enable the [YouTube Data API](https://console.developers.google.com/apis/library/youtube.googleapis.com). Set your [API Key](https://console.cloud.google.com/apis/credentials) using the command below.

`config plugins.youtube.developerkey your_key_here`

`config plugins.youtube.template` - set the reply template.

Default template:

`$logo :: $link :: $title :: Duration: $duration :: Views: $views :: Uploader: $uploader :: Uploaded: $published :: $likes likes :: $dislikes dislikes :: $favorites favorites :: $comments comments`