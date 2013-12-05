<?php
require_once('includes/autoload.php');
$storage = $container->getStorage();

$username = '';
$usernameCanonical = '';

if(array_key_exists('username', $_GET)) {
    // Convert username to lowercase in irc
  $username = $_GET['username'];
  $ircLowerSymbols = array("\\"=>"|", "["=>"{", "]"=>"}", "~"=>"^");
  $usernameCanonical = strtr($username, $ircLowerSymbols);
  $usernameCanonical = strtolower($usernameCanonical);
}

if(array_key_exists('page', $_GET)) {
  $page = $_GET['page'];
}
if(!isset($page)) {
  $page = 1;
}
if($page < 1) {
  $page = 1;
}

$maxResults = 10;
$usersCount = 0;
$users = array();
$errors = array();

try {
  $users = $storage->getUserLikeUsernameCanonical($usernameCanonical, $page, $maxResults);
  $usersCount = $storage->getCountUserLikeUsernameCanonical($usernameCanonical);
} catch(StorageSchemaException $e) {
  $errors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $errors[] = "Error: Database is not available";
}

$storage->close();

// Redirect to profile if only 1 result found
if(count($users) == 1) {
  header('Location: profile.php?username=' . rawurlencode($users[0]['username']));
  die();
}

$values = array();
$values['username'] = $username;
$values['usernameCanonical'] = $usernameCanonical;
$values['page'] = $page;
$values['maxResults'] = $maxResults;
$values['usersCount'] = $usersCount;
$values['users'] = $users;
$values['errors'] = $errors;

$container->setTitle('Players');
$container->setCurrentPage('user.php');

$container->render('user.html.php', $values);
