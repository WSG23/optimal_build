"""Email service for sending notifications via SMTP."""

import logging
import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


class EmailConfig:
    """Email configuration from environment variables."""

    def __init__(self) -> None:
        self.smtp_host = os.getenv("SMTP_HOST", "localhost")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_password = os.getenv("SMTP_PASSWORD", "")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@optimalbuild.com")
        self.from_name = os.getenv("FROM_NAME", "OptimalBuild")
        self.use_tls = os.getenv("SMTP_USE_TLS", "true").lower() == "true"
        self.enabled = os.getenv("EMAIL_ENABLED", "false").lower() == "true"
        self.base_url = os.getenv("APP_BASE_URL", "http://localhost:3000")


email_config = EmailConfig()


class EmailService:
    """Service for sending emails."""

    def __init__(self, config: EmailConfig | None = None):
        self.config = config or email_config

    def is_enabled(self) -> bool:
        """Check if email sending is enabled."""
        return self.config.enabled

    def _get_smtp_connection(self) -> smtplib.SMTP:
        """Create an SMTP connection."""
        smtp = smtplib.SMTP(self.config.smtp_host, self.config.smtp_port)
        if self.config.use_tls:
            smtp.starttls()
        if self.config.smtp_user and self.config.smtp_password:
            smtp.login(self.config.smtp_user, self.config.smtp_password)
        return smtp

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: str | None = None,
    ) -> bool:
        """Send an email.

        Args:
            to_email: Recipient email address
            subject: Email subject
            html_content: HTML body of the email
            text_content: Plain text body (optional fallback)

        Returns:
            True if sent successfully, False otherwise
        """
        if not self.is_enabled():
            logger.info(f"Email disabled - would send to {to_email}: {subject}")
            return True  # Pretend success when disabled

        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = f"{self.config.from_name} <{self.config.from_email}>"
            msg["To"] = to_email

            # Add text part (fallback)
            if text_content:
                part1 = MIMEText(text_content, "plain")
                msg.attach(part1)

            # Add HTML part
            part2 = MIMEText(html_content, "html")
            msg.attach(part2)

            with self._get_smtp_connection() as smtp:
                smtp.sendmail(self.config.from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}: {subject}")
            return True

        except smtplib.SMTPException as e:
            logger.error(f"Failed to send email to {to_email}: {e}")
            return False
        except OSError as e:
            logger.error(f"Network error sending email to {to_email}: {e}")
            return False

    # --- Email Templates ---

    def _get_base_template(self, content: str) -> str:
        """Wrap content in base email template."""
        return f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
        }}
        .header {{
            background: linear-gradient(135deg, #1976d2 0%, #1565c0 100%);
            color: white;
            padding: 20px;
            text-align: center;
            border-radius: 8px 8px 0 0;
        }}
        .content {{
            background: #ffffff;
            padding: 30px;
            border: 1px solid #e0e0e0;
            border-top: none;
        }}
        .button {{
            display: inline-block;
            background: #1976d2;
            color: white !important;
            padding: 12px 24px;
            text-decoration: none;
            border-radius: 4px;
            margin: 20px 0;
        }}
        .button:hover {{
            background: #1565c0;
        }}
        .footer {{
            background: #f5f5f5;
            padding: 20px;
            text-align: center;
            font-size: 12px;
            color: #666;
            border: 1px solid #e0e0e0;
            border-top: none;
            border-radius: 0 0 8px 8px;
        }}
        .highlight {{
            background: #e3f2fd;
            padding: 15px;
            border-radius: 4px;
            margin: 15px 0;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1 style="margin: 0;">OptimalBuild</h1>
    </div>
    <div class="content">
        {content}
    </div>
    <div class="footer">
        <p>This email was sent by OptimalBuild. Please do not reply to this email.</p>
        <p>&copy; 2025 OptimalBuild. All rights reserved.</p>
    </div>
</body>
</html>
"""

    def send_team_invitation(
        self,
        to_email: str,
        inviter_name: str,
        project_name: str,
        role: str,
        invitation_token: str,
    ) -> bool:
        """Send a team invitation email."""
        accept_url = (
            f"{self.config.base_url}/accept-invitation?token={invitation_token}"
        )

        content = f"""
<h2>You've Been Invited!</h2>
<p>{inviter_name} has invited you to join the project <strong>{project_name}</strong> as a <strong>{role}</strong>.</p>

<div class="highlight">
    <p><strong>Project:</strong> {project_name}</p>
    <p><strong>Role:</strong> {role}</p>
    <p><strong>Invited by:</strong> {inviter_name}</p>
</div>

<p style="text-align: center;">
    <a href="{accept_url}" class="button">Accept Invitation</a>
</p>

<p style="font-size: 12px; color: #666;">
    This invitation will expire in 7 days. If you didn't expect this invitation, you can safely ignore this email.
</p>

<p style="font-size: 12px; color: #666;">
    If the button doesn't work, copy and paste this link into your browser:<br>
    <a href="{accept_url}">{accept_url}</a>
</p>
"""
        html = self._get_base_template(content)
        text = f"""
You've Been Invited!

{inviter_name} has invited you to join the project "{project_name}" as a {role}.

Project: {project_name}
Role: {role}
Invited by: {inviter_name}

Accept the invitation by visiting:
{accept_url}

This invitation will expire in 7 days.
"""
        return self.send_email(
            to_email=to_email,
            subject=f"You're invited to join {project_name} on OptimalBuild",
            html_content=html,
            text_content=text,
        )

    def send_workflow_approval_request(
        self,
        to_email: str,
        workflow_title: str,
        step_name: str,
        requester_name: str,
        project_name: str,
        workflow_url: str,
    ) -> bool:
        """Send a workflow approval request email."""
        content = f"""
<h2>Approval Required</h2>
<p>Your approval is needed for a workflow step in project <strong>{project_name}</strong>.</p>

<div class="highlight">
    <p><strong>Workflow:</strong> {workflow_title}</p>
    <p><strong>Step:</strong> {step_name}</p>
    <p><strong>Requested by:</strong> {requester_name}</p>
</div>

<p style="text-align: center;">
    <a href="{workflow_url}" class="button">Review & Approve</a>
</p>

<p style="font-size: 12px; color: #666;">
    Please review this request at your earliest convenience.
</p>
"""
        html = self._get_base_template(content)
        text = f"""
Approval Required

Your approval is needed for a workflow step in project "{project_name}".

Workflow: {workflow_title}
Step: {step_name}
Requested by: {requester_name}

Review and approve at:
{workflow_url}
"""
        return self.send_email(
            to_email=to_email,
            subject=f"Approval Required: {workflow_title}",
            html_content=html,
            text_content=text,
        )

    def send_workflow_decision(
        self,
        to_email: str,
        workflow_title: str,
        decision: str,  # 'approved' or 'rejected'
        decider_name: str,
        project_name: str,
        comments: str | None,
        workflow_url: str,
    ) -> bool:
        """Send a workflow decision notification email."""
        decision_color = "#4caf50" if decision == "approved" else "#f44336"
        decision_text = "Approved" if decision == "approved" else "Rejected"

        comments_html = ""
        comments_text = ""
        if comments:
            comments_html = f"<p><strong>Comments:</strong> {comments}</p>"
            comments_text = f"\nComments: {comments}"

        content = f"""
<h2>Workflow {decision_text}</h2>
<p>A workflow in project <strong>{project_name}</strong> has been {decision}.</p>

<div class="highlight" style="border-left: 4px solid {decision_color};">
    <p><strong>Workflow:</strong> {workflow_title}</p>
    <p><strong>Decision:</strong> <span style="color: {decision_color};">{decision_text}</span></p>
    <p><strong>By:</strong> {decider_name}</p>
    {comments_html}
</div>

<p style="text-align: center;">
    <a href="{workflow_url}" class="button">View Workflow</a>
</p>
"""
        html = self._get_base_template(content)
        text = f"""
Workflow {decision_text}

A workflow in project "{project_name}" has been {decision}.

Workflow: {workflow_title}
Decision: {decision_text}
By: {decider_name}{comments_text}

View workflow at:
{workflow_url}
"""
        return self.send_email(
            to_email=to_email,
            subject=f"Workflow {decision_text}: {workflow_title}",
            html_content=html,
            text_content=text,
        )

    def send_submission_status_update(
        self,
        to_email: str,
        submission_title: str,
        agency_name: str,
        new_status: str,
        project_name: str,
        submission_url: str,
    ) -> bool:
        """Send a regulatory submission status update email."""
        status_colors: dict[str, str] = {
            "approved": "#4caf50",
            "rejected": "#f44336",
            "in_review": "#ff9800",
            "rfi": "#2196f3",
            "submitted": "#9c27b0",
        }
        status_color = status_colors.get(new_status.lower(), "#666")

        content = f"""
<h2>Submission Status Update</h2>
<p>Your regulatory submission for project <strong>{project_name}</strong> has a status update.</p>

<div class="highlight" style="border-left: 4px solid {status_color};">
    <p><strong>Submission:</strong> {submission_title}</p>
    <p><strong>Agency:</strong> {agency_name}</p>
    <p><strong>New Status:</strong> <span style="color: {status_color};">{new_status}</span></p>
</div>

<p style="text-align: center;">
    <a href="{submission_url}" class="button">View Submission</a>
</p>
"""
        html = self._get_base_template(content)
        text = f"""
Submission Status Update

Your regulatory submission for project "{project_name}" has a status update.

Submission: {submission_title}
Agency: {agency_name}
New Status: {new_status}

View submission at:
{submission_url}
"""
        return self.send_email(
            to_email=to_email,
            subject=f"Submission Update: {submission_title} - {new_status}",
            html_content=html,
            text_content=text,
        )
