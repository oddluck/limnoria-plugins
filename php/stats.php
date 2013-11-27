<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
?>
<head>
  <meta charset="utf-8">
  <title>Stats &middot; TriviaTime</title>
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
            <li class="active"><a href="stats.php">Stats</a></li>
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
      <h1>Stats</h1>
      <p>Stats are updated continuously and instantly.</p>
      <p>
      </p>
    </div>

    <div class="row">
      <div class="span6">
        <h2>Todays Top Scores</h2>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            $day = date('j');
            $month = date('m');
            $year = date('Y');

            if ($db) {
              $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE day=:day AND year=:year AND month=:month GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
              $q->execute(array(':day'=>$day, ':year'=>$year, ':month'=>$month));
              if ($q === false) {
                die("Error: database error: table does not exist\n");
              } else {
                $result = $q->fetchAll();
                foreach($result as $key=>$res) {
                  echo '<tr>';
                  echo '<td>' . ($key+1) . '</td>';
                  echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
                  echo '<td>' . number_format($res['points'],0) . '</td>';
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

      <?php
      $sqlClause = '';
      $day = date('N')-1;
      $week = new DateTime();
      $interval = new DateInterval('P'.$day.'D');
      $week->sub($interval);
      $interval = new DateInterval('P1D');
      for($i=0;$i<7;$i++) {
        if($i>0) {
          $sqlClause .= ' or ';
        }
        $sqlClause .= '(day=' . $week->format('j') . 
          ' and month=' . $week->format('n') .
          ' and year=' . $week->format('Y') . 
          ')';
      $week->add($interval);
      }
      ?>
      <div class="span6">
        <h2>Week Top Scores</h2>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if ($db) {
              $q = $db->query("SELECT username, sum(points_made) as points FROM triviauserlog WHERE $sqlClause GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
              if ($q === false) {
                die("Error: database error: table does not exist\n");
              } else {
                $result = $q->fetchAll();
                foreach($result as $key=>$res) {
                  echo '<tr>';
                  echo '<td>' . ($key+1) . '</td>';
                  echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
                  echo '<td>' . number_format($res['points'],0) . '</td>';
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
      <div class="span6">
        <h2>Month Top Scores</h2>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            $day = date('j');
            $month = date('m');
            $year = date('Y');

            if ($db) {
              $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year AND month=:month GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
              $q->execute(array(':year'=>$year, ':month'=>$month));
              if ($q === false) {
                die("Error: database error: table does not exist\n");
              } else {
                $result = $q->fetchAll();
                foreach($result as $key=>$res) {
                  echo '<tr>';
                  echo '<td>' . ($key+1) . '</td>';
                  echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
                  echo '<td>' . number_format($res['points'],0) . '</td>';
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
      <div class="span6">
        <h2>Year Top Scores</h2>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            $day = date('j');
            $month = date('m');
            $year = date('Y');

            if ($db) {
              $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
              $q->execute(array(':year'=>$year));
              if ($q === false) {
                die("Error: database error: table does not exist\n");
              } else {
                $result = $q->fetchAll();
                foreach($result as $key=>$res) {
                  echo '<tr>';
                  echo '<td>' . ($key+1) . '</td>';
                  echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
                  echo '<td>' . number_format($res['points'],0) . '</td>';
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

    <div class="footer">
      <p>&copy; Trivialand 2013 - <a target="_blank" href="https://github.com/tannn/TriviaTime">Github</a></p>
    </div>

  </div> <!-- /container -->

  <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="js/bootstrap.min.js"></script>

</body>
</html>
