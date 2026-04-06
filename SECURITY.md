# Security Policy

## Supported Versions

We release patches for security vulnerabilities in the following versions:

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of Aletheia seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to: **security@aletheia.io**

You should receive a response within 48 hours. If for some reason you do not, please follow up via email to ensure we received your original message.

Please include the following information (as much as you can provide):

- Type of issue (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- Full paths of source file(s) related to the issue
- Location of the affected source code (tag/branch/commit or direct URL)
- Any special configuration required to reproduce the issue
- Step-by-step instructions to reproduce the issue
- Proof-of-concept or exploit code (if possible)
- Impact of the issue, including how an attacker might exploit it

### What to Expect

After you submit a report:

1. **Acknowledgment**: We will acknowledge receipt of your report within 48 hours.

2. **Investigation**: We will investigate the issue and determine its severity and impact.

3. **Updates**: We will keep you informed of our progress throughout the process.

4. **Resolution**: Once we have resolved the issue, we will notify you and discuss public disclosure.

5. **Credit**: If you wish, we will credit you in our security advisories.

### Disclosure Policy

- We follow a 90-day disclosure deadline.
- We will coordinate disclosure with you.
- We will notify users before public disclosure.

## Security Best Practices

When deploying Aletheia, please follow these security best practices:

### Configuration

1. **Secret Key**: Always use a strong, unique `SECRET_KEY` in production:
   ```bash
   python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
   ```

2. **Debug Mode**: Never run with `DEBUG=True` in production.

3. **Allowed Hosts**: Always specify `ALLOWED_HOSTS` explicitly:
   ```python
   ALLOWED_HOSTS = ['api.yourdomain.com']
   ```

4. **HTTPS**: Always use HTTPS in production:
   ```python
   SECURE_SSL_REDIRECT = True
   SECURE_HSTS_SECONDS = 31536000
   ```

### Database

1. **Strong Passwords**: Use strong, unique passwords for database users.

2. **Connection Encryption**: Enable SSL for database connections.

3. **Principle of Least Privilege**: Database users should only have necessary permissions.

### API Security

1. **Rate Limiting**: Enable rate limiting to prevent abuse:
   ```python
   REST_FRAMEWORK = {
       'DEFAULT_THROTTLE_RATES': {
           'anon': '10/minute',
           'user': '60/minute'
       }
   }
   ```

2. **CORS**: Configure CORS restrictively:
   ```python
   CORS_ALLOWED_ORIGINS = ['https://yourdomain.com']
   ```

3. **API Keys**: Rotate API keys regularly.

### File Uploads

1. **Size Limits**: Enforce file size limits.

2. **Type Validation**: Validate file types server-side.

3. **Storage**: Store uploaded files outside the web root.

### Monitoring

1. **Logging**: Enable comprehensive logging.

2. **Alerts**: Set up alerts for suspicious activity.

3. **Audit Trail**: Maintain an audit trail of sensitive operations.

## Security Features

Aletheia includes the following security features:

- **JWT Authentication**: Secure, stateless authentication
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Input Validation**: Comprehensive input sanitization
- **CSRF Protection**: Cross-site request forgery protection
- **XSS Prevention**: Content Security Policy headers
- **SQL Injection Prevention**: ORM-based queries
- **File Validation**: MIME type and extension checking
- **Secure Headers**: HSTS, X-Frame-Options, etc.

## Security Updates

Security updates will be released as patch versions (e.g., 1.0.1). We recommend:

1. Subscribing to security advisories
2. Updating promptly when patches are released
3. Testing updates in a staging environment first