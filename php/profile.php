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

$lastSeen = 'Never';

function emptyResult() {
  $result = array();
  $result['usrname'] = "Not found";
  $result['count'] = 0;
  $result['score'] = 0;
  $result['points'] = 0;
  $result['q_asked'] = 0;
  $result['num_e'] = 0;
  $result['num_e_accepted'] = 0;
  $result['num_q'] = 0;
  $result['num_q_accepted'] = 0;
  $result['num_r'] = 0;
  $result['highest_streak'] = 0;
  return $result;
}

function secondsToTime($inputSeconds) {

  $secondsInAMinute = 60;
  $secondsInAnHour  = 60 * $secondsInAMinute;
  $secondsInADay    = 24 * $secondsInAnHour;

  // extract days
  $days = floor($inputSeconds / $secondsInADay);

  // extract hours
  $hourSeconds = $inputSeconds % $secondsInADay;
  $hours = floor($hourSeconds / $secondsInAnHour);

  // extract minutes
  $minuteSeconds = $hourSeconds % $secondsInAnHour;
  $minutes = floor($minuteSeconds / $secondsInAMinute);

  // extract the remaining seconds
  $remainingSeconds = $minuteSeconds % $secondsInAMinute;
  $seconds = ceil($remainingSeconds);

  // return the final array
  $obj = array(
      'd' => (int) $days,
      'h' => (int) $hours,
      'm' => (int) $minutes,
      's' => (int) $seconds,
  );
  return $obj;
}

$userProfile = emptyResult();
$errors = array();

if ($username != '') {
  try {
    $profileResult = $storage->getUserProfileInformation($usernameCanonical);
    if(count($profileResult) > 0) {
      if(array_key_exists('usrname', $profileResult[0])) {
        if(!is_null($profileResult[0]['usrname'])) {
          $userProfile = $profileResult[0];
        }
      }
    }
    $lastSeenQuery = $storage->getTimeSinceLastPlayed($usernameCanonical);
    if(count($lastSeenQuery) > 0) {
      if(array_key_exists('last_updated', $lastSeenQuery[0])) {
        if(!is_null($lastSeenQuery[0]['last_updated'])) {
          $lastSeenSeconds = strtotime("now") - $lastSeenQuery[0]['last_updated'];
          $lastSeenObj = secondsToTime($lastSeenSeconds);
          $lastSeen = '';
          if($lastSeenObj["d"] > 0) {
            $lastSeen .= $lastSeenObj["d"] . ' days ';
          }
          if($lastSeenObj["h"] > 0) {
            $lastSeen .= $lastSeenObj["h"] . ' hours ';
          }
          if($lastSeenObj["m"] > 0) {
            $lastSeen .= $lastSeenObj["m"] . ' mins ';
          }
          if($lastSeenObj["s"] > 0) {
            $lastSeen .= $lastSeenObj["s"] . ' secs';
          }
          if($lastSeen != '') {
            $lastSeen .= ' ago';
          }
        }
      }
    }
  } catch(StorageSchemaException $e) {
    $errors[] = "Error: Database schema is not queryable";
  } catch(StorageConnectionException $e) {
    $errors[] = "Error: Database is not available";
  }
  $storage->close();
}

$values = array();

$values['userProfile'] = $userProfile;
$values['username'] = $username;
$values['usernameCanonical'] = $usernameCanonical;
$values['errors'] = $errors;
$values['lastSeen'] = $lastSeen;

$container->setTitle($username);

$container->render('profile.html.php', $values);
