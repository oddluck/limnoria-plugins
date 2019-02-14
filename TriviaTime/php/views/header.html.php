<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title><?php echo $viewVars['title']; ?>TriviaTime</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="">
  <meta name="author" content="">

  <link href="<?php echo $container->config['baseFolder']; ?>/css/bootstrap.css" rel="stylesheet">
  <link href="<?php echo $container->config['baseFolder']; ?>/css/triviatime.css" rel="stylesheet">
  <link href="<?php echo $container->config['baseFolder']; ?>/css/bootstrap-responsive.css" rel="stylesheet">
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
        <a href="<?php echo $container->router->generate('home'); ?>" class="brand">TriviaTime</a>
        <div class="nav-collapse collapse">
          <?php
          // Handle username information in nav
          if($container->login->isLoggedIn() && !is_null($container->login->getUser())) {
            $user = $container->login->getUser();
            echo '<p class="navbar-text pull-right">
                    Logged in as ';
            echo htmlspecialchars($user->getUsername());
            echo ' (<a class="navbar-link" href="' . $container->router->generate('logout') . '">logout</a>)';
            echo '</p>';
          }
          ?>
          <ul class="nav">
            <?php
            $currentPageName = '';
            $route = $container->router->matchCurrentRequest();
            if($route) {
              $currentPageName = $route->getName();
            }
            ?>
            <li<?php if($currentPageName=='home') { echo ' class="active"'; } ?>>
              <a href="<?php echo $container->router->generate('home'); ?>">Home</a>
            </li>
            <li<?php if($currentPageName=='stats') { echo ' class="active"'; } ?>>
              <a href="<?php echo $container->router->generate('stats'); ?>">Stats</a>
            </li>
            <li<?php if($currentPageName=='search') { echo ' class="active"'; } ?>>
              <a href="<?php echo $container->router->generate('search'); ?>">Players</a>
            </li>
            <li<?php if($currentPageName=='reports') { echo ' class="active"'; } ?>>
              <a href="<?php echo $container->router->generate('reports'); ?>">Reports</a>
            </li>
            <li<?php if($currentPageName=='about') { echo ' class="active"'; } ?>>
              <a href="<?php echo $container->router->generate('about'); ?>">About</a>
            </li>
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

    $error = $container->getError();
    if(!is_null($error)) {
      echo "<div class='alert alert-error' style='margin-top:10px;'>$error</div>";
    }
    $container->clearError();
    ?>
