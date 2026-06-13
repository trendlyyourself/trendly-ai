# Trendly AI Security Guidelines

## Overview
This document outlines the security measures implemented in Trendly AI and guidelines for maintaining security standards.

## Current Security Measures

### 1. Authentication & Authorization
- **Password Hashing**: Using bcrypt algorithm for password hashing
- **JWT Tokens**: Access tokens expire after 7 days (configurable)
- **OAuth2 Bearer**: Standard OAuth2 password flow with bearer tokens
- **Dependency Injection**: FastAPI dependency injection for authentication checks

### 2. Rate Limiting
- **Login Endpoint**: Max 5 requests per minute per IP/email
- **In-Memory Storage**: Rate limiting state stored in application memory
- **Configurable**: Can be adjusted in `app/core/security.py`

### 3. Input Validation
- **Password Requirements**: 
  - Minimum 8 characters
  - Must contain uppercase letter
  - Must contain lowercase letter
  - Must contain number
- **Email Validation**: Using Pydantic's EmailStr validator
- **Field Length Limits**: All text fields have max length constraints

### 4. CORS Configuration
- **Environment-Specific**: Different origins for dev vs production
- **Production Origins**: Only allows `https://trendly-ai-nine.vercel.app`
- **Development Origins**: Allows localhost variants on ports 3000 and 5173
- **Methods Restricted**: Only GET, POST, PUT, DELETE, OPTIONS allowed
- **Headers Restricted**: Only Content-Type and Authorization headers

### 5. Security Headers
All responses include security headers to prevent common attacks:
- `X-Content-Type-Options: nosniff` - Prevents MIME type sniffing
- `X-Frame-Options: DENY` - Prevents clickjacking
- `X-XSS-Protection: 1; mode=block` - Enables XSS protection
- `Strict-Transport-Security: max-age=31536000` - HTTPS enforcement (production)
- `Referrer-Policy: strict-origin-when-cross-origin` - Limits referrer leakage
- `Permissions-Policy` - Restricts access to device features

### 6. Database Security
- **Parameterized Queries**: All SQL queries use parameterized statements (? placeholders)
- **No String Concatenation**: Prevents SQL injection
- **SQLite Encryption**: Consider SQLCipher for sensitive deployments

## Security Best Practices

### For Developers

1. **Never commit .env files**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Set unique SECRET_KEY in production**
   ```bash
   # Generate
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

4. **Use environment-specific configurations**
   - Development: `APP_ENV=development`
   - Production: `APP_ENV=production`

### For Deployment

1. **Production Configuration**
   - Set `APP_ENV=production`
   - Use strong SECRET_KEY (32+ characters)
   - Set FRONTEND_URL to production domain
   - Enable HTTPS/SSL
   - Use PostgreSQL instead of SQLite

2. **Backend Server**
   - Do NOT expose on 0.0.0.0 in production
   - Use reverse proxy (nginx/Apache)
   - Run as non-root user
   - Enable firewall rules
   - Restrict access to necessary ports only

3. **Monitoring**
   - Log authentication failures
   - Monitor rate limit hits
   - Track database access
   - Use application monitoring tools

## Dependency Security

### Current Critical Dependencies
- `fastapi`: Web framework
- `python-jose`: JWT token handling
- `passlib`: Password hashing
- `bcrypt`: Password hashing algorithm
- `pydantic`: Input validation
- `sqlite3`: Database

### Updating Dependencies
```bash
# Check for vulnerabilities
pip install pip-audit
pip-audit

# Update packages
pip install --upgrade <package-name>
```

## Known Limitations

1. **In-Memory Rate Limiting**: Rate limit data is lost on server restart
   - Solution for production: Use Redis for distributed rate limiting

2. **SQLite Database**: Not suitable for multi-process deployments
   - Solution: Migrate to PostgreSQL for production

3. **Single Secret Key**: No key rotation mechanism
   - Solution: Implement key rotation for production

## Future Security Improvements

- [ ] Migrate to PostgreSQL for production
- [ ] Implement Redis-based rate limiting
- [ ] Add request logging and audit trails
- [ ] Implement 2FA/MFA authentication
- [ ] Add CSRF protection tokens
- [ ] Implement API key authentication
- [ ] Add encryption at rest for sensitive data
- [ ] Implement automatic key rotation
- [ ] Add comprehensive security testing (penetration testing)

## Incident Response

If a security vulnerability is discovered:
1. Do not commit the vulnerability to public repositories
2. Create a private security advisory
3. Patch the vulnerability
4. Rotate all potentially compromised secrets
5. Deploy the patch
6. Document the incident

## References

- [OWASP Top 10](https://owasp.org/Top10/)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)
- [JWT Best Practices](https://tools.ietf.org/html/rfc8725)
- [Password Storage Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html)
