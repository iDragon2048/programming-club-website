<?php
// Define your secret password here
$my_secret = "put_a_random_password_here";

// Check if the request has the correct secret header
if (!isset($_SERVER['HTTP_X_SECRET']) || $_SERVER['HTTP_X_SECRET'] !== $my_secret) {
    http_response_code(403); // Send an access denied error
    die("Unauthorized");
}

// If the password matches, save the file
file_put_contents('progress.json', file_get_contents('php://input'));
?>