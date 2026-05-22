<?php

$url = "http://localhost:5000/send-email";


// ==========================================
// FORM DATA
// ==========================================

$postFields = [

    // SMTP CONFIG
    "smtp_host" => "smtp.gmail.com",
    "smtp_port" => "587",

    "smtp_username" => "admin@example.com",
    "smtp_password" => "yourpassword",

    "use_tls" => "true",
    "use_ssl" => "false",

    // EMAIL DATA
    "sender_email" => "admin@example.com",

    "sender_name" => "Lumex AI",

    "subject" => "Welcome Email",

    "text" => "Plain text fallback",

    "html" => "
        <h1>Welcome</h1>
        <p>Hello from Lumex AI</p>
    ",

    // MULTIPLE RECIPIENTS
    "recipients[]" => [
        "user1@example.com",
        "user2@example.com"
    ],

    // ATTACHMENTS
    "attachments[]" => [
        new CURLFile(
            __DIR__ . "/files/report.pdf",
            "application/pdf",
            "report.pdf"
        ),

        new CURLFile(
            __DIR__ . "/files/image.png",
            "image/png",
            "image.png"
        )
    ]
];


// ==========================================
// CURL REQUEST
// ==========================================

$ch = curl_init();

curl_setopt_array($ch, [

    CURLOPT_URL => $url,

    CURLOPT_RETURNTRANSFER => true,

    CURLOPT_POST => true,

    CURLOPT_POSTFIELDS => $postFields,
]);


// ==========================================
// EXECUTE
// ==========================================

$response = curl_exec($ch);

$statusCode = curl_getinfo(
    $ch,
    CURLINFO_HTTP_CODE
);

$error = curl_error($ch);

curl_close($ch);


// ==========================================
// RESPONSE
// ==========================================

if ($error) {

    echo "cURL Error: " . $error;

} else {

    echo "Status Code: " . $statusCode . PHP_EOL;

    echo $response;
}