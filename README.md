 Configuration
## Setting up plugin
1. Download [Supybot][]
2. Download TriviaTime and place it into the plugins folder
3. Load TriviaTime
4. Configure your question file and database location in config.py or with commands
5. Use 'addquestionfile [filename]' command to load questions, the argument is optional

## Setting up PHP
1. Download PHP and PHP-MySQL (for PDO)
2. Configure config.php to point to your TriviaTime database in the plugin/TriviaTime/Storage/db folder

## How to update
1. Stop the game, if it is currently in progress.
2. Unload TriviaTime
3. Move files into plugins/TriviaTime directory. Do not delete any files in TriviaTime/storage (aside from samplequestions, if you wish). 
4. If there were any changes to the database or config, they should be updated automatically. Otherwise, further instructions for updating that version will appear here.
5. Load TriviaTime
6. If everything went smoothly, you have now sucessfully updated the plugin to the latest version.

## Important - Setting up permissions for sqlite (website)
If you do not plan on using the webpage you can ignore this.

In order to use the website to delete/accept edits, reports, new questions, and deletes, you will need to set the proper permissions for the sqlite db, called 'trivia.db' by default. The default location for the database is inside of the supybot's directory, with the .conf file, inside of plugins/TriviaTime/storage/db.

PHP's PDO requires that the user that php is run under has write access to the folder that the db is stored in. For this reason I would suggest moving the database to its own folder, which the webservers user has write access.

I would recommend either creating a new group and adding the user that runs supybot and the webservers user to it, or changing the permissions of the database so that the group who owns it is the webserver, and the user who owns it is the user who runs supybot. After doing that, changing permissions to 775 will allow the group who owns the file to write to the database.

  [Supybot]: http://sourceforge.net/projects/supybot/
