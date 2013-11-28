<!DOCTYPE html>
<?php
include('config.php');
include('includes/storage.php');
try {
    $storage = new Storage($config['dbLocation']);
} catch(StorageException $e) {

}
$username = '';
$usernameCanonical = '';

if(array_key_exists('username', $_GET)) {
  // Convert username to lowercase in irc
  $username = $_GET['username'];
  $ircLowerSymbols = array("\\"=>"|", "["=>"{", "]"=>"}", "~"=>"^");
  $usernameCanonical = strtr($username, $ircLowerSymbols);
  $usernameCanonical = strtolower($usernameCanonical);
}

$lastSeen = 'Never';

function emptyResult() {
  $result = array();
  $result['usrname'] = "Not found";
  $result['count'] = 0;
  $result['score'] = 0;
  $result['points'] = 0;
  $result['q_asked'] = 0;
  $result['num_e'] = 0;
  $result['num_e_accepted'] = 0;
  $result['num_q'] = 0;
  $result['num_q_accepted'] = 0;
  $result['num_r'] = 0;
  $result['highest_streak'] = 0;
  return $result;
}

function secondsToTime($inputSeconds) {

  $secondsInAMinute = 60;
  $secondsInAnHour  = 60 * $secondsInAMinute;
  $secondsInADay    = 24 * $secondsInAnHour;

  // extract days
  $days = floor($inputSeconds / $secondsInADay);

  // extract hours
  $hourSeconds = $inputSeconds % $secondsInADay;
  $hours = floor($hourSeconds / $secondsInAnHour);

  // extract minutes
  $minuteSeconds = $hourSeconds % $secondsInAnHour;
  $minutes = floor($minuteSeconds / $secondsInAMinute);

  // extract the remaining seconds
  $remainingSeconds = $minuteSeconds % $secondsInAMinute;
  $seconds = ceil($remainingSeconds);

  // return the final array
  $obj = array(
      'd' => (int) $days,
      'h' => (int) $hours,
      'm' => (int) $minutes,
      's' => (int) $seconds,
  );
  return $obj;
}

$userProfile = emptyResult();

if ($username != '') {
  try {
    $profileResult = $storage->getUserProfileInformation($usernameCanonical);
    if(count($profileResult) > 0) {
      if(array_key_exists('usrname', $profileResult[0])) {
        if(!is_null($profileResult[0]['usrname'])) {
          $userProfile = $profileResult[0];
        }
      }
    }
    $lastSeenQuery = $storage->getTimeSinceLastPlayed($usernameCanonical);
    if(count($lastSeenQuery) > 0) {
      if(array_key_exists('last_updated', $lastSeenQuery[0])) {
        if(!is_null($lastSeenQuery[0]['last_updated'])) {
          $lastSeenSeconds = strtotime("now") - $lastSeenQuery[0]['last_updated'];
          $lastSeenObj = secondsToTime($lastSeenSeconds);
          $lastSeen = '';
          if($lastSeenObj["d"] > 0) {
            $lastSeen .= $lastSeenObj["d"] . ' days ';
          }
          if($lastSeenObj["h"] > 0) {
            $lastSeen .= $lastSeenObj["h"] . ' hours ';
          }
          if($lastSeenObj["m"] > 0) {
            $lastSeen .= $lastSeenObj["m"] . ' mins ';
          }
          if($lastSeenObj["s"] > 0) {
            $lastSeen .= $lastSeenObj["s"] . ' secs';
          }
        }
      }
    }
    $storage->close();
  } catch(StorageException $e) {
    $storage->close();
  }
}

?>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title><?php echo $userProfile['usrname']; ?> &middot; TriviaTime</title>
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
    <div class="row profile-header">
      <div class="span12">
        <h1><?php echo $userProfile['usrname']; ?></h1>
        <p>Profile and stats.</p>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Last seen</h2>
        <p> <?php echo $lastSeen; ?> ago</p>
      </div>
      <div span="span6">
        <h2>Highest Streak</h2>
        <p><?php echo $userProfile['highest_streak']; ?>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Averages</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Average Time/Question*</th>
              <th>Average Points/Question*</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if($userProfile['usrname'] != 'Not found') {
              echo '<tr>';
              echo '<td>' . number_format($userProfile['count'],2) . '</td>';
              echo '<td>' . number_format($userProfile['score'],2) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
      </div>
      <div class="span6">
        <h2>Totals</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Total Points</th>
              <th>Number Answered*</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if($userProfile['usrname'] != 'Not found') {
              echo '<tr>';
              echo '<td>' . number_format($userProfile['points'],0) . '</td>';
              echo '<td>' . number_format($userProfile['q_asked'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
      </div>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Contributions</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Reports Made</th>
              <th>Edits (Made/Accepted)</th>
              <th>Questions (Made/Accepted)</th>
            </tr>
          </thead>
          <tbody>
            <?php
            if($userProfile['usrname'] != 'Not found') {
              echo '<tr>';
              echo '<td>' . number_format($userProfile['num_r'],0) . '</td>';
              echo '<td>' . number_format($userProfile['num_e'],0) . '/' . number_format($userProfile['num_e_accepted'],0) . '</td>';
              echo '<td>' . number_format($userProfile['num_q'],0) . '/' . number_format($userProfile['num_q_accepted'],0) . '</td>';
              echo '</tr>';
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

  <script src="http://codeorigin.jquery.com/jquery-2.0.3.min.js"></script>
  <script src="js/bootstrap.min.js"></script>

</body>
</html>
