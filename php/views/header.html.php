<!DOCTYPE html>
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
    <!-- HTML5 shim, for IE6-8 support of HTML5 elements -->
    <!--[if lt IE 9]>
      <script src="js/html5shiv.min.js"></script>
    <![endif]-->
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
          <?php
          // Handle username information in nav
          if($container->login->isLoggedIn() && !is_null($container->login->getUser())) {
            $user = $container->login->getUser();
            echo '<p class="navbar-text pull-right">
                    Logged in as ';
            echo $user->getUsername();
            echo ' (<a class="navbar-link" href="logout.php">logout</a>)';
            echo '</p>';
          }
          ?>
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
    <?php
    $notice = $container->getNotice();
    if(!is_null($notice)) {
      echo "<div class='alert alert-info' style='margin-top:10px;'>$notice</div>";
    }
    $container->clearNotice();
    ?>
