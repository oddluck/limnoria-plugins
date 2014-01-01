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
$routes[] = array("pattern"=>"/profile/:username", "target"=>"User:profile", "args"=>array("name"=>"profile", "filters" => array("username" => "([a-zA-Z\d_\-\[\]\\^{}|`%]*)")));

// Reports
$routes[] = array("pattern"=>"/reports", "target"=>"Reports:list", "args"=>array("name"=>"reports"));

// Login/Logout
$routes[] = array("pattern"=>"/login", "target"=>"Login:login", "args"=>array("name"=>"login"));
$routes[] = array("pattern"=>"/logout", "target"=>"Login:logout", "args"=>array("name"=>"logout"));

// Admin Report remove
$routes[] = array("pattern"=>"/manage/report/:id/remove", "target"=>"AdminReport:removeReport", "args"=>array("name"=>"remove-report", "filters"=> array("id"=>"([\d]+)")));

// Admin Edit accept/remove
$routes[] = array("pattern"=>"/manage/edit/:id/accept", "target"=>"AdminEdit:acceptEdit", "args"=>array("name"=>"accept-edit", "filters"=> array("id"=>"([\d]+)")));
$routes[] = array("pattern"=>"/manage/edit/:id/remove", "target"=>"AdminEdit:removeEdit", "args"=>array("name"=>"remove-edit", "filters"=> array("id"=>"([\d]+)")));

// Admin Delete accept/remove
$routes[] = array("pattern"=>"/manage/delete/:id/accept", "target"=>"AdminDelete:acceptDelete", "args"=>array("name"=>"accept-delete", "filters"=> array("id"=>"([\d]+)")));
$routes[] = array("pattern"=>"/manage/delete/:id/remove", "target"=>"AdminDelete:removeDelete", "args"=>array("name"=>"remove-delete", "filters"=> array("id"=>"([\d]+)")));

// Admin new accept/remove
$routes[] = array("pattern"=>"/manage/new/:id/accept", "target"=>"AdminNew:acceptNew", "args"=>array("name"=>"accept-new", "filters"=> array("id"=>"([\d]+)")));
$routes[] = array("pattern"=>"/manage/new/:id/remove", "target"=>"AdminNew:removeNew", "args"=>array("name"=>"remove-new", "filters"=> array("id"=>"([\d]+)")));
