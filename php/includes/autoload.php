<?php
include 'config.php';

function autoloadIncludes($class) {
    global $config;
    $filename = $class . ".php";
    if(file_exists($config['libLocation'] . $filename)) {
        require_once($config['libLocation'] . $filename);
    }
}

spl_autoload_register('autoloadIncludes');

$container = new Bootstrap($config);
