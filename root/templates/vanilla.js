const form = new FormData();

form.append(
    "smtp_host",
    "smtp.gmail.com"
);

form.append(
    "subject",
    "Hello"
);

form.append(
    "recipients",
    "user@example.com"
);

form.append(
    "attachments",
    fileInput.files[0]
);

await fetch(
    "http://localhost:5000/send-email",
    {
        method: "POST",
        body: form
    }
);