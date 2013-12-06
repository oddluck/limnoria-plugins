<?php
class LoginController extends Controller
{
    protected function getPostVariable($key) {
        if(array_key_exists($key, $_POST)) {
            $value = $_POST[$key];
        }
        if(!isset($value)) {
          $value = null;
        }
        return $value;
    }

    protected function doRedirect() {
        $defaultPage = $this->container->config['defaultLoginRedirectPage'];
        if(array_key_exists('lastPage', $_SESSION)) {
            $this->redirect($_SESSION('lastPage'));
        } else {
            $this->redirect($this->container->router->generate($defaultPage));
        } 
    }

    public function loginAction() {
        $login = $this->container->getLogin();

        if($login->isLoggedIn()) {
            $this->doRedirect();
        }

        $errors = array();
        if($_SERVER['REQUEST_METHOD'] === 'POST') {
            $username = $this->getPostVariable("username");
            $password = $this->getPostVariable("password");

            if(empty($username)) {
                $errors['username'] = "Please enter a Username.";
            }
            if(empty($password)) {
                $errors['password'] = "Please enter a Password.";
            }
            if(!empty($username) && !empty($password)) {
                try {
                    if($login->login($username, $password)) {
                        $this->container->setNotice("<strong>Success!</strong> You have been successfully logged in.");
                        $this->doRedirect();
                    } else {
                        $errors['login'] = "Invalid credentials. Please check your username and password, and try again.";
                    }
                } catch (StorageException $e) {
                    $errors['login'] = "Error: Database is not available.";
                }


            }
        }

        $values = array();
        $values['errors'] = $errors;

        $this->container->setTitle("Login");
        $this->container->render("login.html.php", $values);        
    }

    public function logoutAction() {
        $login = $this->container->getLogin();

        $login->logout();

        // force a new session, for the notice
        $this->container->login = new Login($this->container->storage);

        $this->container->setNotice("<strong>Success!</strong> You have been successfully logged out.");
        $this->doRedirect();
    }
}
