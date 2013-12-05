<?php
class Login
{
    protected $storage;
    protected $loggedIn = false;
    protected $user = null;

    public function __construct($storage) {
        $this->storage=$storage;
        $this->startSession();
        $this->isLoggedIn();
    }

    protected function startSession() {
        session_start();
    }

    protected function checkSessionLoggedIn() {
        if(!isset($_SESSION['username']) || !isset($_SESSION['loggedIn'])) {
            return false;
        }
        if(!empty($_SESSION['username']) && $_SESSION['loggedIn']) {
            return true;
        }
        return false;
    }

    protected function checkLoggedIn() {
        $this->loggedIn = $this->checkSessionLoggedIn();
    }

    protected function hashPassword($salt, $password) {
        return sha1($salt . $password);
    }

    protected function createUser($username, $capabilities) {
        $this->user = new User($username, $capabilities);
    }

    protected function ircToLower($str) {
        $ircLowerSymbols = array("\\"=>"|", "["=>"{", "]"=>"}", "~"=>"^");
        $str = strtr($str, $ircLowerSymbols);
        $str = strtolower($str);
        return $str;
    }

    public function isLoggedIn() {
        return $this->loggedIn;
    }

    public function getUser() {
        return $this->user;
    }

    public function login($username, $password) {
        if($this->loggedIn) {
            return true;
        }

        $usernameCanonical = $this->ircToLower($username);

        // Storage get salt, hashedPassword, capabilities for user
        $results = $this->storage->getLoginByUsernameCanonical($usernameCanonical);

        if(count($results) < 0) {
            return false;
        }

        $result = $results[0];

        $username = $result['username'];
        $salt = $result['salt'];
        $targetPassword = $result['password'];
        $capability = $result['capability'];
        $isHashed = $result['is_hashed'];

        $hashPassword = $password;
        if($isHashed) {
            $hashPassword = $this->hashPassword($salt, $password);
        }

        if($targetPassword == $hashPassword) {
            $_SESSION['username'] = $username;
            $_SESSION['loggedIn'] = true;
            $this->loggedIn = true;
            $this->createUser($username, $capability);
            return true;
        }
        return false;
    }

    public function logout() {
        $_SESSION = array();
        session_destroy();
        $this->loggedIn = false;
        $this->user = null;
    }
}
