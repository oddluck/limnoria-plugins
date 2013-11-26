<!DOCTYPE html>
<html lang="en">
<?php
include('config.php');
include('pagination.php');

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

$maxResults = 5;
?>
<head>
  <meta charset="utf-8">
  <title>Reports &middot; TriviaTime</title>
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
              <li><a href="index.php">Home</a></li>
              <li><a href="stats.php">Stats</a></li>
              <li><a href="user.php">Players</a></li>
              <li class="active"><a href="reports.php">Reports</a></li>
              <li><a href="about.php">About</a></li>
            </ul>
          </div>
        </div>
      </div><!-- /.navbar -->
    </div>

    <div class="hero-unit">
      <h1>Reports</h1>
      <p>The reports and edits that are currently pending.</p>
      <p>
      </p>
    </div>
    <div class="accordion" id="accordion1">
      <div class="accordion-group">
        <div class="accordion-heading">
          <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion1" href="#collapseOne">
            Hide reports
          </a>
        </div>
        <div class="row">
          <div class="span12">
            <div id="collapseOne" class="accordion-body collapse in">
              <div class="accordion-inner">
                <h2>Reports</h2>
                <table class="table">
                  <thead>
                    <tr>
                      <th>Report #</th>
                      <th>Username</th>
                      <th>Question #</th>
                      <th>Question</th>
                      <th>Report Text</th>
                    </tr>
                  </thead>
                  <tbody>
                    <?php
                    $resultCount = 0;
                    if ($db) {
                      $q = $db->prepare('SELECT tr.*, tq.question as original  
                        FROM triviareport tr 
                        INNER JOIN triviaquestion tq 
                        on tq.id=question_num 
                        ORDER BY id DESC LIMIT :offset, :maxResults');
                      $qCount = $db->query('SELECT count(id) FROM triviareport');
                      $q->execute(array(':offset'=>($reportPage-1) * $maxResults, ':maxResults'=>$maxResults));
                      if ($q === false) {
                        die("Error: database error: table does not exist\n");
                      } else {
                        $result = $q->fetchAll();
                        $resultCount = $qCount->fetchColumn();
                        foreach($result as $res) {
                          echo '<tr>';
                          echo '<td>' . $res['id'] . '</td>';
                          echo '<td>' . $res['username'] . '</td>';
                          echo '<td>' . $res['question_num'] . '</td>';
                          echo '<td>' . $res['original'] . '</td>';
                          echo '<td>' . $res['report_text'] . '</td>';
                          echo '</tr>';
                        }
                      }
                    } else {
                      die('Couldnt connect to db');
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
          </div>
        </div>
      </div>
    </div>


    <div class="accordion" id="accordion2">
      <div class="accordion-group">
        <div class="accordion-heading">
          <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion2" href="#collapseTwo">
            Hide edits
          </a>
        </div>
        <div class="row">
          <div class="span12">
            <div id="collapseTwo" class="accordion-body collapse in">
              <div class="accordion-inner">
                <h2>Edits</h2>
                <table class="table">
                  <thead>
                    <tr>
                      <th>Edit #</th>
                      <th>Username</th>
                      <th>New Question</th>
                      <th>Old Question</th>
                      <th>Question #</th>
                    </tr>
                  </thead>
                  <tbody>
                    <?php
                    $resultCount = 0;
                    if ($db) {
                      $q = $db->prepare('SELECT te.*, tq.question as original  
                        FROM triviaedit te 
                        INNER JOIN triviaquestion tq 
                        on tq.id=question_id 
                        ORDER BY id DESC LIMIT :offset, :maxResults');
                      $q->execute(array(':offset'=>($editPage-1) * $maxResults, ':maxResults'=>$maxResults));
                      $qCount = $db->query('SELECT count(id) FROM triviaedit');
                      if ($q === false) {
                        die("Error: database error: table does not exist\n");
                      } else {
                        $result = $q->fetchAll();
                        $resultCount = $qCount->fetchColumn();
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
                          echo '<td>' . $res['username'] . '</td>';
                          echo '<td>' . $differenceString . '</td>';
                          echo '<td>' . $res['original'] . '</td>';
                          echo '<td>' . $res['question_id'] . '</td>';
                          echo '</tr>';
                        }
                      }
                    } else {
                      die($err);
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
          </div>
        </div>
      </div>
    </div>

    <div class="accordion" id="accordion3">
      <div class="accordion-group">
        <div class="accordion-heading">
          <a class="accordion-toggle" data-toggle="collapse" data-parent="#accordion3" href="#collapseThree">
            Hide added questions
          </a>
        </div>
        <div class="row">
          <div class="span12">
            <div id="collapseThree" class="accordion-body collapse in">
              <div class="accordion-inner">
                <h2>Added Questions</h2>
                <table class="table">
                  <thead>
                    <tr>
                      <th>#</th>
                      <th>Author</th>
                      <th>New Question</th>
                    </tr>
                  </thead>
                  <tbody>
                    <?php
                    $resultCount = 0;
                    if ($db) {
                      $q = $db->prepare('SELECT tq.*  FROM triviatemporaryquestion tq ORDER BY tq.id DESC LIMIT :offset, :maxResults');
                      $q->execute(array(':offset'=>($newPage-1) * $maxResults, ':maxResults'=>$maxResults));
                      $qCount = $db->query('SELECT count(id) FROM triviatemporaryquestion');
                      if ($q === false) {
                        die("Error: database error: table does not exist\n");
                      } else {
                        $result = $q->fetchAll();
                        $resultCount = $qCount->fetchColumn();
                        foreach($result as $res) {
                          echo '<tr>';
                          echo '<td>' . $res['id'] . '</td>';
                          echo '<td>' . $res['username'] . '</td>';
                          echo '<td>' . $res['question'] . '</td>';
                          echo '</tr>';
                        }
                      }
                    } else {
                      die('Couldnt connect to db');
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
          </div>
        </div>
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
