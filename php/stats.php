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
                <li class="active"><a href="stats.php">Stats</a></li>
                <li><a href="user.php">Players</a></li>
                <li><a href="reports.php">Reports</a></li>
                <li><a href="about.php">About</a></li>
              </ul>
            </div>
          </div>
        </div><!-- /.navbar -->
      </div>

      <div class="hero-unit">
        <h1>Stats</h1>
        <p>Stats are updated continuously and instantly.</p>
        <p>
        </p>
      </div>


      <div class="row">

                <?php /*
                    if ($db) {
                        $q = $db->query('SELECT username, sum(points_made) as points FROM triviauserlog GROUP BY username ORDER BY points DESC LIMIT 10');
                        if ($q === false) {
                            die("Error: database error: table does not exist\n");
                        } else {
                            $result = $q->fetchAll();

                            foreach($result as $key=>$res) {

                                echo '<tr>';
                                echo '<td>' . ($key+1) . '</td>';
                                echo '<td>' . $res['username'] . '</td>';
                                echo '<td>' . $res['points'] . '</td>';
                                echo '</tr>';
                            }
                        }
                    } else {
                        die($err);
                    }
                    */
                ?>
        <div class="span12">
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
                        $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE day=:day AND year=:year AND month=:month GROUP BY username ORDER BY points DESC LIMIT 10");
                        $q->execute(array(':day'=>$day, 'year'=>$year, 'month'=>$month));
                        if ($q === false) {
                            die("Error: database error: table does not exist\n");
                        } else {
                            $result = $q->fetchAll();
                            foreach($result as $key=>$res) {
                                echo '<tr>';
                                echo '<td>' . ($key+1) . '</td>';
                                echo '<td>' . $res['username'] . '</td>';
                                echo '<td>' . $res['points'] . '</td>';
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
        <div class="span12">
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
        $q = $db->query("SELECT username, sum(points_made) as points FROM triviauserlog WHERE $sqlClause GROUP BY username ORDER BY points DESC LIMIT 10");
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            foreach($result as $key=>$res) {
                echo '<tr>';
                echo '<td>' . ($key+1) . '</td>';
                echo '<td>' . $res['username'] . '</td>';
                echo '<td>' . $res['points'] . '</td>';
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
                        $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year AND month=:month GROUP BY username ORDER BY points DESC LIMIT 10");
                        $q->execute(array('year'=>$year, 'month'=>$month));
                        if ($q === false) {
                            die("Error: database error: table does not exist\n");
                        } else {
                            $result = $q->fetchAll();
                            foreach($result as $key=>$res) {
                                echo '<tr>';
                                echo '<td>' . ($key+1) . '</td>';
                                echo '<td>' . $res['username'] . '</td>';
                                echo '<td>' . $res['points'] . '</td>';
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
                        $q = $db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year GROUP BY username ORDER BY points DESC LIMIT 10");
                        $q->execute(array('year'=>$year));
                        if ($q === false) {
                            die("Error: database error: table does not exist\n");
                        } else {
                            $result = $q->fetchAll();
                            foreach($result as $key=>$res) {
                                echo '<tr>';
                                echo '<td>' . ($key+1) . '</td>';
                                echo '<td>' . $res['username'] . '</td>';
                                echo '<td>' . $res['points'] . '</td>';
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


