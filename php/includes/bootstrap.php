<?php
class Bootstrap
{
    public $storage;
    public $config;
    public $login;

    public $title = '';
    public $currentPage = '';

    public function __construct($config) {
        $this->config = $config;
        $this->storage = new Storage($this->config['dbLocation']);
        $this->login = new Login($this->storage);
    }

    public function render($page, $values=array()) {
        $viewVars = array();
        $viewVars['title'] = $this->title;
        if($this->title != '') {
            $viewVars['title'] .= ' &middot; ';
        }
        $viewVars['currentPage'] = $this->currentPage;
        $container = $this;
        include($this->config['viewLocation'] . 'header.php');
        include($this->config['viewLocation'] . $page);
        include($this->config['viewLocation'] . 'footer.php');
    }

    public function setTitle($title) {
        $this->title = $title;
    }

    public function setCurrentPage($currentPage) {
        $this->currentPage = $currentPage;
    }

    public function getTitle() {
        return $this->title;
    }

    public function getCurrentPage() {
        return $this->currentPage;
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
