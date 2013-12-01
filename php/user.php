<?php
include('config.php');
include('includes/pagination.php');
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

if(array_key_exists('page', $_GET)) {
  $page = $_GET['page'];
}
if(!isset($page)) {
  $page = 1;
}
if($page < 1) {
  $page = 1;
}

$maxResults = 10;
$usersCount = 0;
$users = array();
$errors = array();

try {
  $users = $storage->getUserLikeUsernameCanonical($usernameCanonical, $page, $maxResults);
  $usersCount = $storage->getCountUserLikeUsernameCanonical($usernameCanonical);
} catch(StorageSchemaException $e) {
  $errors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $errors[] = "Error: Database is not available";
}

$storage->close();

// Redirect to profile if only 1 result found
if(count($users) == 1) {
  header('Location: profile.php?username=' . $users[0]['username']);
  die();
}
?><!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <title>Players &middot; TriviaTime</title>
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
            <li class="active"><a href="user.php">Players</a></li>
            <li><a href="reports.php">Reports</a></li>
            <li><a href="about.php">About</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div><!-- /.navbar -->
  <div class="container">
    <div class="hero-unit">
      <h1>Players</h1>
      <p>Show stats for players.</p>
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
        if(count($errors) != 0) {
          foreach($errors as $error) {
            echo "<div class='alert alert-error'>$error</div>";
          }
        }
        if($usersCount==0) {
          echo "<div class='alert alert-error'>User not found.</div>";
          $users = array();
        }
        if($usernameCanonical=='') {
          echo "<div class='alert alert-info'>Enter a username above to search for stats.</div>";
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
            foreach($users as $res) {
              echo '<tr>';
              echo '<td><a href="profile.php?username=' . $res['username'] . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '<td>' . number_format($res['total'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($page, $usersCount, $maxResults); 
        $pagination->paginate(); 
        ?>
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
