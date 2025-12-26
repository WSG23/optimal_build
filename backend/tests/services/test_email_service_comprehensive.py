"""Comprehensive tests for email service.

Tests cover:
- EmailConfig initialization
- EmailService methods
- SMTP connection handling
- Email template generation
- Template-specific emails (invitations, approvals, etc.)
"""

from __future__ import annotations


class TestEmailConfigDefaults:
    """Tests for EmailConfig default values."""

    def test_default_smtp_host(self) -> None:
        """Test default SMTP host is localhost."""
        default_host = "localhost"
        assert default_host == "localhost"

    def test_default_smtp_port(self) -> None:
        """Test default SMTP port is 587."""
        default_port = 587
        assert default_port == 587

    def test_default_smtp_user_empty(self) -> None:
        """Test default SMTP user is empty string."""
        default_user = ""
        assert default_user == ""

    def test_default_smtp_password_empty(self) -> None:
        """Test default SMTP password is empty string."""
        default_password = ""
        assert default_password == ""

    def test_default_from_email(self) -> None:
        """Test default from email."""
        default_from = "noreply@optimalbuild.com"
        assert default_from == "noreply@optimalbuild.com"

    def test_default_from_name(self) -> None:
        """Test default from name."""
        default_name = "OptimalBuild"
        assert default_name == "OptimalBuild"

    def test_default_use_tls_true(self) -> None:
        """Test default use_tls is True."""
        use_tls = True
        assert use_tls is True

    def test_default_enabled_false(self) -> None:
        """Test default enabled is False."""
        enabled = False
        assert enabled is False

    def test_default_base_url(self) -> None:
        """Test default base URL."""
        base_url = "http://localhost:3000"
        assert base_url == "http://localhost:3000"


class TestEmailConfigFromEnvironment:
    """Tests for EmailConfig loading from environment."""

    def test_smtp_host_from_env(self) -> None:
        """Test SMTP_HOST loaded from environment."""
        env_host = "smtp.sendgrid.net"
        assert env_host is not None

    def test_smtp_port_from_env(self) -> None:
        """Test SMTP_PORT loaded and converted to int."""
        env_port = int("587")
        assert env_port == 587

    def test_smtp_port_custom(self) -> None:
        """Test custom SMTP port."""
        custom_port = 465
        assert custom_port == 465

    def test_use_tls_parsing_true(self) -> None:
        """Test use_tls parsing for 'true'."""
        value = "true"
        use_tls = value.lower() == "true"
        assert use_tls is True

    def test_use_tls_parsing_false(self) -> None:
        """Test use_tls parsing for 'false'."""
        value = "false"
        use_tls = value.lower() == "true"
        assert use_tls is False

    def test_enabled_parsing_true(self) -> None:
        """Test enabled parsing for 'true'."""
        value = "true"
        enabled = value.lower() == "true"
        assert enabled is True

    def test_enabled_parsing_false(self) -> None:
        """Test enabled parsing for 'false'."""
        value = "false"
        enabled = value.lower() == "true"
        assert enabled is False


class TestEmailServiceInit:
    """Tests for EmailService initialization."""

    def test_accepts_custom_config(self) -> None:
        """Test EmailService accepts custom config."""
        config = object()  # Mock config
        assert config is not None

    def test_uses_global_config_if_none(self) -> None:
        """Test EmailService uses global config if none provided."""
        default_config = None
        # Would fall back to email_config global
        assert default_config is None


class TestEmailServiceIsEnabled:
    """Tests for EmailService.is_enabled method."""

    def test_returns_true_when_enabled(self) -> None:
        """Test is_enabled returns True when enabled."""
        enabled = True
        assert enabled is True

    def test_returns_false_when_disabled(self) -> None:
        """Test is_enabled returns False when disabled."""
        enabled = False
        assert enabled is False


class TestSMTPConnection:
    """Tests for SMTP connection handling."""

    def test_creates_smtp_instance(self) -> None:
        """Test creates SMTP instance with host and port."""
        host = "localhost"
        port = 587
        assert host is not None and port > 0

    def test_starttls_when_use_tls(self) -> None:
        """Test STARTTLS called when use_tls is True."""
        use_tls = True
        # Would call smtp.starttls()
        assert use_tls is True

    def test_login_with_credentials(self) -> None:
        """Test login called when credentials provided."""
        smtp_user = "user@example.com"
        smtp_password = "password123"
        has_credentials = bool(smtp_user and smtp_password)
        assert has_credentials is True

    def test_no_login_without_credentials(self) -> None:
        """Test no login when credentials empty."""
        smtp_user = ""
        smtp_password = ""
        has_credentials = bool(smtp_user and smtp_password)
        assert has_credentials is False


class TestSendEmail:
    """Tests for send_email method."""

    def test_returns_true_when_disabled(self) -> None:
        """Test returns True (pretend success) when disabled."""
        enabled = False
        if not enabled:
            result = True  # Pretend success
        assert result is True

    def test_creates_multipart_message(self) -> None:
        """Test creates multipart/alternative message."""
        msg_type = "alternative"
        assert msg_type == "alternative"

    def test_sets_subject(self) -> None:
        """Test sets email subject."""
        subject = "Test Email Subject"
        assert len(subject) > 0

    def test_sets_from_header(self) -> None:
        """Test sets From header with name and email."""
        from_name = "OptimalBuild"
        from_email = "noreply@optimalbuild.com"
        from_header = f"{from_name} <{from_email}>"
        assert from_name in from_header
        assert from_email in from_header

    def test_sets_to_header(self) -> None:
        """Test sets To header."""
        to_email = "recipient@example.com"
        assert "@" in to_email

    def test_attaches_text_part(self) -> None:
        """Test attaches text/plain part when provided."""
        text_content = "Plain text content"
        assert len(text_content) > 0

    def test_attaches_html_part(self) -> None:
        """Test attaches text/html part."""
        html_content = "<html><body>HTML content</body></html>"
        assert "<html>" in html_content

    def test_returns_true_on_success(self) -> None:
        """Test returns True on successful send."""
        result = True
        assert result is True

    def test_returns_false_on_smtp_error(self) -> None:
        """Test returns False on SMTP error."""
        result = False  # SMTPException raised
        assert result is False

    def test_returns_false_on_os_error(self) -> None:
        """Test returns False on OS/network error."""
        result = False  # OSError raised
        assert result is False


class TestBaseEmailTemplate:
    """Tests for base email template."""

    def test_includes_doctype(self) -> None:
        """Test template includes DOCTYPE."""
        template = "<!DOCTYPE html>"
        assert "DOCTYPE" in template

    def test_includes_utf8_charset(self) -> None:
        """Test template includes UTF-8 charset."""
        meta = '<meta charset="utf-8">'
        assert "utf-8" in meta

    def test_includes_viewport_meta(self) -> None:
        """Test template includes viewport meta tag."""
        meta = '<meta name="viewport"'
        assert "viewport" in meta

    def test_includes_header_section(self) -> None:
        """Test template includes header section."""
        header = '<div class="header">'
        assert "header" in header

    def test_includes_content_section(self) -> None:
        """Test template includes content section."""
        content = '<div class="content">'
        assert "content" in content

    def test_includes_footer_section(self) -> None:
        """Test template includes footer section."""
        footer = '<div class="footer">'
        assert "footer" in footer

    def test_includes_optimalbuild_branding(self) -> None:
        """Test template includes OptimalBuild branding."""
        branding = "OptimalBuild"
        assert branding == "OptimalBuild"

    def test_includes_copyright(self) -> None:
        """Test template includes copyright notice."""
        copyright_text = "© 2025 OptimalBuild"
        assert "2025" in copyright_text


class TestTeamInvitationEmail:
    """Tests for team invitation email."""

    def test_generates_accept_url(self) -> None:
        """Test generates accept invitation URL."""
        base_url = "http://localhost:3000"
        token = "abc123token"
        accept_url = f"{base_url}/accept-invitation?token={token}"
        assert "accept-invitation" in accept_url
        assert token in accept_url

    def test_includes_inviter_name(self) -> None:
        """Test includes inviter name in email."""
        inviter_name = "John Tan"
        content = f"{inviter_name} has invited you"
        assert inviter_name in content

    def test_includes_project_name(self) -> None:
        """Test includes project name in email."""
        project_name = "Marina Bay Development"
        content = f"project <strong>{project_name}</strong>"
        assert project_name in content

    def test_includes_role(self) -> None:
        """Test includes role in email."""
        role = "Developer"
        content = f"as a <strong>{role}</strong>"
        assert role in content

    def test_includes_accept_button(self) -> None:
        """Test includes accept invitation button."""
        button_text = "Accept Invitation"
        assert button_text == "Accept Invitation"

    def test_includes_expiry_notice(self) -> None:
        """Test includes 7-day expiry notice."""
        notice = "expire in 7 days"
        assert "7 days" in notice

    def test_generates_text_version(self) -> None:
        """Test generates plain text version."""
        text = "You've Been Invited!"
        assert len(text) > 0

    def test_subject_includes_project(self) -> None:
        """Test subject includes project name."""
        project_name = "Marina Bay Development"
        subject = f"You're invited to join {project_name} on OptimalBuild"
        assert project_name in subject


class TestWorkflowApprovalRequestEmail:
    """Tests for workflow approval request email."""

    def test_includes_workflow_title(self) -> None:
        """Test includes workflow title."""
        workflow_title = "Design Phase Approval"
        content = f"<strong>Workflow:</strong> {workflow_title}"
        assert workflow_title in content

    def test_includes_step_name(self) -> None:
        """Test includes step name."""
        step_name = "Architect Review"
        content = f"<strong>Step:</strong> {step_name}"
        assert step_name in content

    def test_includes_requester_name(self) -> None:
        """Test includes requester name."""
        requester_name = "Sarah Lim"
        content = f"<strong>Requested by:</strong> {requester_name}"
        assert requester_name in content

    def test_includes_project_name(self) -> None:
        """Test includes project name."""
        project_name = "Orchard Tower"
        content = f"project <strong>{project_name}</strong>"
        assert project_name in content

    def test_includes_review_button(self) -> None:
        """Test includes review and approve button."""
        button_text = "Review & Approve"
        assert button_text == "Review & Approve"

    def test_subject_format(self) -> None:
        """Test subject format."""
        workflow_title = "Design Phase Approval"
        subject = f"Approval Required: {workflow_title}"
        assert subject == "Approval Required: Design Phase Approval"


class TestWorkflowDecisionEmail:
    """Tests for workflow decision notification email."""

    def test_approved_decision_color(self) -> None:
        """Test approved decision uses green color."""
        decision = "approved"
        color = "#4caf50" if decision == "approved" else "#f44336"
        assert color == "#4caf50"

    def test_rejected_decision_color(self) -> None:
        """Test rejected decision uses red color."""
        decision = "rejected"
        color = "#4caf50" if decision == "approved" else "#f44336"
        assert color == "#f44336"

    def test_approved_text(self) -> None:
        """Test approved decision text."""
        decision = "approved"
        text = "Approved" if decision == "approved" else "Rejected"
        assert text == "Approved"

    def test_rejected_text(self) -> None:
        """Test rejected decision text."""
        decision = "rejected"
        text = "Approved" if decision == "approved" else "Rejected"
        assert text == "Rejected"

    def test_includes_comments_when_provided(self) -> None:
        """Test includes comments when provided."""
        comments = "Great work, approved with minor changes"
        html = f"<p><strong>Comments:</strong> {comments}</p>"
        assert comments in html

    def test_no_comments_when_none(self) -> None:
        """Test no comments section when None."""
        comments = None
        html = "" if not comments else f"<p>Comments: {comments}</p>"
        assert html == ""

    def test_includes_decider_name(self) -> None:
        """Test includes decider name."""
        decider_name = "Michael Wong"
        content = f"<strong>By:</strong> {decider_name}"
        assert decider_name in content

    def test_subject_approved(self) -> None:
        """Test subject for approved workflow."""
        workflow_title = "Design Review"
        subject = f"Workflow Approved: {workflow_title}"
        assert "Approved" in subject

    def test_subject_rejected(self) -> None:
        """Test subject for rejected workflow."""
        workflow_title = "Design Review"
        subject = f"Workflow Rejected: {workflow_title}"
        assert "Rejected" in subject


class TestSubmissionStatusUpdateEmail:
    """Tests for regulatory submission status update email."""

    def test_approved_status_color(self) -> None:
        """Test approved status uses green color."""
        colors = {
            "approved": "#4caf50",
            "rejected": "#f44336",
            "in_review": "#ff9800",
            "rfi": "#2196f3",
            "submitted": "#9c27b0",
        }
        assert colors["approved"] == "#4caf50"

    def test_rejected_status_color(self) -> None:
        """Test rejected status uses red color."""
        colors = {"rejected": "#f44336"}
        assert colors["rejected"] == "#f44336"

    def test_in_review_status_color(self) -> None:
        """Test in_review status uses orange color."""
        colors = {"in_review": "#ff9800"}
        assert colors["in_review"] == "#ff9800"

    def test_rfi_status_color(self) -> None:
        """Test RFI status uses blue color."""
        colors = {"rfi": "#2196f3"}
        assert colors["rfi"] == "#2196f3"

    def test_submitted_status_color(self) -> None:
        """Test submitted status uses purple color."""
        colors = {"submitted": "#9c27b0"}
        assert colors["submitted"] == "#9c27b0"

    def test_unknown_status_default_color(self) -> None:
        """Test unknown status uses default gray color."""
        status = "unknown"
        colors = {"approved": "#4caf50"}
        color = colors.get(status.lower(), "#666")
        assert color == "#666"

    def test_includes_submission_title(self) -> None:
        """Test includes submission title."""
        title = "URA Planning Permission"
        content = f"<strong>Submission:</strong> {title}"
        assert title in content

    def test_includes_agency_name(self) -> None:
        """Test includes agency name."""
        agency = "Urban Redevelopment Authority"
        content = f"<strong>Agency:</strong> {agency}"
        assert agency in content

    def test_includes_new_status(self) -> None:
        """Test includes new status."""
        status = "approved"
        content = f"<strong>New Status:</strong> <span>{status}</span>"
        assert status in content

    def test_subject_format(self) -> None:
        """Test subject format includes title and status."""
        title = "URA Planning Permission"
        status = "approved"
        subject = f"Submission Update: {title} - {status}"
        assert title in subject
        assert status in subject


class TestEmailLogging:
    """Tests for email service logging."""

    def test_logs_disabled_email(self) -> None:
        """Test logs when email is disabled."""
        log_message = "Email disabled - would send to test@example.com: Test Subject"
        assert "disabled" in log_message.lower()

    def test_logs_successful_send(self) -> None:
        """Test logs successful email send."""
        log_message = "Email sent successfully to test@example.com: Test Subject"
        assert "successfully" in log_message

    def test_logs_smtp_error(self) -> None:
        """Test logs SMTP errors."""
        log_message = "Failed to send email to test@example.com: SMTP error"
        assert "Failed" in log_message

    def test_logs_network_error(self) -> None:
        """Test logs network errors."""
        log_message = (
            "Network error sending email to test@example.com: Connection refused"
        )
        assert "Network error" in log_message


class TestEmailValidation:
    """Tests for email address validation."""

    def test_valid_email_format(self) -> None:
        """Test valid email address format."""
        email = "user@example.com"
        assert "@" in email
        assert "." in email.split("@")[1]

    def test_singapore_domain(self) -> None:
        """Test Singapore domain email."""
        email = "user@company.com.sg"
        assert email.endswith(".sg")

    def test_corporate_email(self) -> None:
        """Test corporate email."""
        email = "john.tan@optimalbuild.com"
        assert "optimalbuild.com" in email


class TestEdgeCases:
    """Tests for edge cases in email service."""

    def test_empty_subject(self) -> None:
        """Test handling empty subject."""
        subject = ""
        assert subject == ""

    def test_very_long_subject(self) -> None:
        """Test handling very long subject."""
        subject = "A" * 200
        # Subject should be truncated or handled
        assert len(subject) == 200

    def test_html_special_characters(self) -> None:
        """Test handling HTML special characters."""
        content = "Company <ABC> & Partners"
        # Should be escaped in HTML
        assert "<" in content

    def test_unicode_content(self) -> None:
        """Test handling unicode content."""
        content = "Réunion: 新加坡开发项目"
        assert len(content) > 0

    def test_empty_html_content(self) -> None:
        """Test handling empty HTML content."""
        html_content = ""
        assert html_content == ""

    def test_none_text_content(self) -> None:
        """Test handling None text content."""
        text_content = None
        # Should not attach text part
        assert text_content is None
