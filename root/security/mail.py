from root import config
import requests
import base64
import mimetypes
from flask import jsonify
import smtplib
from email.message import EmailMessage
from email.utils import formataddr
import html
import ssl


def image_to_data_url(url):
    mime_type, _ = mimetypes.guess_type(url)
    if not mime_type:
        mime_type = "image/png"
    with open(url, 'rb') as img_file:
        encoded_str = base64.b64encode(img_file.read()).decode("utf-8")

    return f"data:{mime_type};base64,{encoded_str}"


if config.DEBUG:
    host = 'http://127.0.0.1:10000'
else:
    host = 'https://mx.vorateck.com.ng'

site_logo = f"{host}/static/logos/full.png"
site_name = "VoraMX"
site_icon = image_to_data_url(config.LOGO_PATH)


def send_api_mail(account, message):
    try:
        smtp_host = account.smtp_host
        smtp_port = account.encryption["port"]
        encryption = account.encryption["encryption"]
        smtp_username = account.smtp_username
        smtp_password = account.decrypt_password()
        use_tls = encryption.lower() == "tls"
        use_ssl = encryption.lower() == "ssl"
        # =====================================
        # EMAIL DATA
        # =====================================
        sender_email = account.smtp_username
        # CUSTOM DISPLAY NAME
        sender_name = account.name
        recipients = message.recipients
        subject = message.subject
        html_content = message.message
        text_content = html.escape(message.message)
        # =====================================
        # VALIDATION
        # =====================================
        required_fields = [
            smtp_host, smtp_username, smtp_password,
            sender_email, subject, smtp_port, encryption
        ]
        if not all(required_fields):
            return {
                "error": "Missing required fields",
                "status": 400
            }

        if not recipients:
            return {
                "error": "No recipients provided",
                "status": 400
            }

        # =====================================
        # PROCESS ATTACHMENTS
        # =====================================
        """
        files = request.files.getlist("attachments")
    
        validated_files = validate_attachments(
            files
        )
        """
        # =====================================
        # BUILD EMAIL
        # =====================================
        try:
            msg = EmailMessage()
            msg["Subject"] = subject
            # CUSTOM DISPLAY NAME
            msg["From"] = formataddr(
                (sender_name, sender_email)
            )
            msg["To"] = ", ".join(recipients)
            # Plain text fallback
            msg.set_content(text_content)
            # HTML content
            if html_content:
                msg.add_alternative(
                    html_content,
                    subtype="html"
                )
            # =====================================
            # ATTACH FILES
            # =====================================
            """
            for file in validated_files:
                mime_main, mime_sub = (
                    file["mime_type"].split("/", 1)
                )
                msg.add_attachment(
                    file["data"], maintype=mime_main,
                    subtype=mime_sub, filename=file["filename"]
                )
            """
            # =====================================
            # SEND EMAIL
            # =====================================
            if use_ssl:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(smtp_host, smtp_port, context=context) as smtp:
                    smtp.login(smtp_username, smtp_password)
                    smtp.send_message(msg)
            else:
                with smtplib.SMTP(smtp_host, smtp_port) as smtp:
                    if use_tls: smtp.starttls()
                    smtp.login(smtp_username, smtp_password)
                    smtp.send_message(msg)
            return {
                "success": True,
                "message": "Email sent successfully"
            }
        except ValueError as e:
            return {
                "error": f"Error occurred: {str(e)}",
                "status": 400
            }
        except smtplib.SMTPAuthenticationError:
            return {
                "error": "SMTP authentication failed",
                "status": 401
            }

        except smtplib.SMTPException as e:
            return {
                "error": f"SMTP error: {str(e)}",
                "status": 500
            }
    except Exception as e:
        return {
            "error": f"Unexpected server error: {str(e)}",
            "status": 500
        }


def send_mail(subject, recipients, message, sender="ai@eduka.ng"):
    url = f"/v0/utilities/send_emails/"
    data = {
        "sender": sender, "subject": subject, "recipients": recipients,
        "message": base64.b64encode(message.encode()).decode()
    }
    try:
        res = requests.post(url, json=data, headers={
            "Content-Type": 'application/json',
            'X-API-KEY': config.INTERNAL_API_KEY
        })
        if res.status_code not in [200, 201]:
            try:
                resp = res.json()
                return False, resp.get("message", "Unknown error")
            except ValueError:
                return False, f"{res.text[:200]}"
        try:
            resp = res.json()
            return True, resp.get("message", "Success")
        except ValueError:
            return False, f"{res.text[:200]}"
    except requests.exceptions.ConnectionError:
        return False, "Network error: Unable to reach the server."

    except requests.exceptions.Timeout:
        return False, "Network error: The request timed out."

    except requests.exceptions.RequestException as e:
        return False, f"Unexpected network error: {str(e)}"
    except Exception as e:
        return False, f"{str(e)}"

def confirmation_email(receiver, code):
    subject = f"{site_name}: Email Confirmation Code"
    recipient_list = [receiver]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear user,<h4><br><br>
    <p>Kindly enter the confirmation code below to verify your email address.</p>
    <h1 style="text-align:center;margin:20px;letter-spacing:15px;">{code}</h1>
    <br><br>
    <p>We hope that you enjoy your experience with us.</p><br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    <br><br>
    <p><i>This is an auto-generated personalized email. Please do not reply.</i></p>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_sub_payment(user, trans):
    subject = f"{site_name}: Subscription Payment Notification"
    recipient_list = [user.email]  # List of recipient emails
    html_message = f"""
    <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <style>
                table {{width: 100%;margin: auto;border-collapse:collapse;}}
                table tr td, table tr th {{padding: 15px;font-size: 13px;border:1px solid black;}}
                .title {{margin-bottom: 30px;text-align:center;}}
                table tr th, table tr td {{text-align:left;}}
                table tr th:nth-child(1) {{width: 70px;}}
                table tr th:nth-child(1) {{width: calc(100% - 70px);}}
            </style>
        </head>
        <body>
            <center>
            <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
            </center>
            <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
            <h4>Dear {user.first_name or 'Esteemed Customer'},<h4><br><br>
            <p>You have successfully made a subscription payment of &#8358;{str(trans.amount)} for {user.duration}</p>
            <h3 class="title">Subscription Details</h3>
            <table>
                <tbody>
                    <tr>
                        <td>Subscription Plan</td>
                        <td>{user.plan.title}</td>
                    </tr>
                    <tr>
                        <td>Amount</td>
                        <td>&#8358;{str(trans.amount)}</td>
                    </tr>
                    <tr>
                        <td>Payment Date</td>
                        <td>{trans.timestamp.strftime("%B %d, %Y")}</td>
                    </tr>
                    <tr>
                        <td>Start Date</td>
                        <td>{user.start_date.strftime("%B %d, %Y")}</td>
                    </tr>
                    <tr>
                        <td>Duration</td>
                        <td>{user.duration}</td>
                    </tr>
                    <tr>
                        <td>Expiry Date</td>
                        <td>{user.expiry_date.strftime("%B %d, %Y")}</td>
                    </tr>
                </tbody>
            </table>
            <br><br>
            <p>Kindly visit your dashboard to generate/print your payment receipt.</p>
            <p>Thanks for your cooperation.</p>
            <br><br>
            <h4>Best Regards,<h4>
            <h4>{site_name}.</h4>
            <br><br>
            <p><i>This is an auto-generated personalized email. Please do not reply.</i></p>
            </div>
        </body>
    </html>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_card_expiration(card):
    subject = f"{site_name}: Card Expiration Notification"
    recipient_list = [card.user.email]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 150px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear {card.user.first_name},<h4><br><br>
    <p>Your debit card ({card.cardNumber}) has expired on {card.expiryDate}.</p>
    <p>Kindly add a new card on your dashboard to ensure your subscriptions are up to date and renewed when due.</p>
    <p>Your expired card will be removed from our system within 24 hours</p>
    <p>Thanks for your cooperation.</p>
    <br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    <br><br>
    <p><i>This is an auto-generated personalized email. Please do not reply.</i></p>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_password_email(receiver, user_name, new_password):
    subject = f"{site_name}: Password Reset Request"
    recipient_list = [receiver]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear {user_name},<h4><br><br>
    <p>You have requested a password reset for your account. your new temporary password is <span style="color:blue;font-weight:600">{new_password}</span></p>
    <p>Kindly ensure to change your password after logging in.</p><br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_sub_expiration(user):
    subject = f"{site_name}: Subscription Expiration Notification"
    recipient_list = [user.email]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear {user.first_name},<h4><br><br>
    <p>Your current subscription for <b>{user.plan.title} Plan</b> has expired on {user.expiry_date.strftime('%B %d, %Y')}.</p>
    <p>If you have enabled auto-renewal, your subscription will be auto renewed using your linked debit card for the current plan and duration.</p>
    <p>Thanks for your cooperation.</p>
    <br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_sub_reminder(user):
    subject = f"{site_name}: Subscription Expiration Reminder"
    recipient_list = [user.email]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear {user.first_name},<h4><br><br>
    <p>Your current subscription for <b>{user.plan.title} Plan</b> will expire on {user.expiry_date.strftime('%B %d, %Y')}.</p>
    <p>If you have enabled auto-renewal, your subscription will be auto renewed using your linked debit card for the current plan and duration when it expires.</p>
    <p>If you have already paid for another subscription, it will be automatically activated after your current plan expires.</p>
    <p>You can roll over your plan by renewing your subscription before it expires. This will also increase your chance of getting a discount.</p>
    <p>If you do not want to auto-renew, kindly turn off auto-renewal on your dashboard</p>
    <p>Thanks for your cooperation.</p>
    <br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    <br><br>
    <p><i>This is an auto-generated personalized email. Please do not reply.</i></p>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def send_renewal_failure(user, reason):
    subject = f"{site_name}: Subscription Renewal Failure"
    recipient_list = [user.email]  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 200px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear {user.first_name},<h4><br><br>
    <p>Your auto subscription renewal for <b>{user.plan.title} Plan</b> has failed because you have {reason}.</p>
    <br><br>
    <p>Thanks for your cooperation.</p>
    <br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

def contact_email(recipients, mssg):
    subject = f"{site_name}: New Message Alert"
    recipient_list = recipients  # List of recipient emails
    html_message = f"""
    <center>
    <img src="{site_logo}" alt="" style="width: 150px;height:auto;" />
    </center>
    <div style="text-align:left; font-family: 'Lucida Sans', 'Lucida Sans Regular', 'Lucida Grande', 'Lucida Sans Unicode', Geneva, Verdana, sans-serif;">
    <h4>Dear Admin,<h4><br><br>
    <p>You have a new message alert from <a href="mailto:{mssg.email}" style="color:blue;font-weight:600">{mssg.name}: {mssg.email}</a></p>
    <p><span style="color:blue;font-weight:600">Subject:</span> {mssg.subject}</p><br><br>
    <p><span style="color:blue;font-weight:600">Message:</span> {mssg.message}</p><br><br>
    <h4>Best Regards,<h4>
    <h4>{site_name}.</h4>
    </div>
    """
    stat, res = send_mail(subject, recipient_list, html_message)
    return stat, res

