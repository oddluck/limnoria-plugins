<?php
require_once("includes/autoload.php");

function redirect($page) {
    header('Location: ' . $page);
    die();
}

$login = $container->getLogin();

$login->logout();

// force a new session, for the notice
$container->login = new Login();

$container->setNotice("<strong>Success!</strong> You have been successfully logged out.");
redirect($container->getConfig()['defaultLoginRedirectPage']);
