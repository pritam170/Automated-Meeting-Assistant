import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

class Mailer:
    @staticmethod
    def test_connection(host, port, username, password, use_ssl=False, use_tls=True):
        """
        Tests the SMTP server connection with the given settings.
        Returns (True, "Success message") or (False, "Error message").
        """
        try:
            if use_ssl:
                server = smtplib.SMTP_SSL(host, port, timeout=10)
            else:
                server = smtplib.SMTP(host, port, timeout=10)
                if use_tls:
                    server.starttls()
            
            if username and password:
                server.login(username, password)
            
            server.quit()
            return True, "SMTP connection established and authenticated successfully!"
        except Exception as e:
            return False, str(e)

    @staticmethod
    def send_task_email(smtp_config, recipient_email, recipient_name, meeting_title, meeting_summary, all_tasks, recipient_tasks):
        """
        Sends a beautifully formatted HTML email with action items.
        
        smtp_config: dict with host, port, username, password, use_ssl, use_tls, sender_email
        recipient_email: str
        recipient_name: str
        meeting_title: str
        meeting_summary: str
        all_tasks: list of dicts [{"task": "...", "assignee": "...", "due_date": "..."}]
        recipient_tasks: list of dicts (tasks assigned to this user)
        """
        sender_email = smtp_config.get("sender_email") or smtp_config.get("username")
        
        # Create message container
        msg = MIMEMultipart('alternative')
        msg['Subject'] = f"Action Items: {meeting_title}"
        msg['From'] = f"AuraMeet Assistant <{sender_email}>"
        msg['To'] = recipient_email

        # Build HTML content
        my_tasks_html = ""
        for item in recipient_tasks:
            my_tasks_html += f"""
            <div style="background-color: #f0f4ff; border-left: 4px solid #4f46e5; padding: 12px; margin-bottom: 10px; border-radius: 0 6px 6px 0;">
                <strong style="color: #1e1b4b; font-size: 15px;">Task:</strong> {item['task']}<br>
                <span style="color: #6b7280; font-size: 13px;"><strong>Due Date:</strong> {item['due_date']}</span>
            </div>
            """

        all_tasks_rows = ""
        for idx, item in enumerate(all_tasks):
            is_recipient = item['assignee'].lower() == recipient_name.lower()
            row_style = 'background-color: #f8fafc;' if idx % 2 == 0 else 'background-color: #ffffff;'
            if is_recipient:
                row_style = 'background-color: #eff6ff; font-weight: bold; border-left: 3px solid #3b82f6;'

            all_tasks_rows += f"""
            <tr style="{row_style}">
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #334155;">{item['task']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #334155;">{item['assignee']}</td>
                <td style="padding: 10px; border-bottom: 1px solid #e2e8f0; font-size: 14px; color: #64748b;">{item['due_date']}</td>
            </tr>
            """

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    background-color: #f1f5f9;
                    margin: 0;
                    padding: 0;
                    -webkit-font-smoothing: antialiased;
                }}
                .container {{
                    max-width: 600px;
                    margin: 30px auto;
                    background: #ffffff;
                    border-radius: 12px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1), 0 2px 4px -1px rgba(0,0,0,0.06);
                }}
                .header {{
                    background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                    color: white;
                    padding: 30px 24px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 24px;
                    font-weight: 700;
                    letter-spacing: -0.5px;
                }}
                .header p {{
                    margin: 8px 0 0 0;
                    font-size: 14px;
                    opacity: 0.9;
                }}
                .content {{
                    padding: 24px;
                }}
                .greeting {{
                    font-size: 16px;
                    color: #1e293b;
                    margin-bottom: 20px;
                }}
                .section-title {{
                    font-size: 18px;
                    font-weight: 600;
                    color: #0f172a;
                    border-bottom: 2px solid #e2e8f0;
                    padding-bottom: 8px;
                    margin-top: 24px;
                    margin-bottom: 16px;
                }}
                .summary-box {{
                    background-color: #f8fafc;
                    border-radius: 8px;
                    padding: 16px;
                    border: 1px solid #e2e8f0;
                    color: #475569;
                    font-size: 14px;
                    line-height: 1.6;
                }}
                .task-table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin-top: 10px;
                }}
                .task-table th {{
                    background-color: #f1f5f9;
                    color: #475569;
                    text-align: left;
                    padding: 10px;
                    font-size: 12px;
                    font-weight: 600;
                    text-transform: uppercase;
                    border-bottom: 2px solid #cbd5e1;
                }}
                .footer {{
                    background-color: #f8fafc;
                    text-align: center;
                    padding: 16px;
                    font-size: 12px;
                    color: #94a3b8;
                    border-top: 1px solid #e2e8f0;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>AuraMeet Summary</h1>
                    <p>{meeting_title}</p>
                </div>
                <div class="content">
                    <div class="greeting">
                        Hi <strong>{recipient_name}</strong>,
                        <p>Here are your action items and summary from the recent meeting.</p>
                    </div>

                    <div class="section-title">Your Action Items</div>
                    {my_tasks_html}

                    <div class="section-title">Meeting Summary</div>
                    <div class="summary-box">
                        {meeting_summary}
                    </div>

                    <div class="section-title">All Meeting Action Items</div>
                    <table class="task-table">
                        <thead>
                            <tr>
                                <th>Task</th>
                                <th>Assignee</th>
                                <th>Due Date</th>
                            </tr>
                        </thead>
                        <tbody>
                            {all_tasks_rows}
                        </tbody>
                    </table>
                </div>
                <div class="footer">
                    Sent automatically by AuraMeet Assistant. Do not reply directly to this email.
                </div>
            </div>
        </body>
        </html>
        """
        
        msg.attach(MIMEText(html_content, 'html'))
        
        # Connect and send
        host = smtp_config.get("host")
        port = smtp_config.get("port")
        username = smtp_config.get("username")
        password = smtp_config.get("password")
        use_ssl = smtp_config.get("use_ssl", False)
        use_tls = smtp_config.get("use_tls", True)

        if use_ssl:
            server = smtplib.SMTP_SSL(host, port, timeout=15)
        else:
            server = smtplib.SMTP(host, port, timeout=15)
            if use_tls:
                server.starttls()

        if username and password:
            server.login(username, password)
            
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
