    <div class="hero-unit">
      <h1>Top Scores</h1>
      <p>Player rankings.</p>
    </div>
    <div class="row">
      <div class="span12">
        <ul class="nav nav-pills">
          <li<?php if($values['timespan']=='day') { echo ' class="active"'; } ?>><a href="<?php echo $container->router->generate('top', array('timespan'=>'day')); ?>">Day</a></li>
          <li<?php if($values['timespan']=='week') { echo ' class="active"'; } ?>><a href="<?php echo $container->router->generate('top', array('timespan'=>'week')); ?>">Week</a></li>
          <li<?php if($values['timespan']=='month') { echo ' class="active"'; } ?>><a href="<?php echo $container->router->generate('top', array('timespan'=>'month')); ?>">Month</a></li>
          <li<?php if($values['timespan']=='year') { echo ' class="active"'; } ?>><a href="<?php echo $container->router->generate('top', array('timespan'=>'year')); ?>">Year</a></li>
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
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
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
    