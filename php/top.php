<?php
require_once('includes/autoload.php');

$timespans = array('d'=>'Day', 'w'=>'Week', 'm'=>'Month', 'y'=>'Year');
$timespan = 'd';
$timeDesc = 'Day';
if(array_key_exists('t', $_GET)) {
  if(array_key_exists(strtolower($_GET['t']), $timespans)) {
    $timespan = strtolower($_GET['t']);
    $timeDesc = $timespans[$timespan];
  }
}

$container->setTitle('Top Scores for ' . $timeDesc);
$container->setCurrentPage('top.php');

$container->render('top.php');
