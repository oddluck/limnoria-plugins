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

$container->render('top.php', 'Top Scores for ' . $timeDesc, 'top.php');
