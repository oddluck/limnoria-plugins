<?php
class Bootstrap
{
    public $storage;
    public $config;
    public $login;
    public $renderer;
    public $router;

    public function __construct($config, $routes) {
        $this->config = $config;
        $this->storage = new Storage($this->config['dbLocation']);
        $this->login = new Login($this->storage);
        $this->renderer = new Renderer($config, $this);
        $this->router = new Router();
        $this->loadRoutes($routes);

        $this->setCurrentPage(basename($_SERVER['PHP_SELF']));
    }

    public function loadRoutes($routes) {
        $this->router->setBasePath($routes['base']);
        foreach($routes['routes'] as $route) {
            $pattern = '';
            $target = '';
            $args = array();
            if(array_key_exists('pattern', $route)) {
                $pattern = $route['pattern'];
            }
            if(array_key_exists('target', $route)) {
                $target = $route['target'];
            }
            if(array_key_exists('args', $route)) {
                $args = $route['args'];
            }
            $this->router->map($pattern, $target, $args);
        }
    }

    public function render($page, $values=array(), $useTemplate=true) {
        $this->renderer->render($page, $values, $useTemplate);
    }

    public function clearNotice() {
        if(array_key_exists('notice', $_SESSION)) {
            unset($_SESSION['notice']);
        }
    }

    public function clearError() {
        if(array_key_exists('error', $_SESSION)) {
            unset($_SESSION['error']);
        }
    }

    public function setTitle($title) {
        $this->renderer->setTitle($title);
    }

    public function setNotice($notice) {
        $_SESSION['notice'] = $notice;
    }

    public function setError($error) {
        $_SESSION['error'] = $error;
    }

    public function setCurrentPage($currentPage) {
        $this->renderer->setCurrentPage($currentPage);
    }

    public function getNotice() {
        if(array_key_exists('notice', $_SESSION)) {
            return $_SESSION['notice'];
        } else {
            return null;
        }
    }

    public function getError() {
        if(array_key_exists('error', $_SESSION)) {
            return $_SESSION['error'];
        } else {
            return null;
        }
    }

    public function getLogin() {
        return $this->login;
    }

    public function getStorage() {
        return $this->storage;
    }

    public function getConfig() {
        return $this->config;
    }

    public function set404() {
        header("HTTP/1.0 404 Not Found");
    }

    public function render404() {
        $this->set404();
        $this->render('404.html.php');
        die();
    }

    public function redirect($page) {
        header('Location: ' . $page);
        die();
    }
}
