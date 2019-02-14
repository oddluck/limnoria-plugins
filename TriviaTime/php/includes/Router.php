<?php
class Router
{
    private $routes = array();
    private $namedRoutes = array();
    private $basePath = '';

    public function setBasePath($basePath) {
        $this->basePath = (string) $basePath;
    }

    public function map($routeUrl, $target = '', array $args = array()) {
        $route = new Route();
        $route->setUrl($this->basePath . $routeUrl);
        $route->setTarget($target);

        if(isset($args['methods'])) {
            $methods = explode(',', $args['methods']);
            $route->setMethods($methods);
        }

        if(isset($args['filters'])) {
            $route->setFilters($args['filters']);
        }

        if(isset($args['name'])) {
            $route->setName($args['name']);
            if (!isset($this->namedRoutes[$route->getName()])) {
                $this->namedRoutes[$route->getName()] = $route;
            }
        }

        $this->routes[] = $route;
    }

    public function matchCurrentRequest() {
        $requestMethod = $_SERVER['REQUEST_METHOD'];
        if(isset($_POST['_method']) && in_array(strtoupper($_POST['_method']),array('PUT','DELETE'))) {
            $requestMethod = strtoupper($_POST['_method']);
        }

        $requestUrl = $_SERVER['REQUEST_URI'];

        // strip GET variables from URL
        $pos = strpos($requestUrl, '?');
        if($pos !== false) {
            $requestUrl =  substr($requestUrl, 0, $pos);
        }

        return $this->match($requestUrl, $requestMethod);
    }

    public function match($requestUrl, $requestMethod = 'GET') {

        foreach($this->routes as $route) {
            // compare server request method with route's allowed http methods
            if(!in_array($requestMethod, $route->getMethods())) {
                continue;
            }

            // check if request url matches route regex. if not, return false.
            if (!preg_match("@^".$route->getRegex()."*$@i", $requestUrl, $matches)) {
                continue;
            }

            $params = array();
            if (preg_match_all("/:([\w-]+)/", $route->getUrl(), $argument_keys)) {
                // grab array with matches
                $argument_keys = $argument_keys[1];

                // loop trough parameter names, store matching value in $params array
                foreach ($argument_keys as $key => $name) {
                    if (isset($matches[$key + 1])) {
                        $params[$name] = $matches[$key + 1];
                    }
                }
            }
            $route->setParameters($params);
            return $route;
        }
        return false;
    }

    public function generate($routeName, array $params = array()) {
        // Check if route exists
        if (!isset($this->namedRoutes[$routeName])) {
            throw new Exception("No route with the name $routeName has been found.");
        }
        $route = $this->namedRoutes[$routeName];

        $url = $route->getUrl();
        // replace route url with given parameters
        if ($params && preg_match_all("/:(\w+)/", $url, $param_keys)) {
            // grab array with matches
            $param_keys = $param_keys[1];
            // loop trough parameter names, store matching value in $params array
            foreach ($param_keys as $i => $key) {
                if (isset($params[$key])) {
                    $url = preg_replace("/:(\w+)/", $params[$key], $url, 1);
                }
            }
        }
        return $url;
    }
}
