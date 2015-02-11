#Configuration
## Setting up the plugin
1. Download [Supybot][]
2. Download TriviaTime and place it into the plugins folder
3. Load TriviaTime
4. Configure your question file and database location in config.py or with commands
5. Use 'addquestionfile [filename]' command to load questions, the argument is optional

## IMPORTANT: How to update
1. Stop the game, if it is currently in progress.
2. Backup your entire Supybot directory. The most important file needed is the database in /storage/, but it's best to be safe.
3. Unload TriviaTime. Since you are unloading the plugin, you will not have to restart or kill your bot.
4. Do not delete any files in TriviaTime/storage during this process (aside from samplequestions, if you wish).
5. Copy over the changed files.
    * Version v1.2 files changed **README.md, plugin.py, config.py, __init__.py** (changes to config adds new value, removes another)
6. If there were any changes to the database, they should be updated automatically. Otherwise, further instructions for updating that version will appear here.
7. If config.py was changed, you will need to manually add your desired values again. You can compare the previous file (the backup) to the new file. (v1.1)
8. Load TriviaTime again. If you followed the instructions correctly, you won't have an error.
9. If everything went smoothly, you have now sucessfully updated the plugin to the latest version. Use .info to verify you are on the latest version.

## Question editing tools
TriviaTime was designed to make editing, deleting, and adding questions a breeze, for both administrators and players. However, due to the amount of tools available, it can be complicated to new players. Instructions on these tools are available [here][].

#How to set up the website

## Download and Install
1. Install PHP (for PDO) and PHP-SQLite.
2. Configure config.php to point to your TriviaTime database in the plugin/TriviaTime/Storage/db folder
3. mod_rewrite should be enabled for Apache servers (nginx servers may be a bit different)

## Setting up permissions for SQLite

In order to use the website to delete/accept edits, reports, new questions, and deletes, you will need to set the proper permissions for the SQLite db, called 'trivia.db' by default. The default location for the database is inside of the supybot's directory, with the .conf file, inside of plugins/TriviaTime/storage/db.

PHP's PDO requires that the user that PHP is run under has write access to the folder that the db is stored in. For this reason I would suggest moving the database to its own folder, which the webservers user has write access.

I would recommend either creating a new group and adding the user that runs supybot and the webservers user to it, or changing the permissions of the database so that the group who owns it is the webserver, and the user who owns it is the user who runs supybot. After doing that, changing permissions to 775 will allow the group who owns the file to write to the database.

  [Supybot]: http://sourceforge.net/projects/supybot/
  [here]: http://trivialand.org/
