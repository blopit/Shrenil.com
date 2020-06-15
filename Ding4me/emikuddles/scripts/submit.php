<?php
if( isset($_POST['token'])) {

    if ($_POST['token'] != 'vh5qxkuKDH0bdL29y19Z') {
        die("incorrect token");
    }
    if (!isset($_POST['title'])) {
            die("missing title") ;
        } else if ($_POST['title'] == "") {
           die("missing title");
        }
    if (!isset($_POST['content'])) {
        die("missing content");
    } else if ($_POST['content'] == "") {
       die("missing content");
    }

    $servername = "ding4me.com";
    $username = "blopit";
    $password = "MPoppy123";
    $dbname = "ding4me";

    // Create connection
    $conn = new mysqli($servername, $username, $password, $dbname);
    // Check connection
    if ( $conn->connect_error ) {
        die("Connection failed: " . $conn->connect_error);
    }

    $post_title = $_POST['title'];
    $post_subtitle = $_POST['subtitle'];
    $post_content = $_POST['content'];

    $post_title = mysql_real_escape_string($post_title);
    $post_subtitle = mysql_real_escape_string($post_subtitle);
    $post_content = mysql_real_escape_string($post_content);

    $sql = "INSERT post (title, subtitle, content)
    VALUES ('$post_title','$post_subtitle', '$post_content')";

    if ($ conn->query($sql) === TRUE) {
        echo "New record created successfully";
    } else {
        echo "Error: " . $sql . "<br>" . $conn->error;
    }

    $conn->close();
}

?>