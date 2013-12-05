<?php
class Paginator
{
    protected $key = 'page';
    protected $target = '';
    protected $next = '&raquo;';
    protected $previous = '&laquo;';
    protected $crumbs = 5;
    protected $resultsPerPage = 10;
    protected $currentPage;
    protected $totalResults;

    public function __construct($currentPage, $totalResults, $resultsPerPage=null, $key=null, $target=null) {
        $this->currentPage = $currentPage;
        $this->totalResults = $totalResults;
        if(!is_null($key)) {
            $this->key = $key;
        }
        if(!is_null($resultsPerPage)) {
            $this->resultsPerPage = $resultsPerPage;
        }
        if(!is_null($target)) {
            $this->target = $target;
        } else {
            $this->target = $this->getCurrentURI();
        }
    }

    protected function getCurrentURI() {
        return $_SERVER['REQUEST_URI'];
    }

    protected function replacePageVariable($uri, $pageNumber) {
        $pathInfo = parse_url($uri);
        if(array_key_exists('query', $pathInfo)) {
            $queryString = $pathInfo['query'];
        } else {
            $queryString = '';
        }
        parse_str($queryString, $queryArray);
        $queryArray[$this->key] = $pageNumber;
        if($pageNumber == 1) {
            unset($queryArray[$this->key]);
        }
        $queryString = http_build_query($queryArray);
        $new = $pathInfo['path'];
        if($queryString != ''){
            $new .=  '?' . $queryString;
        }
        return $new;  
    }

    protected function getMaxPages() {
        if($this->totalResults==0) {
            return 1;
        }
        $max = intval($this->totalResults / $this->resultsPerPage);
        if($this->totalResults % $this->resultsPerPage > 0) {
            $max++;
        }
        return intval($max);
    }

    public function paginate() {
        echo '<div class="pagination"><ul>';
        $startCrumb = $this->currentPage - ($this->crumbs-1)/2;
        if($startCrumb < 1) {
            $startCrumb = 1;
        }

        $endCrumb = $startCrumb + $this->crumbs-1;
        if($endCrumb > $this->getMaxPages()) {
            $endCrumb = $this->getMaxPages();
        }

        while($endCrumb - $startCrumb < $this->crumbs - 1) {
            if($startCrumb <= 1) {
                break;
            }
            $startCrumb--;
        }

        $startDots = false;
        if($startCrumb > 1) {
            $startDots = true;
        }
        $endDots = false;
        if($endCrumb < $this->getMaxPages()) {
            $endDots = true;
        }

        if($this->currentPage > 1) {
            echo '<li>';
            echo '<a href="';
            if($this->currentPage > $this->getMaxPages()) {
                echo $this->replacePageVariable($this->target, $this->getMaxPages());
            } else {
                echo $this->replacePageVariable($this->target, $this->currentPage-1);
            }
            echo '">';
        } else {
            echo '<li class="disabled"><span>';
        }
        echo $this->previous;
        if($this->currentPage > 1) {
            echo '</a></li>';
        } else {
            echo '</span></li>';
        }

        if($startDots){
            echo '<li class="disabled"><span>...</span></li>';
        }

        for($i=$startCrumb;$i<=$endCrumb;$i++) {
            if($i!=$this->currentPage){
                echo '<li>';
                echo '<a href="';
                echo $this->replacePageVariable($this->target, $i);
                echo '">';
            } else {
                echo '<li class="active"><span>';
            }
            echo $i;
            if($i!=$this->currentPage){
                echo '</a></li>';
            } else {
                echo '</span></li>';
            }
        }

        if($endDots){
            echo '<li class="disabled"><span>...</span></li>';
        }

        if($this->currentPage < $this->getMaxPages()) {
            echo '<li>';
            echo '<a href="';
            if($this->currentPage < 1) {
                echo $this->replacePageVariable($this->target, 1);
            } else {
                echo $this->replacePageVariable($this->target, $this->currentPage+1);
            }
            echo '">';
        } else {
            echo '<li class="disabled"><span>';
        }
        echo $this->next;
        if($this->currentPage < $this->getMaxPages()) {
            echo '</a></li>';
        } else {
            echo '</span></li>';
        }
        echo '</ul></div>';
    }
}
