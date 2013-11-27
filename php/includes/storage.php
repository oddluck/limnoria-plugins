<?php
    class Storage
    {
        protected $dbLocation;
        protected $dbType;
        protected $db = null;

        public function __construct($dbLocation, $dbType='sqlite:') {
            $this->dbLocation = $dbLocation;
            $this->dbType = $dbType;
            $this->connect();
        }

        public function connect() {
            if(is_null($this->db)) {
                try {
                    $this->db = new PDO($this->dbType . $this->dbLocation);
                    if(!$this->db) {
                        throw new StorageConnectionException($err);
                    }
                } catch (Exception $e) {

                }
            }
        }

        public function close() {
            $this->db = null;
        }

        public function getTopReports($page, $max) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            if($page < 1) {
                $page = 1;
            }
            if($max < 1) {
                $max = 1;
            }
            $q = $this->db->prepare('SELECT tr.*, tq.question as original  
                    FROM triviareport tr 
                    INNER JOIN triviaquestion tq 
                    ON tq.id=question_num 
                    ORDER BY id DESC LIMIT :offset, :maxResults');
            $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getCountReports() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->query('SELECT count(id) FROM triviareport');
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchColumn();
            return $result;
        }

        public function getTopNewQuestions($page, $max) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            if($page < 1) {
                $page = 1;
            }
            if($max < 1) {
                $max = 1;
            }
            $q = $this->db->prepare('SELECT tq.*  FROM triviatemporaryquestion tq ORDER BY tq.id DESC LIMIT :offset, :maxResults');
            $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getCountNewQuestions() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->query('SELECT count(id) FROM triviatemporaryquestion');
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchColumn();
            return $result;
        }

        public function getTopEdits($page, $max) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            if($page < 1) {
                $page = 1;
            }
            if($max < 1) {
                $max = 1;
            }
            $q = $this->db->prepare('SELECT te.*, tq.question as original  
                    FROM triviaedit te 
                    INNER JOIN triviaquestion tq 
                    ON tq.id=question_id 
                    ORDER BY id DESC LIMIT :offset, :maxResults');
            $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getCountEdits() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->query('SELECT count(id) FROM triviaedit');
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchColumn();
            return $result;
        }

        public function getDayTopScores() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $day = date('j');
            $month = date('m');
            $year = date('Y');
            $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE day=:day AND year=:year AND month=:month GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
            $q->execute(array(':day'=>$day, ':year'=>$year, ':month'=>$month));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getWeekTopScores() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $sqlClause = '';
            $day = date('N')-1;
            $week = new DateTime();
            $interval = new DateInterval('P'.$day.'D');
            $week->sub($interval);
            $interval = new DateInterval('P1D');
            for($i=0;$i<7;$i++) {
                if($i>0) {
                    $sqlClause .= ' or ';
                }
                $sqlClause .= '(day=' . $week->format('j') . 
                                    ' and month=' . $week->format('n') .
                                    ' and year=' . $week->format('Y') . 
                                    ')';
                $week->add($interval);
            }
            $q = $this->db->query("SELECT username, sum(points_made) as points FROM triviauserlog WHERE $sqlClause GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getMonthTopScores() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $month = date('m');
            $year = date('Y');
            $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year AND month=:month GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
            $q->execute(array(':year'=>$year, ':month'=>$month));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getYearTopScores() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $year = date('Y');
            $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year GROUP BY username_canonical ORDER BY points DESC LIMIT 10");
            $q->execute(array(':year'=>$year));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getUserLikeUsernameCanonical($usernameCanonical, $page, $max) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            if($page < 1) {
                $page = 1;
            }
            if($max < 1) {
                $max = 1;
            }
            $q = $this->db->prepare('select
                    tl.username,
                    sum(tl.points_made) as points,
                    sum(tl.num_answered) as total
                    from triviauserlog tl
                    where tl.username_canonical like :username
                    group by tl.username_canonical
                    limit :offset, :maxResults
                    ');
            $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max, ':username'=>'%'.$usernameCanonical.'%'));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getCountUserLikeUsernameCanonical($usernameCanonical) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->prepare('select
                    count(distinct(tl.username_canonical))
                    from triviauserlog tl
                    where tl.username_canonical like :username
                    ');
            $q->execute(array(':username'=>'%'.$usernameCanonical.'%'));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchColumn();
            return $result;
        }

        public function getRecentAskedQuestions() {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->query('SELECT asked_at, channel, round_num, question, line_num FROM triviagameslog ORDER BY id DESC LIMIT 10');
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        public function getUserProfileInformation($usernameCanonical) {
            if(!$this->isConnected()) {
                throw new StorageConnectionException();
            }
            $q = $this->db->prepare('select
                    tl.username as usrname,
                    sum(tl2.t * (tl2.n / (select sum(num_answered) from triviauserlog where username_canonical=:username))) as count,
                    sum(tl2.p * (tl2.n / (select sum(num_answered) from triviauserlog where username_canonical=:username))) as score,
                    (select sum(points_made) from triviauserlog t3 where username_canonical=:username) as points,
                    (select sum(num_answered) from triviauserlog t4 where username_canonical=:username) as q_asked,
                    (select num_editted from triviausers where username_canonical=:username) as num_e,
                    (select num_editted_accepted from triviausers where username_canonical=:username) as num_e_accepted,
                    (select num_questions_added from triviausers where username_canonical=:username) as num_q,
                    (select num_questions_accepted from triviausers where username_canonical=:username) as num_q_accepted,
                    (select num_reported from triviausers where username_canonical=:username) as num_r
                    from (select tl3.id as id2, tl3.average_time * 1.0 as t, tl3.average_score * 1.0 as p, tl3.num_answered * 1.0 as n from triviauserlog tl3) tl2
                    inner join triviauserlog tl
                    on tl.username_canonical=:username
                    and tl.id=tl2.id2
                    limit 1');
            $q->execute(array(':username'=>$usernameCanonical));
            if ($q === false) {
                throw new StorageSchemaException();
            }
            $result = $q->fetchAll();
            return $result;
        }

        private function isConnected() {
            if(is_null($this->db)) {
                return false;
            }
            return true;
        }
    }

    class StorageException extends Exception { }

    class StorageSchemaException extends StorageException { }

    class StorageConnectionException extends StorageException { }