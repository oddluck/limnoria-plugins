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

if(array_key_exists('rp', $_GET)) {
  $reportPage = $_GET['rp'];
}
if(!isset($reportPage)) {
  $reportPage = 1;
}
if($reportPage < 1) {
  $reportPage = 1;
}

if(array_key_exists('ep', $_GET)) {
  $editPage = $_GET['ep'];
}
if(!isset($editPage)) {
  $editPage = 1;
}
if($editPage < 1) {
  $editPage = 1;
}

if(array_key_exists('np', $_GET)) {
  $newPage = $_GET['np'];
}
if(!isset($newPage)) {
  $newPage = 1;
}
if($newPage < 1) {
  $newPage = 1;
}

if(array_key_exists('dp', $_GET)) {
  $deletePage = $_GET['dp'];
}
if(!isset($deletePage)) {
  $deletePage = 1;
}
if($deletePage < 1) {
  $deletePage = 1;
}

$maxResults = 5;
?>
<head>
  <meta charset="utf-8">
  <title>Reports &middot; TriviaTime</title>
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
            <li class="active"><a href="reports.php">Reports</a></li>
            <li><a href="about.php">About</a></li>
          </ul>
        </div>
      </div>
    </div>
  </div><!-- /.navbar -->
  <div class="container">
    <div class="hero-unit">
      <h1>Reports</h1>
      <p>The reports and edits that are currently pending.</p>
      <p>
      </p>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Reports</h2>
        <?php
        $resultCount = 0;
        $result = array();
        try {
          $result = $storage->getTopReports($reportPage, $maxResults);
          $resultCount = $storage->getCountReports();
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Report #</th>
              <th class="hidden-phone">Username</th>
              <th>Question #</th>
              <th>Question</th>
              <th>Report Text</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($result as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td>' . $res['question_num'] . '</td>';
              echo '<td class="breakable">' . $res['original'] . '</td>';
              echo '<td class="breakable">' . $res['report_text'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($reportPage, $resultCount, $maxResults, 'rp'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>


    <div class="row">
      <div class="span12">
        <h2>Edits</h2>
        <?php
        $resultCount = 0;
        $result = array();
        try {
          $result = $storage->getTopEdits($editPage, $maxResults);
          $resultCount = $storage->getCountEdits();
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Edit #</th>
              <th class="hidden-phone">Username</th>
              <th>New Question</th>
              <th>Old Question</th>
              <th>Question #</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($result as $res) {
              $isItalic = false;
              $splitNew = explode('*', $res['question']);
              $splitOld = explode('*', $res['original']);

              $differenceString = '';
              for($y=0;$y<sizeof($splitNew);$y++){
                if($y>0) {
                  $isItalic = false;
                  $differenceString .= '</u>';
                  $differenceString .= '*';
                }
                $brokenNew = str_split($splitNew[$y]);
                if(!array_key_exists($y, $splitOld)){
                  $splitOld[$y] = '*';
                }
                $brokenOld = str_split($splitOld[$y]);
                for($i=0;$i<sizeof($brokenNew);$i++) {
                  if(!array_key_exists($i, $brokenOld)||!array_key_exists($i, $brokenNew)) {
                    if($isItalic==false){
                      $isItalic = true;
                      $differenceString .= '<u>';
                    }
                  } else if($brokenNew[$i]=='*') {
                    $isItalic = false;
                    $differenceString .= '</u>';
                  } else if($brokenNew[$i]!=$brokenOld[$i]) {
                    if($isItalic==false){
                      $isItalic = true;
                      $differenceString .= '<u>';
                    }
                  } else if($brokenNew[$i]==$brokenOld[$i]&&$isItalic==true) {
                    $isItalic = false;
                    $differenceString .= '</u>';
                  }
                  $differenceString.=$brokenNew[$i];
                }
              }
              if($isItalic==true) {
                $differenceString .= '</u>';
              }

              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $differenceString . '</td>';
              echo '<td class="breakable">' . $res['original'] . '</td>';
              echo '<td>' . $res['question_id'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($editPage, $resultCount, $maxResults, 'ep'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Added Questions</h2>
        <?php
        $resultCount = 0;
        $result = array();
        try {
          $result = $storage->getTopNewQuestions($newPage, $maxResults);
          $resultCount = $storage->getCountNewQuestions();
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>#</th>
              <th>Author</th>
              <th>New Question</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($result as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td>' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $res['question'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($newPage, $resultCount, $maxResults, 'np'); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <h2>Pending Deletions</h2>
        <?php
        $resultCount = 0;
        $result = array();
        try {
          $result = $storage->getTopDeletions($deletePage, $maxResults);
          $resultCount = $storage->getCountDeletions();
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
        }
        ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>#</th>
              <th class="hidden-phone">Username</th>
              <th>New Question</th>
              <th>Question #</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($result as $res) {
              echo '<tr>';
              echo '<td>' . $res['id'] . '</td>';
              echo '<td class="hidden-phone">' . $res['username'] . '</td>';
              echo '<td class="breakable">' . $res['question'] . '</td>';
              echo '<td>' . $res['line_num'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($deletePage, $resultCount, $maxResults, 'dp'); 
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
  <script src="js/triviatime.js"></script>

</body>
</html>
