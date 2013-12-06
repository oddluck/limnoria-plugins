<?php
$routes = array();

// Home
$routes[] = array("pattern"=>"/","target"=>'Index:index', "args"=>array("name"=>"home"));

// About
$routes[] = array("pattern"=>"/about", "target"=>"About:about", "args"=>array("name"=>"about"));

// Stats
$routes[] = array("pattern"=>"/stats", "target"=>"Stats:stats", "args"=>array("name"=>"stats"));
$routes[] = array("pattern"=>"/top/:timespan", "target"=>"Stats:top", "args"=>array("name"=>"top"));

// Players
$routes[] = array("pattern"=>"/search", "target"=>"User:search", "args"=>array("name"=>"search"));
$routes[] = array("pattern"=>"/profile/:username", "target"=>"User:profile", "args"=>array("name"=>"profile", "filters" => array("username" => "([^\s/]+)")));

// Reports
$routes[] = array("pattern"=>"/reports", "target"=>"Reports:list", "args"=>array("name"=>"reports"));

// Login/Logout
$routes[] = array("pattern"=>"/login", "target"=>"Login:login", "args"=>array("name"=>"login"));
$routes[] = array("pattern"=>"/logout", "target"=>"Login:logout", "args"=>array("name"=>"logout"));
