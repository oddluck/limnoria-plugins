    <div class="hero-unit">
      <h1>Home</h1>
      <p>Get the latest stats for players and updates.</p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Latest questions asked</h2>
            <?php
            foreach($values['errorsQuestions'] as $error) {
              echo "<div class='alert alert-error'>$error</div>";
            }
            ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Round #</th>
              <th>Channel</th>
              <th>Question</th>
              <th class="hidden-phone">Question #</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['resultQuestions'] as $res) {
              echo '<tr>';
              echo '<td>' . $res['round_num'] . '</td>';
              echo '<td>' . htmlspecialchars($res['channel']) . '</td>';
              echo '<td class="breakable">' . htmlspecialchars($res['question']) . '</td>';
              echo '<td class="hidden-phone">' . $res['line_num'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
      </div>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Latest Activities</h2>
            <?php
            foreach($values['errorsActivities'] as $error) {
              echo "<div class='alert alert-error'>$error</div>";
            }
            ?>
        <table class="table modal-table">
          <thead>
            <tr>
              <th>Time</th>
              <th>Activity</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['resultActivities'] as $res) {
              echo '<tr>';
              echo '<td>' . date('Y/m/d h:i:s A',$res['timestamp']) . '</td>';
              echo '<td>' . htmlspecialchars($res['activity']) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
      </div>
    </div>
