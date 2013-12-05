<?php
class Renderer
{
    protected $title;
    protected $currentPage;
    protected $config;

    public function __construct($config) {
        $this->config = $config;
    }

    public function render($page, $values) {
        $viewVars = array();
        $viewVars['title'] = $this->title;
        if($this->title != '') {
            $viewVars['title'] .= ' &middot; ';
        }
        $viewVars['currentPage'] = $this->currentPage;
        $container = $this;
        include($this->config['viewLocation'] . 'header.html.php');
        include($this->config['viewLocation'] . $page);
        include($this->config['viewLocation'] . 'footer.html.php');
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
}
