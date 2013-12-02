<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
include('includes/storage.php');
try {
    $storage = new Storage($config['dbLocation']);
} catch(StorageException $e) {

}
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
        <?php
        $result = array();
        try {
          $result = $storage->getDayTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php">View all</a></p>
      </div>

      <div class="span6">
        <h2>Week Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getWeekTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=w">View all</a></p>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Month Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getMonthTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=m">View all</a></p>
      </div>
      <div class="span6">
        <h2>Year Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getYearTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            $storage->close();
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=y">View all</a></p>
      </div>
    </div>

    <div class="footer">
      <p>&copy; Trivialand 2013 - <a target="_blank" href="https://github.com/tannn/TriviaTime">GitHub</a></p>
    </div>

  </div> <!-- /container -->

  <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="js/bootstrap.min.js"></script>

</body>
</html>
