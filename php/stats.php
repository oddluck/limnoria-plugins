<?php
require_once('includes/autoload.php');

$storage = $container->getStorage();

$dayResult = array();
$dayErrors = array();
try {
  $dayResult = $storage->getDayTopScores(1, 10);
} catch(StorageSchemaException $e) {
  $dayErrors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $dayErrors[] = "Error: Database is not available";
}

$weekResult = array();
$weekErrors = array();
try {
  $weekResult = $storage->getWeekTopScores(1, 10);
} catch(StorageSchemaException $e) {
  $weekErrors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $weekErrors[] = "Error: Database is not available";
}

$monthResult = array();
$monthErrors = array();
try {
  $monthResult = $storage->getMonthTopScores(1, 10);
} catch(StorageSchemaException $e) {
  $monthErrors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $monthErrors[] = "Error: Database is not available";
}

$yearResult = array();
$yearErrors = array();
try {
  $yearResult = $storage->getYearTopScores(1, 10);
} catch(StorageSchemaException $e) {
  $yearErrors[] = "Error: Database schema is not queryable";
} catch(StorageConnectionException $e) {
  $yearErrors[] = "Error: Database is not available";
}

$values = array();
$values['dayResult'] = $dayResult;
$values['dayErrors'] = $dayErrors;
$values['weekResult'] = $weekResult;
$values['weekErrors'] = $weekErrors;
$values['monthResult'] = $monthResult;
$values['monthErrors'] = $monthErrors;
$values['yearResult'] = $yearResult;
$values['yearErrors'] = $yearErrors;

$container->setTitle('Stats');

$container->render('stats.html.php', $values);
