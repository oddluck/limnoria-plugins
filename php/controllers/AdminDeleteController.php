<?php
class AdminDeleteController extends Controller
{
    public function removeDeleteAction($args) {
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
            $response = $this->createResponseArray(true, 'error', 'You must be logged in to remove pending deletions.');
            $this->doResponse($response, $format);
        }

        try {
            $reportExists = $this->container->storage->deleteExists($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        if(!$reportExists) {
            $response = $this->createResponseArray(true, 'error', 'That pending deletion does not exist.');
            $this->doResponse($response, $format);
        }

        $count = 0;
        try {
            $this->container->storage->removeDelete($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        $response = $this->createResponseArray(false, 'success', 'Pending deletion has been removed.');
        $this->doResponse($response, $format);
    }

    public function createDeleteAction($args) {

    }

    public function acceptDeleteAction($args) {
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
            $response = $this->createResponseArray(true, 'error', 'You must be logged in to accept pending deletions.');
            $this->doResponse($response, $format);
        }

        try {
            $delete = $this->container->storage->getDeleteById($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        if(count($delete) < 1) {
            $response = $this->createResponseArray(true, 'error', 'That pending deletion does not exist.');
            $this->doResponse($response, $format);
        }
        $delete = $delete[0];

        $count = 0;
        try {
            $this->container->storage->removeQuestion($delete['line_num']);
            $this->container->storage->removeDelete($id);
        } catch(StorageException $e) {
            $this->doDbErrorResponse($format);
        }
        $response = $this->createResponseArray(false, 'success', 'Deletion has been accepted. Question has been deleted.');
        $this->doResponse($response, $format);
    } 
    
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

    
}
