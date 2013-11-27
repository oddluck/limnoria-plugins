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
        <span class="brand">TriviaTime</span>
        <div class="nav-collapse collapse">
          <ul class="nav">
            <li class="active"><a href="index.php">Home</a></li>
            <li><a href="stats.php">Stats</a></li>
            <li><a href="user.php">Players</a></li>
            <li><a href="reports.php">Reports</a></li>
            <li><a href="about.php">About</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div><!-- /.navbar -->
  <div class="container">
    <div class="hero-unit">
      <h1>About Us</h1>
      <p>TriviaTime is a trivia word game meant for irc. The source code is on <a target="_blank" href="https://github.com/tannn/TriviaTime">Github</a>, be sure to check it out.</p>
      <p>We are <a href="irc://irc.freenode.net/#trivialand">#trivialand</a> on Freenode. Come join us!</p>
    </div>
    <div class="footer">
      <p>&copy; Trivialand 2013 - <a target="_blank" href="https://github.com/tannn/TriviaTime">Github</a></p>
    </div>

  </div> <!-- /container -->

  <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="js/bootstrap.min.js"></script>

</body>
</html>
