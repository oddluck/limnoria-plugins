<!DOCTYPE html>
<html lang="en">
<?php
  include('config.php');
?>
  <head>
    <meta charset="utf-8">
    <title>Reports &middot; TriviaTime</title>
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
                        if ($db) {
                          $q = $db->query('SELECT tr.*, tq.question as original  FROM triviareport tr INNER JOIN triviaquestion tq on tq.id=question_num ORDER BY id DESC LIMIT 10');
                            if ($q === false) {
                              die("Error: database error: table does not exist\n");
                            } else {
                              $result = $q->fetchAll();
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
                      if ($db) {
                          $q = $db->query('SELECT te.*, tq.question as original  FROM triviaedit te INNER JOIN triviaquestion tq on tq.id=question_id ORDER BY id DESC LIMIT 10');
                          if ($q === false) {
                              die("Error: database error: table does not exist\n");
                          } else {
                              $result = $q->fetchAll();
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
                        if ($db) {
                          $q = $db->query('SELECT tq.*  FROM triviatemporaryquestion tq ORDER BY tq.id DESC LIMIT 10');
                            if ($q === false) {
                              die("Error: database error: table does not exist\n");
                            } else {
                              $result = $q->fetchAll();
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


