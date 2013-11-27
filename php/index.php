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
      <h1>Home</h1>
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
              <th>Question #</th>
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
                  echo '<td class="breakable">' . $res['question'] . '</td>';
                  echo '<td>' . $res['line_num'] . '</td>';
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
