    <div class="hero-unit">
      <h1>Top Scores</h1>
      <p>Player rankings.</p>
    </div>
    <div class="row">
      <div class="span12">
        <ul class="nav nav-pills">
          <li<?php if($values['timespan']=='d') { echo ' class="active"'; } ?>><a href="top.php?t=d">Day</a></li>
          <li<?php if($values['timespan']=='w') { echo ' class="active"'; } ?>><a href="top.php?t=w">Week</a></li>
          <li<?php if($values['timespan']=='m') { echo ' class="active"'; } ?>><a href="top.php?t=m">Month</a></li>
          <li<?php if($values['timespan']=='y') { echo ' class="active"'; } ?>><a href="top.php?t=y">Year</a></li>
        </ul>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Top Scores for <?php echo $values['timeDesc']; ?></h2>
            <?php
            foreach($values['errors'] as $error) {
              echo "<div class='alert alert-error'>$error</div>";
            }
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
            $currentRank = ($values['page']-1)*$values['maxResults'] + 1;
            foreach($values['result'] as $res) {
              echo '<tr>';
              echo '<td>' . $currentRank . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
              $currentRank++;
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['page'], $values['resultCount'], $values['maxResults']); 
        $pagination->paginate(); 
        ?>
      </div>
      <div class="offset6"></div>
    </div>
    