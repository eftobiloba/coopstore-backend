import requests
from string import Template
import os
from app.core.config import settings

def render_products(products: list) -> str:
    rows = ""
    for p in products:
        total_price = p["price"] * p["quantity"]
        rows += f"""
        <tr>
          <td>{p['name']}</td>
          <td>{p['quantity']}</td>
          <td>₦{p['price']:,.0f}</td>
          <td>₦{total_price:,.0f}</td>
        </tr>
        """
    return rows


def send_email_via_api(
    recipient: str,
    subject: str,
    html_filename: str,
    dynamic_values: dict = None,
):
    base_dir = os.path.dirname(os.path.abspath(__file__))  # /services
    assets_dir = os.path.join(base_dir, "..", "assets")
    html_file_path = os.path.join(assets_dir, html_filename)
    base_file_path = os.path.join(assets_dir, "base_email.html")

    if not os.path.exists(html_file_path):
        raise FileNotFoundError(f"HTML file not found: {html_file_path}")

    with open(html_file_path, "r", encoding="utf-8") as f:
        html_content = f.read()

    with open(base_file_path, "r", encoding="utf-8") as f:
        base_template = f.read()

    # Add rendered product rows if present
    if dynamic_values and "products" in dynamic_values:
        dynamic_values["rendered_items"] = render_products(dynamic_values["products"])

    # Format total_amount if present
    if dynamic_values and "total_amount" in dynamic_values:
        dynamic_values["total_amount"] = f"₦{dynamic_values['total_amount']:,.0f}"

    # Merge content into base
    page_content = Template(html_content).safe_substitute(dynamic_values or {})
    full_html = base_template.replace("${content}", page_content)
    full_html = Template(full_html).safe_substitute({"subject": subject, **(dynamic_values or {})})

    payload = {
        "recipient": recipient,
        "subject": subject,
        "html_content": full_html,
        "dynamic_values": dynamic_values or {}
    }

    headers = {
        "Content-Type": "application/json",
        "X-API-Key": settings.api_key
    }

    url = f"{settings.base_url}/notifications/send-raw"
    response = requests.post(url, json=payload, headers=headers)

    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to send email: {response.status_code} {response.text}")
