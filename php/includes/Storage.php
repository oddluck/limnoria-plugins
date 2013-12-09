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
                    $this->db = null;
                }
            } catch(Exception $e) {
                $this->db = null;
            }
        }
    }

    public function close() {
        $this->db = null;
    }

    protected function ircToLower($str) {
        $ircLowerSymbols = array("\\"=>"|", "["=>"{", "]"=>"}", "~"=>"^");
        $str = strtr($str, $ircLowerSymbols);
        $str = strtolower($str);
        return $str;
    }

    public function getLoginByUsernameCanonical($usernameCanonical) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT *
                FROM trivialogin 
                WHERE username_canonical=:username
                LIMIT 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':username'=>$usernameCanonical));
        $result = $q->fetchAll();
        return $result;
    }

    public function getTimeSinceLastPlayed($usernameCanonical) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT last_updated
                FROM triviauserlog 
                WHERE username_canonical=:username
                ORDER BY last_updated DESC
                LIMIT 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':username'=>$usernameCanonical));
        $result = $q->fetchAll();
        return $result;
    }

    public function getTemporaryQuestionById($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT *
                FROM triviatemporaryquestion
                WHERE id=:id
                LIMIT 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchAll();
        return $result;
    }

    public function getDeleteById($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT *
                FROM triviadelete 
                WHERE id=:id
                LIMIT 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchAll();
        return $result;
    }

    public function getEditById($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT *
                FROM triviaedit 
                WHERE id=:id
                LIMIT 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchAll();
        return $result;
    }

    public function temporaryQuestionExists($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT count(id) FROM triviatemporaryquestion WHERE id=:id');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchColumn();
        if($result > 0) {
            return true;
        }
        return false;
    }

    public function insertQuestion($question) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('INSERT INTO triviaquestion VALUES (NULL, :question, :question, 0, 0, 0)');
        $result = $q->execute(array(':question'=>$question));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function deleteExists($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT count(id) FROM triviadelete WHERE id=:id');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchColumn();
        if($result > 0) {
            return true;
        }
        return false;
    }

    public function getTopDeletions($page, $max) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        if($page < 1) {
            $page = 1;
        }
        if($max < 1) {
            $max = 1;
        }
        $q = $this->db->prepare('SELECT td.*, tq.question as question  
                FROM triviadelete td 
                INNER JOIN triviaquestion tq 
                ON tq.id=td.line_num
                ORDER BY id DESC LIMIT :offset, :maxResults');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountDeletions() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT count(id) FROM triviadelete');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $result = $q->fetchColumn();
        return $result;
    }

    public function removeQuestion($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('DELETE FROM triviaquestion WHERE id=:id');
        $result = $q->execute(array(':id'=>$id));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function removeDelete($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('DELETE FROM triviadelete WHERE id=:id');
        $result = $q->execute(array(':id'=>$id));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function removeTemporaryQuestion($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('DELETE FROM triviatemporaryquestion WHERE id=:id');
        $result = $q->execute(array(':id'=>$id));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function removeReport($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('DELETE FROM triviareport WHERE id=:id');
        $result = $q->execute(array(':id'=>$id));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function removeEdit($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('DELETE FROM triviaedit WHERE id=:id');
        $result = $q->execute(array(':id'=>$id));
        if($result === false) {
            throw new StorageSchemaException();
        }
    }

    public function reportExists($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT count(id) FROM triviareport WHERE id=:id');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchColumn();
        if($result > 0) {
            return true;
        }
        return false;
    }

    public function editExists($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT count(id) FROM triviaedit WHERE id=:id');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchColumn();
        if($result > 0) {
            return true;
        }
        return false;
    }

    public function questionExists($id) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('SELECT count(id) FROM triviaquestion WHERE id=:id');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':id'=>$id));
        $result = $q->fetchColumn();
        if($result > 0) {
            return true;
        }
        return false;
    }

    public function updateQuestion($id, $question) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->prepare('UPDATE triviaquestion SET question=:question WHERE id=:id');
        $result = $q->execute(array(':id'=>$id, ':question'=>$question));
        if($result === false) {
            throw new StorageSchemaException();
        }
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
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountReports() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT count(id) FROM triviareport');
        if($q === false) {
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
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountNewQuestions() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT count(id) FROM triviatemporaryquestion');
        if($q === false) {
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
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountEdits() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT count(id) FROM triviaedit');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $result = $q->fetchColumn();
        return $result;
    }

    public function getDayTopScores($page=1, $max=10) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        if($page < 1) {
            $page = 1;
        }
        if($max < 1) {
            $max = 1;
        }
        $day = date('j');
        $month = date('m');
        $year = date('Y');
        $q = $this->db->prepare("SELECT username, 
                                sum(points_made) as points 
                                FROM triviauserlog 
                                WHERE day=:day 
                                AND year=:year 
                                AND month=:month 
                                GROUP BY username_canonical 
                                ORDER BY points DESC 
                                LIMIT :offset, :maxResults");
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max, ':day'=>$day, ':year'=>$year, ':month'=>$month));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountDayTopScores() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $day = date('j');
        $month = date('m');
        $year = date('Y');
        $q = $this->db->prepare('SELECT count(distinct(username_canonical)) 
                                FROM triviauserlog
                                WHERE day=:day 
                                AND year=:year 
                                AND month=:month');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':day'=>$day, ':year'=>$year, ':month'=>$month));
        $result = $q->fetchColumn();
        return $result;
    }

    protected function generateWeekSqlClause() {
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
        return $sqlClause;
    }

    public function getWeekTopScores($page=1, $max=10) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        if($page < 1) {
            $page = 1;
        }
        if($max < 1) {
            $max = 1;
        }
        $sqlClause = $this->generateWeekSqlClause();
        $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE $sqlClause GROUP BY username_canonical ORDER BY points DESC LIMIT :offset, :maxResults");
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountWeekTopScores() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $sqlClause = $this->generateWeekSqlClause();
        $q = $this->db->query('SELECT count(distinct(username_canonical)) 
                                FROM triviauserlog
                                WHERE $sqlClause');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $result = $q->fetchColumn();
        return $result;
    }

    public function getMonthTopScores($page=1, $max=10) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        if($page < 1) {
            $page = 1;
        }
        if($max < 1) {
            $max = 1;
        }
        $month = date('m');
        $year = date('Y');
        $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year AND month=:month GROUP BY username_canonical ORDER BY points DESC LIMIT :offset, :maxResults");
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max, ':year'=>$year, ':month'=>$month));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountMonthTopScores() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $month = date('m');
        $year = date('Y');
        $q = $this->db->prepare('SELECT count(distinct(username_canonical)) 
                                FROM triviauserlog
                                WHERE year=:year 
                                AND month=:month');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':year'=>$year, ':month'=>$month));
        $result = $q->fetchColumn();
        return $result;
    }

    public function getYearTopScores($page=1, $max=10) {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        if($page < 1) {
            $page = 1;
        }
        if($max < 1) {
            $max = 1;
        }
        $year = date('Y');
        $q = $this->db->prepare("SELECT username, sum(points_made) as points FROM triviauserlog WHERE year=:year GROUP BY username_canonical ORDER BY points DESC LIMIT :offset, :maxResults");
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max, ':year'=>$year));
        $result = $q->fetchAll();
        return $result;
    }

    public function getCountYearTopScores() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $year = date('Y');
        $q = $this->db->prepare('SELECT count(distinct(username_canonical)) 
                                FROM triviauserlog
                                WHERE year=:year');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':year'=>$year));
        $result = $q->fetchColumn();
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
        if($q === false) {
            throw new StorageSchemaException();
        }
        $likeString = '%'.$this->escapeLikeQuery($usernameCanonical).'%';
        $q->execute(array(':offset'=>($page-1) * $max, ':maxResults'=>$max, ':username'=>$likeString));
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
        if($q === false) {
            throw new StorageSchemaException();
        }
        $likeString = '%'.$this->escapeLikeQuery($usernameCanonical).'%';
        $q->execute(array(':username'=>$likeString));
        $result = $q->fetchColumn();
        return $result;
    }

    public function getRecentAskedQuestions() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT asked_at, channel, round_num, question, line_num FROM triviagameslog ORDER BY id DESC LIMIT 10');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $result = $q->fetchAll();
        return $result;
    }

    public function getRecentActivities() {
        if(!$this->isConnected()) {
            throw new StorageConnectionException();
        }
        $q = $this->db->query('SELECT * FROM triviaactivity ORDER BY id DESC LIMIT 10');
        if($q === false) {
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
                (select num_reported from triviausers where username_canonical=:username) as num_r,
                (select highest_streak from triviausers where username_canonical=:username) as highest_streak
                from (select tl3.id as id2, tl3.average_time * 1.0 as t, tl3.average_score * 1.0 as p, tl3.num_answered * 1.0 as n from triviauserlog tl3) tl2
                inner join triviauserlog tl
                on tl.username_canonical=:username
                and tl.id=tl2.id2
                limit 1');
        if($q === false) {
            throw new StorageSchemaException();
        }
        $q->execute(array(':username'=>$usernameCanonical));
        $result = $q->fetchAll();
        return $result;
    }

    public function isConnected() {
        if(is_null($this->db)) {
            return false;
        }
        return true;
    }

    protected function escapeLikeQuery($s) {
        $translations = array("%"=>"\\%", "_"=>"\\_");
        return strtr($s, $translations);
    }
}

class StorageException extends Exception { }

class StorageSchemaException extends StorageException { }

class StorageConnectionException extends StorageException { }
