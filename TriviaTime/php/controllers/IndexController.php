<?php
class IndexController extends Controller
{
    public function indexAction() {
        $container = $this->container;
        $storage = $container->getStorage();

        $errorsQ = array();
        $resultQ = array();
        try {
            $resultQ = $storage->getRecentAskedQuestions();
        } catch(StorageSchemaException $e) {
            $errorsQ[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $errorsQ[] = "Error: Database is not available";
        }

        $errorsA = array();
        $resultA = array();
        try {
            $resultA = $storage->getRecentActivities();
        } catch(StorageSchemaException $e) {
            $errorsA[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
            $errorsA[] = "Error: Database is not available";
        }
        $storage->close();

        $values = array();

        $values['resultQuestions'] = $resultQ;
        $values['errorsQuestions'] = $errorsQ;
        $values['resultActivities'] = $resultA;
        $values['errorsActivities'] = $errorsA;

        $container->setTitle('Home');

        $container->render('home.html.php', $values);
    }
}
