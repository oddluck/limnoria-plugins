<?php
class LoginUser
{
    protected $username;
    protected $capabilty;

    public function __construct($username, $capabilty) {
        $this->username = $username;
        $this->capabilty = $capabilty;
    }

    public function getUsername() {
        return $this->username;
    }

    public function getCapability() {
        return $this->capabilty;
    }
}
