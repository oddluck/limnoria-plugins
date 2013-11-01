<?php
    $db = new PDO('sqlite:/tmp/trivia.t');

    if ($db) {
        $q = $db->query('SELECT * FROM triviareport LIMIT 10');
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            echo "First 10 Reports: \n";
            foreach($result as $res) {
                echo $res['reported_at'] . ' ' . $res['channel'] . ' ' . $res['username'] . ' ' . $res['report_text'] . "\n";
            }
        }
    } else {
        die($err);
    }
?>