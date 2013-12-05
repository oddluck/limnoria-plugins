<?php

?><!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title><?php echo $viewVars['title']; ?>TriviaTime</title>
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
            <li<?php if($viewVars['currentPage']=='index.php') { echo ' class="active"'; } ?>><a href="index.php">Home</a></li>
            <li<?php if($viewVars['currentPage']=='stats.php') { echo ' class="active"'; } ?>><a href="stats.php">Stats</a></li>
            <li<?php if($viewVars['currentPage']=='user.php') { echo ' class="active"'; } ?>><a href="user.php">Players</a></li>
            <li<?php if($viewVars['currentPage']=='reports.php') { echo ' class="active"'; } ?>><a href="reports.php">Reports</a></li>
            <li<?php if($viewVars['currentPage']=='about.php') { echo ' class="active"'; } ?>><a href="about.php">About</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div><!-- /.navbar -->
  <div class="container">
