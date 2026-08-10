from django.core.signing import TimestampSigner, BadSignature
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse

signer = TimestampSigner()

def generate_magic_token(identifier):
    """Generates a signed token."""
    return signer.sign(str(identifier))

def verify_magic_token(token):
    """
    Verifies token validity without expiration limit.
    The link will work indefinitely unless SECRET_KEY changes.
    """
    try:
        value = signer.unsign(token)
        return value
    except BadSignature:
        return None

def send_order_magic_link(order, request=None):
    """Sends a beautifully styled order confirmation email via ZeptoMail."""
    token = generate_magic_token(order.tracking_id)
    
    domain = request.build_absolute_uri('/')[:-1] if request else "https://storycandy.co"
    magic_url = f"{domain}{reverse('order_magic_access', kwargs={'token': token})}"

    subject = f"Your Storycandy Order Confirmation (Ref: #{str(order.tracking_id)[:8].upper()})"

    # 1. Plain-text fallback for email clients without HTML support
    plain_message = (
        f"Hi {order.full_name},\n\n"
        f"Thank you for your purchase from Storycandy!\n\n"
        f"Order Ref: {order.tracking_id}\n"
        f"Total Paid: ₹{order.total_amount}\n\n"
        f"You can view your order details and delivery status anytime using this link:\n"
        f"{magic_url}\n\n"
        f"Warm regards,\n"
        f"The Storycandy Team"
    )

    # 2. Build item list rows dynamically for the HTML table
    items_html = ""
    for item in order.items.all():
        items_html += f"""
        <tr>
            <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; color: #333333; font-size: 14px;">
                <strong>{item.book.title}</strong>
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; color: #666666; font-size: 14px; text-align: center;">
                {item.quantity}
            </td>
            <td style="padding: 12px 0; border-bottom: 1px solid #f0f0f0; color: #333333; font-size: 14px; text-align: right; font-weight: 600;">
                ₹{item.price * item.quantity}
            </td>
        </tr>
        """

    # 3. Responsive HTML Email Body
    html_message = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Order Confirmation</title>
    </head>
    <body style="margin: 0; padding: 0; background-color: #f4f6f8; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; -webkit-font-smoothing: antialiased;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background-color: #f4f6f8; padding: 30px 10px;">
            <tr>
                <td align="center">
                    <table role="presentation" width="100%" style="max-width: 600px; background-color: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);">
                        
                        <!-- Header / Branding -->
                        <tr>
                            <td style="background-color: #ffffff; padding: 30px 40px 20px 40px; text-align: center; border-bottom: 3px solid #ff5a5f;">
                                <h1 style="margin: 0; font-size: 28px; font-weight: 800; color: #ff5a5f; letter-spacing: -0.5px;">
                                    Storycandy
                                </h1>
                                <p style="margin: 5px 0 0 0; font-size: 13px; color: #888888; text-transform: uppercase; letter-spacing: 1px;">
                                    Order Confirmation
                                </p>
                            </td>
                        </tr>

                        <!-- Body Content -->
                        <tr>
                            <td style="padding: 30px 40px;">
                                <h2 style="margin: 0 0 12px 0; font-size: 20px; font-weight: 700; color: #222222;">
                                    Hi {order.full_name},
                                </h2>
                                <p style="margin: 0 0 24px 0; font-size: 15px; line-height: 1.6; color: #555555;">
                                    Thank you for your order! We are preparing your books for dispatch. You can track your order status and details anytime using the button below.
                                </p>

                                <!-- Order Metadata Card -->
                                <div style="background-color: #f9fbfd; border: 1px solid #e8eeef; border-radius: 8px; padding: 16px 20px; margin-bottom: 24px;">
                                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0">
                                        <tr>
                                            <td style="font-size: 13px; color: #777777;">Order Reference:</td>
                                            <td style="font-size: 13px; color: #222222; font-weight: 700; text-align: right; font-family: monospace;">
                                                #{str(order.tracking_id)[:8].upper()}
                                            </td>
                                        </tr>
                                        <tr>
                                            <td style="font-size: 13px; color: #777777; padding-top: 6px;">Payment Status:</td>
                                            <td style="font-size: 13px; color: #2e7d32; font-weight: 700; text-align: right; padding-top: 6px;">
                                                Paid
                                            </td>
                                        </tr>
                                    </table>
                                </div>

                                <!-- Purchased Items Table -->
                                <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="margin-bottom: 24px; border-collapse: collapse;">
                                    <thead>
                                        <tr>
                                            <th align="left" style="padding-bottom: 8px; border-bottom: 2px solid #e5e5e5; font-size: 12px; color: #888888; text-transform: uppercase; letter-spacing: 0.5px;">Item</th>
                                            <th align="center" style="padding-bottom: 8px; border-bottom: 2px solid #e5e5e5; font-size: 12px; color: #888888; text-transform: uppercase; letter-spacing: 0.5px;">Qty</th>
                                            <th align="right" style="padding-bottom: 8px; border-bottom: 2px solid #e5e5e5; font-size: 12px; color: #888888; text-transform: uppercase; letter-spacing: 0.5px;">Amount</th>
                                        </tr>
                                    </thead>
                                    <tbody>
                                        {items_html}
                                    </tbody>
                                    <tfoot>
                                        <tr>
                                            <td colspan="2" align="right" style="padding-top: 16px; font-size: 15px; font-weight: 700; color: #222222;">Total Paid:</td>
                                            <td align="right" style="padding-top: 16px; font-size: 18px; font-weight: 800; color: #ff5a5f;">₹{order.total_amount}</td>
                                        </tr>
                                    </tfoot>
                                </table>

                                <!-- CTA Button (Magic Link) -->
                                <div style="text-align: center; margin: 32px 0 24px 0;">
                                    <a href="{magic_url}" target="_blank" style="background-color: #ff5a5f; color: #ffffff; text-decoration: none; font-size: 15px; font-weight: 700; padding: 14px 28px; border-radius: 8px; display: inline-block; box-shadow: 0 4px 10px rgba(255, 90, 95, 0.3);">
                                        View Order & Delivery Status
                                    </a>
                                </div>

                                <p style="margin: 0; font-size: 12px; color: #999999; text-align: center; line-height: 1.5;">
                                    No password required. Keep this email saved to view your order receipt anytime.
                                </p>
                            </td>
                        </tr>

                        <!-- Footer -->
                        <tr>
                            <td style="background-color: #f9fbfd; padding: 20px 40px; text-align: center; border-top: 1px solid #e8eeef;">
                                <p style="margin: 0; font-size: 13px; color: #777777; font-weight: 600;">
                                    Storycandy
                                </p>
                                <p style="margin: 4px 0 0 0; font-size: 12px; color: #aaaaaa;">
                                    Curated books for young curious minds
                                </p>
                            </td>
                        </tr>

                    </table>
                </td>
            </tr>
        </table>
    </body>
    </html>
    """

    # Dispatch email with HTML body attached
    send_mail(
        subject=subject,
        message=plain_message,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[order.email],
        html_message=html_message,
        fail_silently=False,
    )