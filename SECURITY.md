# Security Policy

## Supported Versions

We actively support the latest version of HeyJenna. Security updates will be provided for:

| Version | Supported          |
| ------- | ------------------ |
| Latest  | :white_check_mark: |
| < Latest| :x:                |

## Reporting a Vulnerability

If you discover a security vulnerability in HeyJenna, please report it responsibly:

### How to Report

1. **Do NOT** create a public GitHub issue for security vulnerabilities
2. **Email** the maintainer directly at the email associated with the GitHub account
3. **Include** the following information:
   - Description of the vulnerability
   - Steps to reproduce the issue
   - Potential impact assessment
   - Suggested fix (if you have one)

### What to Expect

- **Acknowledgment** within 48 hours of your report
- **Initial assessment** within 1 week
- **Regular updates** on the progress of fixing the vulnerability
- **Credit** in the security advisory (if you wish)

### Security Considerations

HeyJenna handles:
- **Cookie files** containing authentication data
- **Downloaded media files** from various platforms
- **User-provided URLs** and content
- **Local file system** operations

### Best Practices for Users

1. **Keep cookie files secure** - they contain sensitive authentication data
2. **Use environment variables** for sensitive configuration
3. **Run in isolated environments** when possible
4. **Keep dependencies updated** regularly
5. **Be cautious with URLs** from untrusted sources

### Scope

Security issues we're particularly interested in:
- Authentication bypass
- Arbitrary file access/traversal
- Code injection vulnerabilities
- Sensitive data exposure
- Dependency vulnerabilities

### Out of Scope

- Issues requiring physical access to the machine
- Social engineering attacks
- Issues in third-party dependencies (report to respective maintainers)
- Rate limiting or DoS issues

Thank you for helping keep HeyJenna secure! 🔒