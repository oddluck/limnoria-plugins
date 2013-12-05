<?php
require_once("includes/autoload.php");

function getPostVariable($key) {
    if(array_key_exists($key, $_POST)) {
        $value = $_POST[$key];
    }
    if(!isset($value)) {
      $value = null;
    }
    return $value;
}

function redirect($page) {
    header('Location: ' . $page);
    die();
}

function doRedirect() {
    global $container;
    $defaultPage = $container->getConfig()['defaultLoginRedirectPage'];
    if(array_key_exists('lastPage', $_SESSION)) {
        redirect($_SESSION('lastPage'));
    } else {
        redirect($defaultPage);
    } 
}

$login = $container->getLogin();

if($login->isLoggedIn()) {
    doRedirect();
}

$errors = array();
if($_SERVER['REQUEST_METHOD'] === 'POST') {
    $username = getPostVariable("username");
    $password = getPostVariable("password");

    if(empty($username)) {
        $errors['username'] = "Please enter a Username.";
    }
    if(empty($password)) {
        $errors['password'] = "Please enter a Password.";
    }
    if(!empty($username) && !empty($password)) {
        if($login->login($username, $password)) {
            $container->setNotice("<strong>Success!</strong> You have been successfully logged in.");
            doRedirect();
        } else {
            $errors['login'] = "Invalid credentials. Please check your username and password, and try again.";
        }
    }
}

$values = array();
$values['errors'] = $errors;

$container->setTitle("Login");
$container->render("login.html.php", $values);
