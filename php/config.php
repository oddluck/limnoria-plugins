<?php
/**
 * Change db location here to point to your database from the bot
 */
  $dbLocation = "trivia.db"; // eg "/home/trivia/trivia.db"
  $db = new PDO('sqlite:' . $dbLocation);
?>
