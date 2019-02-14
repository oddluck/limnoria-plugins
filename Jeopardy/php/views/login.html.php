<?php
function getError($index, $values) {
  if(array_key_exists($index, $values['errors'])) {
    return $values['errors'][$index];
  }
  return null;
}
?>
    <form class="form-signin" method="POST">
      <h2 class="form-signin-heading">Please sign in</h2>
      <?php
      if(!is_null(getError('login', $values))) {
        echo "<div class='alert alert-error'>". getError('login', $values) ."</div>";
      }

      if(!is_null(getError('username', $values))) {
        echo "<p class='text-error'>". getError('username', $values) ."</p>";
      }
      ?>
      <input type="text" class="input-block-level" placeholder="Username" name="username">
      <?php
      if(!is_null(getError('password', $values))) {
        echo "<p class='text-error'>". getError('password', $values) ."</p>";
      }
      ?>
      <input type="password" class="input-block-level" placeholder="Password" name="password">
      <!--
      <label class="checkbox">
        <input type="checkbox" value="remember-me"> Remember me
      </label>
      -->
      <button class="btn btn-large btn-primary" type="submit">Sign in</button>
    </form>
