<?php
class AdminNewController extends Controller
{
    protected $formats = array('html', 'json');

    protected function getGetVariable($key) {
        if(array_key_exists($key, $_GET)) {
            return $_GET[$key];
        }
        return null;
    }

    protected function getFormat() {
        $format = $this->getGetVariable('format');
        if(is_null($format) || !in_array($format, $this->formats)) {
            $format = 'html';
        }
        return $format;
    }

    protected function createResponseArray($errorBool, $status, $message) {
        $response = array();
        if($errorBool) {
            $errorBool = true;
        } else {
            $errorBool = false;
        }
        $response['error'] = $errorBool;
        $response['status'] = strval($status);
        $response['message'] = strval($message);
        return $response;
    }

    protected function doHtmlResponse($response) {
        if(isset($response['error'])){
            if($response['error']) {
                $this->setError("<strong>Error:</strong> " . $response['message']);
            } else {
                $this->setNotice("<strong>Success:</strong> " . $response['message']);
            }
        }
        $this->redirect($this->container->router->generate('reports'));
    }

    protected function doJsonResponse($response) {
        $this->render('admin.json.php', $response, false);
        die();
    }

    protected function doDbErrorResponse($format) {
        $response = $this->createResponseArray(true, "error", "Encountered database error.");
        $this->doResponse($response, $format);
    }

    protected function doResponse($response, $format) { 
        if($format==='json') {
            $this->doJsonResponse($response);
        } else {
            $this->doHtmlResponse($response);
        }
    }

    public function createNewAction($args) {

    }

    public function removeNewAction($args) {
        $format = $this->getFormat();

        $id = -1;
        if(array_key_exists('id', $args)) {
            $id = $args['id'];
        }

        if($id < 0) {
            $response = $this->createResponseArray(true, 'error', 'Id can only be positive.');
            $this->doResponse($response, $format);
        }

        $login = $this->container->login;
        if(!$login->isLoggedIn()) {
            $response = $this->createResponseArray(true, 'error', 'You must be logged in to remove new questions.');
            $this->doResponse($response, $format);
        }

        try {
            $newExists = $this->container->storage->temporaryQuestionExists($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        if(!$newExists) {
            $response = $this->createResponseArray(true, 'error', 'That new question does not exist.');
            $this->doResponse($response, $format);
        }

        try {
            $this->container->storage->removeTemporaryQuestion($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        $response = $this->createResponseArray(false, 'success', 'New question has been removed.');
        $this->doResponse($response, $format);
    }

    public function acceptNewAction($args) {
        $format = $this->getFormat();

        $id = -1;
        if(array_key_exists('id', $args)) {
            $id = $args['id'];
        }

        if($id < 0) {
            $response = $this->createResponseArray(true, 'error', 'Id can only be positive.');
            $this->doResponse($response, $format);
        }

        $login = $this->container->login;
        if(!$login->isLoggedIn()) {
            $response = $this->createResponseArray(true, 'error', 'You must be logged in to accept new questions.');
            $this->doResponse($response, $format);
        }

        try {
            $new = $this->container->storage->getTemporaryQuestionById($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        if(count($new) < 1) {
            $response = $this->createResponseArray(true, 'error', 'That new question does not exist.');
            $this->doResponse($response, $format);
        }
        $new = $new[0];

        $count = 0;
        try {
            $this->container->storage->insertQuestion($new['question']);
            $this->container->storage->removeTemporaryQuestion($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        $response = $this->createResponseArray(false, 'success', 'Question has been successfuly accepted.');
        $this->doResponse($response, $format);
    }
}
