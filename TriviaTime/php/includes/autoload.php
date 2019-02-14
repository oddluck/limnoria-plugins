<?php
function autoloadIncludes($class) {
    global $config;
    $filename = $class . ".php";
    if(file_exists($config['libLocation'] . $filename)) {
        require_once($config['libLocation'] . $filename);
    }
    if(file_exists($config['controllerLocation'] . $filename)) {
        require_once($config['controllerLocation'] . $filename);
    }
}

spl_autoload_register('autoloadIncludes');
