<?php
class Controller
{
    protected $container;

    public function __construct($container) {
        $this->container = $container;
    }

    public function getContainer() {
        return $this->container();
    }

    protected function redirect($page) {
        $this->container->redirect($page);
    }

    protected function setTitle($title) {
        $this->container->setTitle($title);
    }

    protected function render($page, $args=array()) {
        $this->container->render($page, $args);
    }

    protected function getNotice($notice) {
        return $this->container->getNotice;
    }

    protected function clearNotice() {
        $this->container->clearNotice();
    }

    protected function setNotice($notice) {
        $this->container->setNotice($notice);
    }

    protected function render404() {
        $this->container->set404();
        $this->container->render404();
    }
}
