<?php
    $db = new PDO('sqlite:/tmp/trivia.t');

    if ($db) {
        $q = $db->query('SELECT * FROM triviagameslog ORDER BY id DESC LIMIT 10');
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            echo "Last 10 questions asked: \n";
            foreach($result as $res) {
                echo $res['asked_at'] . ' Round:'  . $res['channel'] . ':' . $res['round_num'] . ' `' . $res['question'] . '` line number:' . $res['line_num'] . "\n";
            }
        }
    } else {
        die($err);
    }
?>