<?php
$userProfile = $values['userProfile'];
?>
    <div class="row profile-header">
      <div class="span12">
        <h1><?php echo htmlspecialchars($userProfile['usrname']); ?></h1>
        <p>Profile and stats.</p>
      </div>
    </div>
  <?php
  if(count($values['errors']) > 0) {
    echo '<div class="row">
            <div class="span12">';
    foreach($values['errors'] as $error) {
      echo "<div class='alert alert-error'>$error</div>";
    }
    echo '  </div>
          </div>';
  }
  ?>
    <div class="row">
      <div class="span6">
        <h2>Last seen</h2>
        <p>
        <?php
        if($userProfile['usrname'] != 'Not found') {
          echo $values['lastSeen'];
        }
        ?>
        </p>
      </div>
      <div span="span6">
        <h2>Highest Streak</h2>
        <p>
        <?php
        if($userProfile['usrname'] != 'Not found') {
          echo number_format($userProfile['highest_streak'],0);
        }
        ?>
        </p>
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
