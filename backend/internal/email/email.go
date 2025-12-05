package email

import (
	"bytes"
	"fmt"
	"html/template"
	"net/smtp"
	"os"
	"strings"
)

// Config holds email service configuration
type Config struct {
	SMTPHost     string
	SMTPPort     string
	SMTPUser     string
	SMTPPassword string
	FromEmail    string
	FromName     string
	FrontendURL  string
}

// Service handles email sending
type Service struct {
	config Config
}

// NewService creates a new email service
func NewService() *Service {
	return &Service{
		config: Config{
			SMTPHost:     getEnv("SMTP_HOST", "smtp.gmail.com"),
			SMTPPort:     getEnv("SMTP_PORT", "587"),
			SMTPUser:     getEnv("SMTP_USER", ""),
			SMTPPassword: getEnv("SMTP_PASSWORD", ""),
			FromEmail:    getEnv("SMTP_FROM_EMAIL", "noreply@datamigrate.ai"),
			FromName:     getEnv("SMTP_FROM_NAME", "DataMigrate AI"),
			FrontendURL:  getEnv("FRONTEND_URL", "http://localhost:5173"),
		},
	}
}

func getEnv(key, defaultValue string) string {
	if value := os.Getenv(key); value != "" {
		return value
	}
	return defaultValue
}

// IsConfigured returns true if email service is properly configured
func (s *Service) IsConfigured() bool {
	return s.config.SMTPUser != "" && s.config.SMTPPassword != ""
}

// SendEmail sends an email using SMTP
func (s *Service) SendEmail(to, subject, htmlBody, textBody string) error {
	if !s.IsConfigured() {
		return fmt.Errorf("email service is not configured - please set SMTP_USER and SMTP_PASSWORD environment variables")
	}

	// Setup authentication
	auth := smtp.PlainAuth("", s.config.SMTPUser, s.config.SMTPPassword, s.config.SMTPHost)

	// Build email headers
	headers := make(map[string]string)
	headers["From"] = fmt.Sprintf("%s <%s>", s.config.FromName, s.config.FromEmail)
	headers["To"] = to
	headers["Subject"] = subject
	headers["MIME-Version"] = "1.0"
	headers["Content-Type"] = "multipart/alternative; boundary=\"boundary\""

	// Build message
	var msg bytes.Buffer
	for k, v := range headers {
		msg.WriteString(fmt.Sprintf("%s: %s\r\n", k, v))
	}
	msg.WriteString("\r\n")

	// Plain text part
	msg.WriteString("--boundary\r\n")
	msg.WriteString("Content-Type: text/plain; charset=\"utf-8\"\r\n\r\n")
	msg.WriteString(textBody)
	msg.WriteString("\r\n")

	// HTML part
	msg.WriteString("--boundary\r\n")
	msg.WriteString("Content-Type: text/html; charset=\"utf-8\"\r\n\r\n")
	msg.WriteString(htmlBody)
	msg.WriteString("\r\n")
	msg.WriteString("--boundary--")

	// Send email
	addr := fmt.Sprintf("%s:%s", s.config.SMTPHost, s.config.SMTPPort)
	err := smtp.SendMail(addr, auth, s.config.FromEmail, []string{to}, msg.Bytes())
	if err != nil {
		return fmt.Errorf("failed to send email: %w", err)
	}

	return nil
}

// SendPasswordResetEmail sends a password reset email
func (s *Service) SendPasswordResetEmail(to, firstName, resetToken string) error {
	resetURL := fmt.Sprintf("%s/reset-password?token=%s", s.config.FrontendURL, resetToken)

	htmlBody := s.getPasswordResetHTML(firstName, resetURL)
	textBody := s.getPasswordResetText(firstName, resetURL)

	return s.SendEmail(to, "Reset Your DataMigrate AI Password", htmlBody, textBody)
}

// SendWelcomeEmail sends a welcome email to new users
func (s *Service) SendWelcomeEmail(to, firstName, organizationName string) error {
	loginURL := fmt.Sprintf("%s/login", s.config.FrontendURL)

	htmlBody := s.getWelcomeHTML(firstName, organizationName, loginURL)
	textBody := s.getWelcomeText(firstName, organizationName, loginURL)

	return s.SendEmail(to, "Welcome to DataMigrate AI!", htmlBody, textBody)
}

// SendInvitationEmail sends an organization invitation email
func (s *Service) SendInvitationEmail(to, inviterName, organizationName, inviteToken string) error {
	inviteURL := fmt.Sprintf("%s/accept-invite?token=%s", s.config.FrontendURL, inviteToken)

	htmlBody := s.getInvitationHTML(inviterName, organizationName, inviteURL)
	textBody := s.getInvitationText(inviterName, organizationName, inviteURL)

	return s.SendEmail(to, fmt.Sprintf("You've been invited to join %s on DataMigrate AI", organizationName), htmlBody, textBody)
}

// Email templates

func (s *Service) getPasswordResetHTML(firstName, resetURL string) string {
	tmpl := `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Reset Your Password</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">DataMigrate AI</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">Reset Your Password</h2>
        <p>Hi {{.FirstName}},</p>
        <p>We received a request to reset your password for your DataMigrate AI account. Click the button below to create a new password:</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{.ResetURL}}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Reset Password</a>
        </div>
        <p style="color: #666; font-size: 14px;">This link will expire in 1 hour for security reasons.</p>
        <p style="color: #666; font-size: 14px;">If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.</p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            DataMigrate AI - MSSQL to dbt Migration Platform<br>
            This is an automated message, please do not reply.
        </p>
    </div>
</body>
</html>
`
	data := map[string]string{
		"FirstName": firstName,
		"ResetURL":  resetURL,
	}
	return executeTemplate(tmpl, data)
}

func (s *Service) getPasswordResetText(firstName, resetURL string) string {
	return fmt.Sprintf(`Hi %s,

We received a request to reset your password for your DataMigrate AI account.

Click this link to reset your password:
%s

This link will expire in 1 hour for security reasons.

If you didn't request a password reset, you can safely ignore this email. Your password will not be changed.

--
DataMigrate AI - MSSQL to dbt Migration Platform
`, firstName, resetURL)
}

func (s *Service) getWelcomeHTML(firstName, organizationName, loginURL string) string {
	dashboardURL := strings.Replace(loginURL, "/login", "/dashboard", 1)
	tmpl := `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Welcome to DataMigrate AI</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; background-color: #f5f5f5;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 40px 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 32px;">Welcome to DataMigrate AI!</h1>
        <p style="color: rgba(255,255,255,0.9); margin: 10px 0 0 0; font-size: 16px;">Your AI-Powered Migration Journey Starts Now</p>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none;">
        <h2 style="color: #333; margin-top: 0;">Hi {{.FirstName}}! 🎉</h2>
        <p>Thank you for joining DataMigrate AI! Your account for <strong>{{.OrganizationName}}</strong> is ready.</p>

        <div style="background: linear-gradient(135deg, #f5f7fa 0%, #e4e8eb 100%); padding: 20px; border-radius: 8px; margin: 20px 0;">
            <h3 style="color: #667eea; margin-top: 0;">🚀 Why Teams Choose Us</h3>
            <ul style="margin: 0; padding-left: 20px;">
                <li><strong>90% Faster Migrations</strong> - What takes weeks now takes hours</li>
                <li><strong>AI-Powered Accuracy</strong> - 8 specialized agents handle complex transformations</li>
                <li><strong>Enterprise Security</strong> - Your data never leaves your infrastructure</li>
                <li><strong>Multi-Warehouse Support</strong> - Deploy to Snowflake, Databricks, Fabric & more</li>
            </ul>
        </div>

        <h3 style="color: #667eea;">📋 Get Started in 3 Steps:</h3>
        <div style="margin: 15px 0;">
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="background: #667eea; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px;">1</span>
                <span><strong>Connect</strong> - Add your MSSQL database connection</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="background: #667eea; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px;">2</span>
                <span><strong>Select</strong> - Choose tables and views to migrate</span>
            </div>
            <div style="display: flex; align-items: center; margin-bottom: 12px;">
                <span style="background: #667eea; color: white; width: 28px; height: 28px; border-radius: 50%; display: inline-flex; align-items: center; justify-content: center; font-weight: bold; margin-right: 12px;">3</span>
                <span><strong>Deploy</strong> - One-click deployment to your data warehouse</span>
            </div>
        </div>

        <div style="text-align: center; margin: 30px 0;">
            <a href="{{.DashboardURL}}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 16px 40px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; font-size: 16px; box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);">Start Your First Migration</a>
        </div>

        <div style="background: #fff3cd; border: 1px solid #ffc107; padding: 15px; border-radius: 8px; margin: 20px 0;">
            <p style="margin: 0; color: #856404;"><strong>💡 Pro Tip:</strong> Start with a small table to see the magic! Our AI will analyze your schema, detect relationships, and generate production-ready dbt models.</p>
        </div>
    </div>
    <div style="background: #f8f9fa; padding: 20px 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <p style="color: #666; font-size: 13px; margin: 0 0 10px 0; text-align: center;">
            Need help? Our AI support assistant is available 24/7 in the app.
        </p>
        <p style="color: #999; font-size: 12px; text-align: center; margin: 0;">
            DataMigrate AI - MSSQL to dbt Migration Platform<br>
            © 2025 OKO Investments. All rights reserved.
        </p>
    </div>
</body>
</html>
`
	data := map[string]string{
		"FirstName":        firstName,
		"OrganizationName": organizationName,
		"LoginURL":         loginURL,
		"DashboardURL":     dashboardURL,
	}
	return executeTemplate(tmpl, data)
}

func (s *Service) getWelcomeText(firstName, organizationName, loginURL string) string {
	dashboardURL := strings.Replace(loginURL, "/login", "/dashboard", 1)
	return fmt.Sprintf(`Hi %s!

Welcome to DataMigrate AI! 🎉

Thank you for joining us! Your account for %s is ready.

WHY TEAMS CHOOSE US:
• 90%% Faster Migrations - What takes weeks now takes hours
• AI-Powered Accuracy - 8 specialized agents handle complex transformations
• Enterprise Security - Your data never leaves your infrastructure
• Multi-Warehouse Support - Deploy to Snowflake, Databricks, Fabric & more

GET STARTED IN 3 STEPS:
1. Connect - Add your MSSQL database connection
2. Select - Choose tables and views to migrate
3. Deploy - One-click deployment to your data warehouse

Start your first migration: %s

Pro Tip: Start with a small table to see the magic! Our AI will analyze your schema, detect relationships, and generate production-ready dbt models.

Need help? Our AI support assistant is available 24/7 in the app.

--
DataMigrate AI - MSSQL to dbt Migration Platform
© 2025 OKO Investments. All rights reserved.
`, firstName, organizationName, dashboardURL)
}

func (s *Service) getInvitationHTML(inviterName, organizationName, inviteURL string) string {
	tmpl := `
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>You're Invited!</title>
</head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px;">
    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center; border-radius: 10px 10px 0 0;">
        <h1 style="color: white; margin: 0; font-size: 28px;">DataMigrate AI</h1>
    </div>
    <div style="background: #ffffff; padding: 30px; border: 1px solid #e0e0e0; border-top: none; border-radius: 0 0 10px 10px;">
        <h2 style="color: #333; margin-top: 0;">You've Been Invited!</h2>
        <p><strong>{{.InviterName}}</strong> has invited you to join <strong>{{.OrganizationName}}</strong> on DataMigrate AI.</p>
        <p>DataMigrate AI helps teams migrate MSSQL databases to modern dbt projects with AI-powered transformation.</p>
        <div style="text-align: center; margin: 30px 0;">
            <a href="{{.InviteURL}}" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 14px 30px; text-decoration: none; border-radius: 5px; font-weight: bold; display: inline-block;">Accept Invitation</a>
        </div>
        <p style="color: #666; font-size: 14px;">This invitation will expire in 7 days.</p>
        <hr style="border: none; border-top: 1px solid #e0e0e0; margin: 30px 0;">
        <p style="color: #999; font-size: 12px; text-align: center;">
            DataMigrate AI - MSSQL to dbt Migration Platform<br>
            This is an automated message, please do not reply.
        </p>
    </div>
</body>
</html>
`
	data := map[string]string{
		"InviterName":      inviterName,
		"OrganizationName": organizationName,
		"InviteURL":        inviteURL,
	}
	return executeTemplate(tmpl, data)
}

func (s *Service) getInvitationText(inviterName, organizationName, inviteURL string) string {
	return fmt.Sprintf(`You've Been Invited!

%s has invited you to join %s on DataMigrate AI.

DataMigrate AI helps teams migrate MSSQL databases to modern dbt projects with AI-powered transformation.

Accept your invitation: %s

This invitation will expire in 7 days.

--
DataMigrate AI - MSSQL to dbt Migration Platform
`, inviterName, organizationName, inviteURL)
}

func executeTemplate(tmplStr string, data map[string]string) string {
	tmpl, err := template.New("email").Parse(tmplStr)
	if err != nil {
		return tmplStr
	}
	var buf bytes.Buffer
	if err := tmpl.Execute(&buf, data); err != nil {
		return tmplStr
	}
	return buf.String()
}

// Mock email service for development (logs to console)
type MockService struct {
	config Config
}

func NewMockService() *MockService {
	return &MockService{
		config: Config{
			FrontendURL: getEnv("FRONTEND_URL", "http://localhost:5173"),
		},
	}
}

func (s *MockService) IsConfigured() bool {
	return true // Mock is always "configured"
}

func (s *MockService) SendEmail(to, subject, htmlBody, textBody string) error {
	fmt.Printf("\n=== MOCK EMAIL ===\n")
	fmt.Printf("To: %s\n", to)
	fmt.Printf("Subject: %s\n", subject)
	fmt.Printf("Body:\n%s\n", strings.Repeat("-", 40))
	fmt.Printf("%s\n", textBody)
	fmt.Printf("%s\n", strings.Repeat("=", 40))
	return nil
}

func (s *MockService) SendPasswordResetEmail(to, firstName, resetToken string) error {
	resetURL := fmt.Sprintf("%s/reset-password?token=%s", s.config.FrontendURL, resetToken)
	fmt.Printf("\n=== MOCK PASSWORD RESET EMAIL ===\n")
	fmt.Printf("To: %s\n", to)
	fmt.Printf("Reset URL: %s\n", resetURL)
	fmt.Printf("%s\n", strings.Repeat("=", 40))
	return nil
}

func (s *MockService) SendWelcomeEmail(to, firstName, organizationName string) error {
	fmt.Printf("\n=== MOCK WELCOME EMAIL ===\n")
	fmt.Printf("To: %s\n", to)
	fmt.Printf("Name: %s\n", firstName)
	fmt.Printf("Organization: %s\n", organizationName)
	fmt.Printf("%s\n", strings.Repeat("=", 40))
	return nil
}

func (s *MockService) SendInvitationEmail(to, inviterName, organizationName, inviteToken string) error {
	inviteURL := fmt.Sprintf("%s/accept-invite?token=%s", s.config.FrontendURL, inviteToken)
	fmt.Printf("\n=== MOCK INVITATION EMAIL ===\n")
	fmt.Printf("To: %s\n", to)
	fmt.Printf("From: %s\n", inviterName)
	fmt.Printf("Organization: %s\n", organizationName)
	fmt.Printf("Invite URL: %s\n", inviteURL)
	fmt.Printf("%s\n", strings.Repeat("=", 40))
	return nil
}
