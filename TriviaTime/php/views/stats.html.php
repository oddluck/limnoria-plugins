    <div class="hero-unit">
      <h1>Stats</h1>
      <p>Stats are updated continuously and instantly.</p>
    </div>

    <div class="row">
      <div class="span6">
        <h2>Todays Top Scores</h2>
        <?php
        foreach ($values['dayErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['dayResult'] as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="<?php echo $container->router->generate('top', array("timespan"=>"day")); ?>">View all</a></p>
      </div>

      <div class="span6">
        <h2>Week Top Scores</h2>
        <?php
        foreach ($values['weekErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['weekResult'] as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="<?php echo $container->router->generate('top', array("timespan"=>"week")); ?>">View all</a></p>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Month Top Scores</h2>
        <?php
        foreach ($values['monthErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['monthResult'] as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="<?php echo $container->router->generate('top', array("timespan"=>"month")); ?>">View all</a></p>
      </div>
      <div class="span6">
        <h2>Year Top Scores</h2>
        <?php
        foreach ($values['yearErrors'] as $error) {
          echo "<div class='alert alert-error'>$error</div>";
        }
        ?>
        <table class="table">
          <thead>
            <tr>
              <th>#</th>
              <th>Username</th>
              <th>Points</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($values['yearResult'] as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="<?php echo $container->router->generate('top', array("timespan"=>"year")); ?>">View all</a></p>
      </div>
    </div>
