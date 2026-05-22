const axios = require("axios");

const FormData = require("form-data");

const fs = require("fs");


async function sendEmail() {

    try {

        const form = new FormData();

        // =========================
        // SMTP CONFIG
        // =========================

        form.append(
            "smtp_host",
            "smtp.gmail.com"
        );

        form.append(
            "smtp_port",
            "587"
        );

        form.append(
            "smtp_username",
            "admin@example.com"
        );

        form.append(
            "smtp_password",
            "yourpassword"
        );

        form.append(
            "use_tls",
            "true"
        );

        form.append(
            "use_ssl",
            "false"
        );

        // =========================
        // EMAIL DATA
        // =========================

        form.append(
            "sender_email",
            "admin@example.com"
        );

        form.append(
            "sender_name",
            "Lumex AI"
        );

        form.append(
            "subject",
            "Welcome Email"
        );

        form.append(
            "text",
            "Plain text fallback"
        );

        form.append(
            "html",
            `
            <h1>Welcome</h1>
            <p>Hello from Lumex AI</p>
            `
        );

        // MULTIPLE RECIPIENTS
        form.append(
            "recipients",
            "user1@example.com"
        );

        form.append(
            "recipients",
            "user2@example.com"
        );

        // =========================
        // ATTACHMENTS
        // =========================

        form.append(
            "attachments",

            fs.createReadStream(
                "./files/report.pdf"
            )
        );

        form.append(
            "attachments",

            fs.createReadStream(
                "./files/image.png"
            )
        );

        // =========================
        // API REQUEST
        // =========================

        const response = await axios.post(

            "http://localhost:5000/send-email",

            form,

            {
                headers: form.getHeaders(),

                maxBodyLength: Infinity,
                maxContentLength: Infinity
            }
        );

        console.log(response.data);

    } catch (error) {

        if (error.response) {

            console.error(
                error.response.data
            );

        } else {

            console.error(error.message);
        }
    }
}


sendEmail();