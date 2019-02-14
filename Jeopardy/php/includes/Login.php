<?php
class Login
{
    protected $storage;
    protected $loggedIn = false;
    protected $user = null;

    public function __construct($storage) {
        $this->storage=$storage;
        $this->startSession();
        $this->checkLoggedIn();
    }

    protected function startSession() {
        session_start();
    }

    protected function endSession() {
        session_destroy();
    }

    protected function checkSessionLoggedIn() {
        if(!isset($_SESSION['username']) || !isset($_SESSION['loggedIn']) || !isset($_SESSION['capability'])) {
            return false;
        }
        if(!empty($_SESSION['username']) && $_SESSION['loggedIn']) {
            return true;
        }
        return false;
    }

    protected function checkLoggedIn() {
        $this->loggedIn = $this->checkSessionLoggedIn();

        if($this->isLoggedIn()) {
            $this->createUser($_SESSION['username'], $_SESSION['capability']);
        }
    }

    protected function hashPassword($salt, $password) {
        return sha1($salt . $password);
    }

    protected function createUser($username, $capabilities) {
        $this->user = new LoginUser($username, $capabilities);
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
        if($this->isLoggedIn()) {
            return true;
        }

        $usernameCanonical = $this->ircToLower($username);

        // Storage get salt, hashedPassword, capabilities for user
        try {
            $results = $this->storage->getLoginByUsernameCanonical($usernameCanonical);
        } catch(StorageException $e) {
            throw $e;
        }
        if(count($results) < 1) {
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
            $_SESSION['capability'] = $capability;
            $this->loggedIn = true;
            $this->createUser($username, $capability);
            return true;
        }
        return false;
    }

    public function logout() {
        $_SESSION = array();
        $this->endSession();
        $this->loggedIn = false;
        $this->user = null;
    }
}
