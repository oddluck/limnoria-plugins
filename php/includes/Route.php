<?php
class Route
{
    private $url;
    private $methods = array('GET','POST','PUT','DELETE');
    private $target;
    private $name;
    private $filters = array();
    private $parameters = array();

    public function getUrl() {
        return $this->url;
    }

    public function setUrl($url) {
        $url = (string) $url;

        // make sure that the URL is suffixed with a forward slash
        if(substr($url,-1) !== '/') {
            $url .= '/';   
        }
        
        $this->url = $url;
    }

    public function getTarget() {
        return $this->target;
    }

    public function setTarget($target) {
        $this->target = $target;
    }

    public function getMethods() {
        return $this->methods;
    }

    public function setMethods(array $methods) {
        $this->methods = $methods;
    }

    public function getName() {
        return $this->name;
    }

    public function setName($name) {
        $this->name = (string) $name;
    }

    public function setFilters(array $filters) {
        $this->filters = $filters;
    }

    public function getRegex() {
        return preg_replace_callback("/:(\w+)/", array(&$this, 'substituteFilter'), $this->url);
    }

    private function substituteFilter($matches) {
        if (isset($matches[1]) && isset($this->filters[$matches[1]])) {
            return $this->filters[$matches[1]];
        }
    
        return "([\w-]+)";
    }

    public function getParameters() {
        return $this->parameters;
    }

    public function setParameters(array $parameters) {
        $this->parameters = $parameters;
    }
}
