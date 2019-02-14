<?php
class StatsController extends Controller
{
    function statsAction() {
        $container = $this->container;
        $storage = $container->getStorage();

        $dayResult = array();
        $dayErrors = array();
        try {
            $dayResult = $storage->getDayTopScores(1, 10);
        } catch(StorageSchemaException $e) {
            $dayErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $dayErrors[] = "Error: Database is not available";
        }

        $weekResult = array();
        $weekErrors = array();
        try {
            $weekResult = $storage->getWeekTopScores(1, 10);
        } catch(StorageSchemaException $e) {
            $weekErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $weekErrors[] = "Error: Database is not available";
        }

        $monthResult = array();
        $monthErrors = array();
        try {
            $monthResult = $storage->getMonthTopScores(1, 10);
        } catch(StorageSchemaException $e) {
            $monthErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $monthErrors[] = "Error: Database is not available";
        }

        $yearResult = array();
        $yearErrors = array();
        try {
            $yearResult = $storage->getYearTopScores(1, 10);
        } catch(StorageSchemaException $e) {
            $yearErrors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $yearErrors[] = "Error: Database is not available";
        }

        $values = array();
        $values['dayResult'] = $dayResult;
        $values['dayErrors'] = $dayErrors;
        $values['weekResult'] = $weekResult;
        $values['weekErrors'] = $weekErrors;
        $values['monthResult'] = $monthResult;
        $values['monthErrors'] = $monthErrors;
        $values['yearResult'] = $yearResult;
        $values['yearErrors'] = $yearErrors;

        $container->setTitle('Stats');

        $container->render('stats.html.php', $values);

    }

    public function topAction($args) {
        $container = $this->container;
        $storage = $container->getStorage();

        $timespans = array('day'=>'Day', 'week'=>'Week', 'month'=>'Month', 'year'=>'Year');
        $timespan = 'day';
        $timeDesc = 'Day';
        if(array_key_exists('timespan', $args)) {
            if(array_key_exists(strtolower($args['timespan']), $timespans)) {
                $timespan = strtolower($args['timespan']);
                $timeDesc = $timespans[$timespan];
            }
        }

        if(array_key_exists('page', $_GET)) {
            $page = $_GET['page'];
        }
        if(!isset($page)) {
            $page = 1;
        }
        if($page < 1) {
            $page = 1;
        }

        $maxResults = 20;

        $resultCount = 0;
        $result = array();
        $errors = array();
        try {
            if ($timespan == 'week') {
                $result = $storage->getWeekTopScores($page, $maxResults);
                $resultCount = $storage->getCountWeekTopScores();
            } else if ($timespan == 'month') {
                $result = $storage->getMonthTopScores($page, $maxResults);
                $resultCount = $storage->getCountMonthTopScores();
            } else if ($timespan == 'year') {
                $result = $storage->getYearTopScores($page, $maxResults);
                $resultCount = $storage->getCountYearTopScores();    
            } else {
                $result = $storage->getDayTopScores($page, $maxResults);
                $resultCount = $storage->getCountDayTopScores();
            }
        } catch(StorageSchemaException $e) {
            $errors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $errors[] = "Error: Database is not available";
        }

        $values = array();
        $values['result'] = $result;
        $values['resultCount'] = $resultCount;
        $values['maxResults'] = $maxResults;
        $values['page'] = $page;
        $values['timespan'] = $timespan;
        $values['timeDesc'] = $timeDesc;
        $values['errors'] = $errors;

        $container->setTitle('Top Scores for ' . $timeDesc);

        $container->render('top.html.php', $values);
    }
}
