<?php
class ReportsController extends Controller
{
    protected function getPageVariable($name) {
        if(array_key_exists($name, $_GET)) {
            $page = $_GET[$name];
        }
        if(!isset($page)) {
            $page = 1;
        }
        if($page < 1) {
            $page = 1;
        }
        return $page;
    }

    public function listAction($args) {
        $container = $this->container;
        $storage = $container->getStorage();

        $reportPage = $this->getPageVariable('rp');
        $editPage = $this->getPageVariable('ep');
        $newPage = $this->getPageVariable('np');
        $deletePage = $this->getPageVariable('dp');

        $maxResults = 5;

        $reportResultCount = 0;
        $reportResult = array();
        $reportErrors = array();
        try {
            $reportResult = $storage->getTopReports($reportPage, $maxResults);
            $reportResultCount = $storage->getCountReports();
        } catch(StorageSchemaException $e) {
            $reportErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $reportErrors[] = "Error: Database is not available";
        }

        $editResultCount = 0;
        $editResult = array();
        $editErrors = array();
        try {
            $editResult = $storage->getTopEdits($editPage, $maxResults);
            $editResultCount = $storage->getCountEdits();
        } catch(StorageSchemaException $e) {
            $editErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $editErrors[] = "Error: Database is not available";
        }

        $newResultCount = 0;
        $newResult = array();
        $newErrors = array();
        try {
            $newResult = $storage->getTopNewQuestions($newPage, $maxResults);
            $newResultCount = $storage->getCountNewQuestions();
        } catch(StorageSchemaException $e) {
            $newErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $newErrors[] = "Error: Database is not available";
        }

        $deleteResultCount = 0;
        $deleteResult = array();
        $deleteErrors = array();
        try {
            $deleteResult = $storage->getTopDeletions($deletePage, $maxResults);
            $deleteResultCount = $storage->getCountDeletions();
        } catch(StorageSchemaException $e) {
            $deleteErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $deleteErrors[] = "Error: Database is not available";
        }

        $values = array();
        $values['maxResults'] = $maxResults;

        $values['reportResultCount'] = $reportResultCount;
        $values['reportResult'] = $reportResult;
        $values['reportErrors'] = $reportErrors;
        $values['reportPage'] = $reportPage;

        $values['editResultCount'] = $editResultCount;
        $values['editResult'] = $editResult;
        $values['editErrors'] = $editErrors;
        $values['editPage'] = $editPage;

        $values['newResultCount'] = $newResultCount;
        $values['newResult'] = $newResult;
        $values['newErrors'] = $newErrors;
        $values['newPage'] = $newPage;

        $values['deleteResultCount'] = $deleteResultCount;
        $values['deleteResult'] = $deleteResult;
        $values['deleteErrors'] = $deleteErrors;
        $values['deletePage'] = $deletePage;

        $container->setTitle('Reports');

        $container->render('reports.html.php', $values);
    }
}
