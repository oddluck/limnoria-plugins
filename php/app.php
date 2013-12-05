<?php
// Load config
include "config/config.php"; // $config
// Load routes
include $config['configLocation'] . "routes.php"; // $routes

// Make the autoloader, requires $config
include $config['libLocation'] . "autoload.php";

// some base folder hacking for websites not in base dir
$config['baseFolder'] = dirname($_SERVER['PHP_SELF']);
$config['baseFolder'] = rtrim($config['baseFolder'], '/');

$routeInfo = array("base"=>$config['baseFolder'] . $config['baseRoute'], "routes"=>$routes);

// Create the container
$container = new Bootstrap($config, $routeInfo);


// Start the application based on the route
// TODO: Should this be in the Bootstrap?
$currentRoute = $container->router->matchCurrentRequest();
if(!$currentRoute) {
    $container->render404();
}

$params = $currentRoute->getParameters();
$target = $currentRoute->getTarget();

$parts = explode(':', $target);
if(count($parts) < 2) {
    // configuration error
    throw new Exception("Route is not properly configured.");
}

$controllerName = $parts[0];
$action = $parts[1];

$className = $controllerName . 'Controller';
$actionName = $action . 'Action';
$controller = new $className($container);
$controller->$actionName($params);
