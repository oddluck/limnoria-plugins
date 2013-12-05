<?php
class Bootstrap
{
    public $storage;
    public $config;
    public $login;
    public $renderer;

    public function __construct($config) {
        $this->config = $config;
        $this->storage = new Storage($this->config['dbLocation']);
        $this->login = new Login($this->storage);
        $this->renderer = new Renderer($config, $this);

        $this->setCurrentPage(basename($_SERVER['PHP_SELF']));
    }

    public function render($page, $values=array()) {
        $this->renderer->render($page, $values);
    }

    public function clearNotice() {
        if(array_key_exists('notice', $_SESSION)) {
            unset($_SESSION['notice']);
        }
    }

    public function setTitle($title) {
        $this->renderer->setTitle($title);
    }

    public function setNotice($notice) {
        $_SESSION['notice'] = $notice;
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

    public function getLogin() {
        return $this->login;
    }

    public function getStorage() {
        return $this->storage;
    }

    public function getConfig() {
        return $this->config;
    }
}
