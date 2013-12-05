<?php
class IndexController extends Controller
{
    public function indexAction() {
        $container = $this->container;
        $storage = $container->getStorage();

        $errors = array();
        $result = array();
        try {
          $result = $storage->getRecentAskedQuestions();
        } catch(StorageSchemaException $e) {
          $errors[] = "Error: Database schema is not queryable";
        } catch(StorageConnectionException $e) {
          $errors[] = "Error: Database is not available";
        }
        $storage->close();

        $values = array();

        $values['result'] = $result;
        $values['errors'] = $errors;

        $container->setTitle('Home');

        $container->render('home.html.php', $values);
    }
}
