<?php
$username = $values['username']; 
$usernameCanonical = $values['usernameCanonical'];
$page = $values['page'];
$maxResults = $values['maxResults'];
$usersCount = $values['usersCount'];
$users = $values['users'];
$errors = $values['errors'];
?>
    <div class="hero-unit">
      <h1>Players</h1>
      <p>Show stats for players.</p>
      <p>
      </p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Search</h2>
        <form method="get">
          Username: <input name="username" value="<?php echo $username; ?>"></input>
          <input type="submit"></input>
        </form>
        <?php
        if(count($errors) != 0) {
          foreach($errors as $error) {
            echo "<div class='alert alert-error'>$error</div>";
          }
        }
        if($usersCount==0) {
          echo "<div class='alert alert-error'>User not found.</div>";
          $users = array();
        }
        if($usernameCanonical=='') {
          echo "<div class='alert alert-info'>Enter a username above to search for stats.</div>";
        }
        ?>
      </div>
    </div>



    <div class="row">
      <div class="span12">
        <h2>Player data</h2>
        <table class="table">
          <thead>
            <tr>
              <th>Username</th>
              <th>Total Points</th>
              <th>Question Answered*</th>
            </tr>
          </thead>
          <tbody>
            <?php
            foreach($users as $res) {
              echo '<tr>';
              echo '<td><a href="profile.php?username=' . rawurlencode($res['username']) . '">' . $res['username'] . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '<td>' . number_format($res['total'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($page, $usersCount, $maxResults); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <p>* These stats do not include KAOS</p>
      </div>
    </div>
    