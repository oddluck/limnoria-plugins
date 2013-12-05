<?php
$storage = $container->getStorage();
?>
    <div class="hero-unit">
      <h1>Stats</h1>
      <p>Stats are updated continuously and instantly.</p>
      <p>
      </p>
    </div>

    <div class="row">
      <div class="span6">
        <h2>Todays Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getDayTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php">View all</a></p>
      </div>

      <div class="span6">
        <h2>Week Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getWeekTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=w">View all</a></p>
      </div>
    </div>
    <div class="row">
      <div class="span6">
        <h2>Month Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getMonthTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=m">View all</a></p>
      </div>
      <div class="span6">
        <h2>Year Top Scores</h2>
        <?php
        $result = array();
        try {
          $result = $storage->getYearTopScores(1, 10);
        } catch(StorageSchemaException $e) {
          echo "<div class='alert alert-error'>Error: Database schema is not queryable</div>";
        } catch(StorageConnectionException $e) {
          echo "<div class='alert alert-error'>Error: Database is not available</div>";
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
            foreach($result as $key=>$res) {
              echo '<tr>';
              echo '<td>' . ($key+1) . '</td>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '</tr>';
            }
            $storage->close();
            ?>
          </tbody>
        </table>
        <p><a class="btn btn-info btn-block" href="top.php?t=y">View all</a></p>
      </div>
    </div>
