    <div class="hero-unit">
      <h1>Players</h1>
      <p>Show stats for players.</p>
    </div>
    <div class="row">
      <div class="span12">
        <h2>Search</h2>
        <form method="get">
          Username: <input name="username" value="<?php echo $values['username']; ?>"></input>
          <button class="btn btn-small btn-primary" type="submit">Search</button>
        </form>
        <?php
        if(count($values['errors']) != 0) {
          foreach($values['errors'] as $error) {
            echo "<div class='alert alert-error'>$error</div>";
          }
        }
        if($values['usersCount']==0) {
          echo "<div class='alert alert-error'>User not found.</div>";
          $values['users'] = array();
        }
        if($values['usernameCanonical']=='') {
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
            foreach($values['users'] as $res) {
              echo '<tr>';
              echo '<td><a href="' . $container->router->generate('profile', array("username"=>$res['username'])) . '">' . htmlspecialchars($res['username']) . '</a></td>';
              echo '<td>' . number_format($res['points'],0) . '</td>';
              echo '<td>' . number_format($res['total'],0) . '</td>';
              echo '</tr>';
            }
            ?>
          </tbody>
        </table>
        <?php
        $pagination = new Paginator($values['page'], $values['usersCount'], $values['maxResults']); 
        $pagination->paginate(); 
        ?>
      </div>
    </div>

    <div class="row">
      <div class="span12">
        <p>* These stats do not include KAOS</p>
      </div>
    </div>
    