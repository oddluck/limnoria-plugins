<!DOCTYPE html>
<html lang="en">
<?php
  include('config.php');
  if(array_key_exists('username', $_GET)) {
    // Convert username to lowercase in irc
    $username = $_GET['username'];
    $ircLowerSymbols = array("\\"=>"|", "["=>"{", "]"=>"}", "~"=>"^");
    $usernameCanonical = strtr($username, $ircLowerSymbols);
    $usernameCanonical = strtolower($usernameCanonical);
  } else {
    $username = '';
    $usernameCanonical = '';
  }
?>
  <head>
    <meta charset="utf-8">
    <title>Players &middot; TriviaTime</title>
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <meta name="description" content="">
    <meta name="author" content="">

    <!-- Le styles -->
    <link href="css/bootstrap.css" rel="stylesheet">
    <style type="text/css">
      body {
        padding-top: 20px;
        padding-bottom: 60px;
      }

      /* Custom container */
      .container {
        margin: 0 auto;
        max-width: 1000px;
      }
      .container > hr {
        margin: 60px 0;
      }

      /* Customize the navbar links to be fill the entire space of the .navbar */
      .navbar .navbar-inner {
        padding: 0;
      }
      .navbar .nav {
        margin: 0;
        display: table;
        width: 100%;
      }
      .navbar .nav li {
        display: table-cell;
        width: 1%;
        float: none;
      }
      .navbar .nav li a {
        font-weight: bold;
        text-align: center;
        border-left: 1px solid rgba(255,255,255,.75);
        border-right: 1px solid rgba(0,0,0,.1);
      }
      .navbar .nav li:first-child a {
        border-left: 0;
        border-radius: 3px 0 0 3px;
      }
      .navbar .nav li:last-child a {
        border-right: 0;
        border-radius: 0 3px 3px 0;
      }
    </style>
    <link href="css/bootstrap-responsive.css" rel="stylesheet">

  </head>

  <body>

    <div class="container">

      <div class="masthead">
        <h3 class="muted">TriviaTime</h3>
        <div class="navbar">
          <div class="navbar-inner">
            <div class="container">
              <ul class="nav">
                <li><a href="index.php">Home</a></li>
                <li><a href="stats.php">Stats</a></li>
                <li class="active"><a href="user.php">Players</a></li>
                <li><a href="reports.php">Reports</a></li>
                <li><a href="about.php">About</a></li>
              </ul>
            </div>
          </div>
        </div><!-- /.navbar -->
      </div>

      <div class="hero-unit">
        <h1>Players</h1>
        <p>Show stats for users.</p>
        <p>
        </p>
      </div>
      <div class="row">
        <div class="span12">
            <h2>Search</h2>
            <form method="get">
                Username: <input name="username" value="<?php echo $username; ?>"></input>
                <input type="submit"></input>
            </form>
<?php
    if ($db) {
        $q = $db->prepare('select
            tl.username,
            sum(tl.points_made) as points,
            sum(tl.num_answered) as total
            from triviauserlog tl
            where tl.username_canonical like :username
            group by tl.username_canonical
            limit 20
            ');
        $q->execute(array(':username'=>'%'.$usernameCanonical.'%'));
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            foreach($result as $res) {
                if(is_null($res['username'])) {
                    echo "<div class='alert alert-error'>User not found.</div>";
                }
            }
        }
    } else {
        if(isset($err)) {
            die($err);
        }
        else {
            echo "<div class='alert alert-info'>Enter a username above to search for stats.</div>";
        }
    }
?>
        </div>
    </div>



      <div class="row">
        <div class="span12">
          <h2>Player data</h2>
            <table class="table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Total Points</th>
                  <th>Question Answered*</th>
                </tr>
              </thead>
              <tbody>
<?php

        if(isset($result)) {
            foreach($result as $res) {
                if(!is_null($res['username'])) {
                    echo '<tr>';
                    echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
                    echo '<td>' . number_format($res['points'],0) . '</td>';
                    echo '<td>' . number_format($res['total'],0) . '</td>';
                    echo '</tr>';
                }
            }
        }
?>
              </tbody>
            </table>
        </div>
      </div>

      <div class="row">
        <div class="span12">
            <p>* These stats do not include KAOS</p>
        </div>
      </div>
      <div class="footer">
        <p>&copy; Trivialand 2013 - <a target="_blank" href="https://github.com/tannn/TriviaTime">Github</a></p>
      </div>

    </div> <!-- /container -->

    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
    <script src="js/bootstrap.min.js"></script>

  </body>
</html>
