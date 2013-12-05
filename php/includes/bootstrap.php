<?php
class Bootstrap
{
    public $storage;
    public $config;
    public $login;

    public function __construct($config) {
        $this->config = $config;
        $this->storage = new Storage($this->config['dbLocation']);
        $this->login = new Login($this->storage);
    }

    public function render($page, $title='', $currentPage='', $values=array()) {
        $viewVars = array();
        $viewVars['title'] = '';
        $viewVars['currentPage'] = '';
        if(!empty($title)) {
            $viewVars['title'] = $title . ' &middot; ';
        }
        if(!empty($currentPage)) {
            $viewVars['currentPage'] = $currentPage;
        }
        $container = $this;
        include($this->config['viewLocation'] . 'header.php');
        include($this->config['viewLocation'] . $page);
        include($this->config['viewLocation'] . 'footer.php');
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
