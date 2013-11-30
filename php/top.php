<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
include('includes/pagination.php');
include('includes/storage.php');
try {
    $storage = new Storage($config['dbLocation']);
} catch(StorageException $e) {

}
$timespans = array('d'=>'Day', 'w'=>'Week', 'm'=>'Month', 'y'=>'Year');
$timespan = 'd';
$timeDesc = 'Day';
if(array_key_exists('t', $_GET)) {
  if(array_key_exists(strtolower($_GET['t']), $timespans)) {
    $timespan = strtolower($_GET['t']);
    $timeDesc = $timespans[$timespan];
  }
}

if(array_key_exists('page', $_GET)) {
  $page = $_GET['page'];
}
if(!isset($page)) {
  $page = 1;
}
if($page < 1) {
  $page = 1;
}

$maxResults = 20;

function replaceTimespanVariable($t) {
    $pathInfo = parse_url($_SERVER['REQUEST_URI']);
    if(array_key_exists('query', $pathInfo)) {
        $queryString = $pathInfo['query'];
    } else {
        $queryString = '';
    }
    parse_str($queryString, $queryArray);
    $queryArray['t'] = $t;
    if($t == 'd') {
        unset($queryArray['t']);
    }
    $queryArray['page'] = 1;
    unset($queryArray['page']);
    $queryString = http_build_query($queryArray);
    $new = $pathInfo['path'];
    if($queryString != ''){
        $new .=  '?' . $queryString;
    }
    return $new;  
}

?>
<head>
  <meta charset="utf-8">
  <title>Top Scores for <?php echo $timeDesc; ?> &middot; TriviaTime</title>
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
    <div class="hero-unit">
      <h1>Top Scores</h1>
      <p>Player rankings.</p>
    </div>
    <div class="row">
      <div class="span12">
        <ul class="nav nav-pills">
          <li<?php if($timespan=='d') { echo ' class="active"'; } ?>><a href="<?php echo replaceTimespanVariable('d'); ?>">Day</a></li>
          <li<?php if($timespan=='w') { echo ' class="active"'; } ?>><a href="<?php echo replaceTimespanVariable('w'); ?>">Week</a></li>
          <li<?php if($timespan=='m') { echo ' class="active"'; } ?>><a href="<?php echo replaceTimespanVariable('m'); ?>">Month</a></li>
          <li<?php if($timespan=='y') { echo ' class="active"'; } ?>><a href="<?php echo replaceTimespanVariable('y'); ?>">Year</a></li>
        </ul>
      </div>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Top Scores for <?php echo $timeDesc; ?></h2>
            <?php
            $resultCount = 0;
            $result = array();
            try {
              if ($timespan == 'w') {
                $result = $storage->getWeekTopScores($page, $maxResults);
                $resultCount = $storage->getCountWeekTopScores();
              } else if ($timespan == 'm') {
                $result = $storage->getMonthTopScores($page, $maxResults);
                $resultCount = $storage->getCountMonthTopScores();
              } else if ($timespan == 'y') {
                $result = $storage->getYearTopScores($page, $maxResults);
                $resultCount = $storage->getCountYearTopScores();    
              } else {
                $result = $storage->getDayTopScores($page, $maxResults);
                $resultCount = $storage->getCountDayTopScores();
              }
            } catch(StorageSchemaException $e) {
              echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
            } catch(StorageConnectionException $e) {
              echo "<div class='alert alert-error'>Error: Database is not available</div>";
            }
            $storage->close();
            ?>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Score</th>
            </tr>
          </thead>
          <tbody>
            <?php
            $currentRank = ($page-1)*$maxResults + 1;
            foreach($result as $res) {
              echo '<tr>';
              echo '<td>' . $currentRank . '</td>';
              echo '<td>' . $res['username'] . '</td>';
              echo '<td>' . $res['points'] . '</td>';
              echo '</tr>';
              $currentRank++;
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($page, $resultCount, $maxResults); 
        $pagination->paginate(); 
        ?>
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
