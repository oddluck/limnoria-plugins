<?php
    $db = new PDO('sqlite:/tmp/trivia.t');

    if ($db) {
        $q = $db->query('SELECT username, sum(points_made) as points FROM triviauserlog GROUP BY username ORDER BY points DESC LIMIT 10');
        if ($q === false) {
            die("Error: database error: table does not exist\n");
        } else {
            $result = $q->fetchAll();
            echo "Top 10 (All time): \n";
            foreach($result as $res) {
                echo $res['username'] . ' ' . $res['points'] . "\n";
            }
        }
    } else {
        die($err);
    }
?>