import smtplib
import threading
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import logging

logger = logging.getLogger(__name__)

# Gmail Credentials
SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 465
SENDER_EMAIL = "kuriankurian405@gmail.com"
SENDER_PASSWORD = "fjlu gcli yezu wbmo"

def _send_email_async(to_email, subject, html_content):
    """Internal function to send an email asynchronously."""
    try:
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"Fancy Store <{SENDER_EMAIL}>"
        msg["To"] = to_email

        # Attach the HTML content
        part = MIMEText(html_content, "html")
        msg.attach(part)

        # Connect to Gmail SMTP server using SSL
        with smtplib.SMTP_SSL(SMTP_SERVER, SMTP_PORT) as server:
            server.login(SENDER_EMAIL, SENDER_PASSWORD)
            server.sendmail(SENDER_EMAIL, to_email, msg.as_string())
            
        logger.info(f"Email '{subject}' sent successfully to {to_email}")
        
    except Exception as e:
        logger.error(f"Failed to send email to {to_email}. Error: {str(e)}")


def send_email(to_email, subject, html_content):
    """Dispatches the email in a separate background thread so the web request doesn't block."""
    if not to_email:
        logger.warning("No destination email provided.")
        return
        
    thread = threading.Thread(target=_send_email_async, args=(to_email, subject, html_content))
    thread.daemon = True
    thread.start()


def send_order_confirmation(order, user_email):
    """Send order confirmation email."""
    subject = f"Order Confirmation - #{order.order_number}"
    
    # Generate items list
    items_html = ""
    for item in order.items:
        items_html += f"<li>{item.get('name', 'Product')} x{item.get('quantity', 1)} (₹{item.get('price', 0):,.2f})</li>"

    # Simple, clean HTML template
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #0d6efd; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Thank You For Your Order!</h1>
        </div>
        <div style="padding: 20px;">
            <p>Hi {order.shipping_address.get('full_name', 'Customer')},</p>
            <p>Your order <strong>#{order.order_number}</strong> has been successfully placed. We are currently processing it.</p>
            
            <h3 style="border-bottom: 1px solid #eee; padding-bottom: 10px;">Order Summary</h3>
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Total Amount:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">₹{order.grand_total:,.2f}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee;"><strong>Payment Status:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">{order.payment_status}</td>
                </tr>
                <tr>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; vertical-align: top;"><strong>Items:</strong></td>
                    <td style="padding: 8px 0; border-bottom: 1px solid #eee; text-align: right;">
                        <ul style="list-style-type: none; padding: 0; margin: 0; text-align: right;">
                            {items_html}
                        </ul>
                    </td>
                </tr>
            </table>

            <h3 style="border-bottom: 1px solid #eee; padding-bottom: 10px; margin-top: 20px;">Delivery Address</h3>
            <p style="margin: 0; line-height: 1.5;">
                {order.shipping_address.get('full_name')}<br>
                {order.shipping_address.get('address_line1', '')}<br>
                {order.shipping_address.get('city')}, {order.shipping_address.get('state')} {order.shipping_address.get('postal_code', '')}<br>
                Phone: {order.shipping_address.get('phone')}
            </p>
            
            <div style="margin-top: 30px; padding: 15px; background-color: #f8f9fa; border-radius: 5px; text-align: center; font-size: 14px;">
                If you have any questions about your order, please contact our support team.
            </div>
        </div>
    </div>
    """
    
    send_email(user_email, subject, html)


def send_order_cancellation(order, user_email):
    """Send order cancellation notification."""
    subject = f"Order Cancelled - #{order.order_number}"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #dc3545; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Order Cancelled</h1>
        </div>
        <div style="padding: 20px;">
            <p>Hi {order.shipping_address.get('full_name', 'Customer')},</p>
            <p>Your order <strong>#{order.order_number}</strong> has been cancelled successfully.</p>
            
            <div style="background-color: #fff3cd; color: #856404; padding: 15px; border: 1px solid #ffeeba; border-radius: 4px; margin: 20px 0;">
                If you had made any payments online, the refund process will be initiated shortly and typically reflects in your account within 5-7 business days.
            </div>

            <p style="margin-top: 30px;">
                We hope to serve you again soon!<br><br>
                Best Regards,<br>
                <strong>Fancy Store Team</strong>
            </p>
        </div>
    </div>
    """
    
    send_email(user_email, subject, html)


def send_otp_email(user_email, otp):
    """Send a one-time password (OTP) email for password reset."""
    subject = "Password Reset OTP - Fancy Store"
    
    html = f"""
    <div style="font-family: Arial, sans-serif; color: #333; max-width: 600px; margin: 0 auto; border: 1px solid #ddd; border-radius: 8px; overflow: hidden;">
        <div style="background-color: #0d6efd; color: white; padding: 20px; text-align: center;">
            <h1 style="margin: 0; font-size: 24px;">Reset Your Password</h1>
        </div>
        <div style="padding: 30px 20px; text-align: center;">
            <p style="font-size: 16px;">We received a request to reset the password associated with this email address.</p>
            <p style="font-size: 16px;">Here is your 6-digit verification code:</p>
            
            <div style="margin: 30px auto; background-color: #f4f4f4; padding: 20px; border-radius: 8px; display: inline-block; letter-spacing: 5px;">
                <strong style="font-size: 32px; color: #0d6efd;">{otp}</strong>
            </div>
            
            <p style="color: #777; font-size: 14px; margin-top: 20px;">
                This code is valid for 10 minutes. If you did not request a password reset, please ignore this email.
            </p>
            
            <p style="margin-top: 30px; font-size: 14px;">
                Best Regards,<br>
                <strong>Fancy Store Team</strong>
            </p>
        </div>
    </div>
    """
    
    send_email(user_email, subject, html)
