    <div class="hero-unit">
      <h1>Home</h1>
      <p>Get the latest stats for players and updates.</p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Latest questions asked</h2>
            <?php
            foreach($values['errors'] as $error) {
              echo "<div class='alert alert-error'>$error</div>";
            }
            ?>
        <table class="table modal-table">
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
            foreach($values['result'] as $res) {
              echo '<tr>';
              echo '<td>' . $res['round_num'] . '</td>';
              echo '<td>' . $res['channel'] . '</td>';
              echo '<td class="breakable">' . $res['question'] . '</td>';
              echo '<td>' . $res['line_num'] . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
      </div>
    </div>
