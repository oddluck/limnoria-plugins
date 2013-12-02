<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
?>
<head>
  <meta charset="utf-8">
  <title>About &middot; TriviaTime</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="">
  <meta name="author" content="">

  <link href="css/bootstrap.css" rel="stylesheet">
  <link href="css/triviatime.css" rel="stylesheet">
  <link href="css/bootstrap-responsive.css" rel="stylesheet">

</head>

<body>
  <div class="navbar navbar-inverse navbar-fixed-top">
    <div class="navbar-inner">
      <div class="container">
        <button class="btn btn-navbar collapsed" data-toggle="collapse" data-target=".nav-collapse" type="button">
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
          <span class="icon-bar"></span>
        </button>
        <a href="index.php" class="brand">TriviaTime</a>
        <div class="nav-collapse collapse">
          <ul class="nav">
            <li><a href="index.php">Home</a></li>
            <li><a href="stats.php">Stats</a></li>
            <li><a href="user.php">Players</a></li>
            <li><a href="reports.php">Reports</a></li>
            <li class="active"><a href="about.php">About</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div><!-- /.navbar -->
  <div class="container">
    <div class="hero-unit">
        <h1>About TriviaTime</h1>
        <p>We are <a href="irc://irc.freenode.net/#trivialand">#trivialand</a> on Freenode. Come join us!</p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>About</h2>
        <p>TriviaTime is a feature-packed trivia plugin developed by the Trivialand channel on Freenode, written in Python for <a href="https://github.com/jamessan/Supybot">Supybot</a> with a built-in website generator. Be the first to answer the question to score points. On KAOS, it's a team effort to get all the answers before the time runs out. As you play you'll earn badges and level up.</p>
      </div>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Source</h2>
        <p>The source code is available on <a target="_blank" href="https://github.com/tannn/TriviaTime">GitHub</a>, be sure to check it out.
          Fork us and contribute!</p>
      </div>
    </div>
    <div class="footer">
      <p>&copy; Trivialand 2013 - <a target="_blank" href="https://github.com/tannn/TriviaTime">GitHub</a></p>
    </div>

  </div> <!-- /container -->

  <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="js/bootstrap.min.js"></script>

</body>
</html>
