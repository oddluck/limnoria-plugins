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
        $this->renderer = new Renderer($config);

        $this->setCurrentPage(basename($_SERVER['PHP_SELF']));
    }

    public function render($page, $values=array()) {
        $this->renderer->render($page, $values);
    }

    public function setTitle($title) {
        $this->renderer->setTitle($title);
    }

    public function setCurrentPage($currentPage) {
        $this->renderer->setCurrentPage($currentPage);
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
