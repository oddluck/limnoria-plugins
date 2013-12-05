<?php
class Renderer
{
    protected $title = '';
    protected $currentPage = '';
    protected $config;
    protected $container;

    public function __construct($config, $container) {
        $this->config = $config;
        $this->container = $container;
    }

    public function render($page, $values, $useTemplate=true) {
        $viewVars = array();
        $viewVars['title'] = $this->title;
        if($this->title != '') {
            $viewVars['title'] .= ' &middot; ';
        }

        $viewVars['currentPage'] = $this->currentPage;
        $container = $this->container;

        if($useTemplate) {
            include($this->config['viewLocation'] . 'header.html.php');
            include($this->config['viewLocation'] . $page);
            include($this->config['viewLocation'] . 'footer.html.php');
        } else {
            include($this->config['viewLocation'] . $page);
        }
    }

    public function setTitle($title) {
        $this->title = $title;
    }

    public function setCurrentPage($currentPage) {
        $this->currentPage = $currentPage;
    }

    public function getContainer() {
        return $this->container;
    }

    public function getTitle() {
        return $this->title;
    }

    public function getCurrentPage() {
        return $this->currentPage;
    }
}
