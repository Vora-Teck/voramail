import requests


url = "http://localhost:5000/send-email"


# ==========================================
# FORM DATA
# ==========================================

data = {

    # SMTP CONFIG
    "smtp_host": "smtp.gmail.com",
    "smtp_port": "587",

    "smtp_username": "admin@example.com",
    "smtp_password": "yourpassword",

    "use_tls": "true",
    "use_ssl": "false",

    # EMAIL DATA
    "sender_email": "admin@example.com",

    "sender_name": "Lumex AI",

    "subject": "Welcome Email",

    "text": "Plain text fallback",

    "html": """
    <h1>Welcome</h1>
    <p>Hello from Lumex AI</p>
    """
}


# ==========================================
# MULTIPLE RECIPIENTS
# ==========================================

recipient_data = [
    ("recipients", "user1@example.com"),
    ("recipients", "user2@example.com"),
]


# ==========================================
# ATTACHMENTS
# ==========================================

files = [

    (
        "attachments",

        (
            "report.pdf",

            open(
                "files/report.pdf",
                "rb"
            ),

            "application/pdf"
        )
    ),

    (
        "attachments",

        (
            "image.png",

            open(
                "files/image.png",
                "rb"
            ),

            "image/png"
        )
    ),
]


# ==========================================
# SEND REQUEST
# ==========================================

response = requests.post(

    url,

    data=[
        *data.items(),
        *recipient_data
    ],

    files=files
)


# ==========================================
# RESPONSE
# ==========================================

print("Status Code:", response.status_code)

print(response.json())