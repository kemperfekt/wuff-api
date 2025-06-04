# WuffChat Agent (Backend API)

This is the backend API service for WuffChat. For comprehensive documentation, please refer to the [main WuffChat README](https://github.com/kemperfekt/wuffchat).

## Quick Links

- 📚 [Full Documentation](https://github.com/kemperfekt/wuffchat)
- 🏗️ [Architecture Overview](https://github.com/kemperfekt/wuffchat#-architecture-overview)
- 🚀 [Quick Start Guide](https://github.com/kemperfekt/wuffchat#-quick-start)
- 🔧 [Development Setup](https://github.com/kemperfekt/wuffchat#-development)
- 📊 [API Documentation](https://api.wuffchat.de/docs)

## Local Development

```bash
# Setup
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Run
uvicorn src.main:app --reload --port 8000

# Test
pytest
```

## Key Features
- V2 FSM-based architecture
- GPT-4 powered responses from dog's perspective
- Weaviate vector search integration
- 11-state conversation flow
- Comprehensive test coverage
- Enterprise-grade security implementation

## 🔒 Security Architecture

WuffChat implements comprehensive security measures to protect user data and prevent abuse:

### Authentication & Authorization
- **API Key Authentication**: All protected endpoints require X-API-Key header
- **Environment-based Keys**: Secure API key management with auto-generation for development
- **Public Endpoint Protection**: Health checks and docs remain accessible

### Session Security
- **Secure Session Tokens**: 32-byte URL-safe tokens beyond simple UUIDs
- **Session Expiration**: 30-minute automatic timeout with activity refresh
- **Token Validation**: Cryptographically secure token comparison using `secrets.compare_digest()`
- **Automatic Cleanup**: Expired sessions are automatically purged every 5 minutes

### Rate Limiting
- **IP-based Limiting**: Powered by slowapi with proxy support for Scalingo
- **Endpoint-specific Limits**: 
  - `/flow_intro`: 10 requests/minute  
  - `/flow_step`: 30 requests/minute
- **Custom Error Messages**: User-friendly German rate limit messages
- **Rate Limit Headers**: X-RateLimit-* headers for client awareness

### Error Handling & Information Security
- **Error Message Sanitization**: Generic user messages, detailed internal logging
- **Safe Error Responses**: No sensitive data (API keys, paths, internal errors) exposed
- **Structured Error Handling**: Consistent error format across all endpoints

### Security Headers
- **X-Frame-Options**: DENY (prevents clickjacking)
- **X-Content-Type-Options**: nosniff (prevents MIME sniffing)  
- **Strict-Transport-Security**: HSTS for HTTPS enforcement
- **X-XSS-Protection**: Browser XSS filter enabled
- **Referrer-Policy**: strict-origin-when-cross-origin
- **Permissions-Policy**: Restricts geolocation, microphone, camera access
- **Server Header Removal**: Hides technology stack information

### CORS & Network Security
- **Environment-aware CORS**: Localhost blocked in production, allowed in development
- **Production Domain Whitelist**: Only trusted domains allowed in production
- **Credential Support**: Secure cross-origin authentication enabled

### Input Validation
- **Pydantic Models**: Runtime type validation for all API inputs
- **Session ID Validation**: Format and existence verification
- **Message Length Limits**: Prevents oversized inputs

### Monitoring & Compliance
- **Security Event Logging**: Authentication failures, rate limit violations logged
- **Audit Trail**: All security events tracked with timestamps and IPs
- **Test Coverage**: Comprehensive security test suite in `tests/test_security.py`

### Security Testing
```bash
# Run security tests
pytest tests/test_security.py -v

# Test session security specifically  
python tests/test_session_security.py
```

### Production Security Checklist
- ✅ API authentication with secure key rotation
- ✅ Rate limiting with appropriate thresholds
- ✅ Session security with token-based auth
- ✅ Error message sanitization
- ✅ Security headers implemented
- ✅ CORS properly configured for production
- ⚠️ Input validation (basic implementation, HTML sanitization pending)
- ⚠️ Security monitoring (logging implemented, alerting pending)

For detailed security audit results, see `.CLAUDE_CONTENT/INFRASTRUCTURE/SECURITY_AUDIT.md`.

For detailed information, see the [main repository documentation](https://github.com/kemperfekt/wuffchat).