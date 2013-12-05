<?php
require_once('includes/autoload.php');

$storage = $container->getStorage();

$timespans = array('d'=>'Day', 'w'=>'Week', 'm'=>'Month', 'y'=>'Year');
$timespan = 'd';
$timeDesc = 'Day';
if(array_key_exists('t', $_GET)) {
  if(array_key_exists(strtolower($_GET['t']), $timespans)) {
    $timespan = strtolower($_GET['t']);
    $timeDesc = $timespans[$timespan];
  }
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

$maxResults = 20;

$resultCount = 0;
$result = array();
$errors = array();
try {
  if ($timespan == 'w') {
    $result = $storage->getWeekTopScores($page, $maxResults);
    $resultCount = $storage->getCountWeekTopScores();
  } else if ($timespan == 'm') {
    $result = $storage->getMonthTopScores($page, $maxResults);
    $resultCount = $storage->getCountMonthTopScores();
  } else if ($timespan == 'y') {
    $result = $storage->getYearTopScores($page, $maxResults);
    $resultCount = $storage->getCountYearTopScores();    
  } else {
    $result = $storage->getDayTopScores($page, $maxResults);
    $resultCount = $storage->getCountDayTopScores();
  }
} catch(StorageSchemaException $e) {
  $errors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $errors[] = "Error: Database is not available";
}

$values = array();
$values['result'] = $result;
$values['resultCount'] = $resultCount;
$values['maxResults'] = $maxResults;
$values['page'] = $page;
$values['timespan'] = $timespan;
$values['timeDesc'] = $timeDesc;
$values['errors'] = $errors;

$container->setTitle('Top Scores for ' . $timeDesc);
$container->setCurrentPage('top.php');

$container->render('top.php', $values);
