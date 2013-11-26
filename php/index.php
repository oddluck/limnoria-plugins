<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
?>
<head>
  <meta charset="utf-8">
  <title>Home &middot; TriviaTime</title>
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="description" content="">
  <meta name="author" content="">

  <!-- Le styles -->
  <link href="css/bootstrap.css" rel="stylesheet">
  <link href="css/triviatime.css" rel="stylesheet">
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
              <li class="active"><a href="index.php">Home</a></li>
              <li><a href="stats.php">Stats</a></li>
              <li><a href="user.php">Players</a></li>
              <li><a href="reports.php">Reports</a></li>
              <li><a href="about.php">About</a></li>
            </ul>
          </div>
        </div>
      </div><!-- /.navbar -->
    </div>

    <div class="hero-unit">
      <h1>TriviaTime</h1>
      <p>Get the latest stats for players and updates.</p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Latest questions asked</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Round #</th>
              <th>Channel</th>
              <th>Question</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if ($db) {
              $q = $db->query('SELECT asked_at, channel, round_num, question, line_num FROM triviagameslog ORDER BY id DESC LIMIT 10');
              if ($q === false) {
                die("Error: database error: table does not exist\n");
              } else {
                $result = $q->fetchAll();
                foreach($result as $res) {
                  echo '<tr>';
                  echo '<td>' . $res['round_num'] . '</td>';
                  echo '<td>' . $res['channel'] . '</td>';
                  echo '<td>' . $res['question'] . '</td>';
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

    <!-- Le javascript
    ================================================== -->
    <!-- Placed at the end of the document so the pages load faster -->
    <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
    <script src="js/bootstrap.min.js"></script>

</body>
</html>
