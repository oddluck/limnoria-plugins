<!DOCTYPE html>
<html lang="en">
<?php
  include('config.php');
  if(array_key_exists('username', $_GET)) {
    $username = strtolower($_GET['username']);
  } else {
    $username = '';
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
                Username: <input name="username"></input>
                <input type="submit"></input>
            </form>
        </div>
    </div>



      <div class="row">
        <div class="span12">
          <h2>Player data</h2>
            <table class="table">
              <thead>
                <tr>
                  <th>Username</th>
                  <th>Average Time/Question*</th>
                  <th>Average Points/Question*</th>
                  <th>Total Points</th>
                  <th>Question Answered*</th>
                  <th>Edits Made</th>
                  <th>Edits Accepted</th>
                </tr>
              </thead>
              <tbody>
<?php
    if ($db) {
        $q = $db->prepare('select
            sum(tl2.t * (tl2.n / 
                (select sum(num_answered) 
                    from triviauserlog 
                    where username=:username))
                ) as count,
            sum(tl2.p * (tl2.n / 
                (select sum(num_answered) 
                    from triviauserlog 
                    where username=:username))
                ) as score,
            (select sum(points_made) from triviauserlog t3 where lower(username)=:username) as points,
            (select sum(num_answered) from triviauserlog t4 where lower(username)=:username) as q_asked,
            (select num_reported from triviausers where lower(username)=:username) as num_r,
            (select num_accepted from triviausers where lower(username)=:username) as num_a
            from (select 
                    tl3.id as id2, 
                    tl3.average_time * 1.0 as t, 
                    tl3.average_score * 1.0 as p, 
                    tl3.num_answered * 1.0 as n 
                    from triviauserlog tl3
                ) tl2
            inner join triviauserlog tl
            on tl.username=:username
            and id=tl2.id2
            ');
        $q->execute(array('username'=>$username));
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            foreach($result as $res) {
                echo '<tr>';
                echo '<td>' . $username . '</td>';
                echo '<td>' . $res['count'] . '</td>';
                echo '<td>' . $res['score'] . '</td>';
                echo '<td>' . $res['points'] . '</td>';
                echo '<td>' . $res['q_asked'] . '</td>';
                echo '<td>' . $res['num_r'] . '</td>';
                echo '<td>' . $res['num_a'] . '</td>';
                echo '</tr>';
            }
        }
    } else {
        die($err);
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
        <p>&copy; Trivialand 2013 - <a href="https://github.com/tannn/TriviaTime">github</a></p>
      </div>

    </div> <!-- /container -->

    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
    <script src="js/bootstrap.min.js"></script>

  </body>
</html>

<!--
select
sum(tl2.t * (tl2.n / (select sum(num_answered) from triviauserlog where username='rootcoma')))
from (select tl3.id as id2, tl3.average_time * 1.0 as t, tl3.num_answered * 1.0 as n
    from triviauserlog tl3
    ) tl2
inner join triviauserlog tl
on tl.username='rootcoma'
and id=tl2.id2
-->