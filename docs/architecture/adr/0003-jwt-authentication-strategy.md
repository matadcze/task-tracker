# ADR-0003: JWT Authentication Strategy

## Status

Accepted

## Date

2024-01-20

## Context

The application requires user authentication to:
- Protect task data (users can only see their own tasks)
- Track who performed actions (audit logging)
- Support stateless API requests (suitable for horizontal scaling)

We need to choose an authentication mechanism that is:
- Secure against common attacks
- Stateless for API scalability
- User-friendly (not requiring frequent re-login)

## Decision

We will use **JWT (JSON Web Tokens)** with a **dual-token strategy**:

### Token Types

| Token | Purpose | Expiry | Storage |
|-------|---------|--------|---------|
| **Access Token** | API authorization | 15 minutes | Memory/localStorage |
| **Refresh Token** | Obtain new access tokens | 7 days | localStorage + DB hash |

### Token Structure

```json
{
  "sub": "user-uuid",
  "exp": 1234567890,
  "type": "access|refresh"
}
```

### Implementation Details

1. **Signing**: HMAC-SHA256 (HS256) with secret key
2. **Refresh tokens stored**: Hash stored in database for revocation
3. **Token revocation**: Mark refresh token as revoked in DB
4. **Password hashing**: bcrypt with automatic salt

### Authentication Flow

```
1. Login: POST /auth/login {email, password}
   → Returns: {access_token, refresh_token}

2. API Request: GET /tasks
   Header: Authorization: Bearer <access_token>

3. Token Refresh: POST /auth/refresh {refresh_token}
   → Returns: {access_token, refresh_token}

4. Logout: Client deletes tokens (optional: revoke refresh token)
```

## Consequences

### Positive

- **Stateless**: No server-side session storage for access tokens
- **Scalable**: Any backend instance can verify tokens
- **Secure**: Short-lived access tokens limit exposure
- **Revocable**: Refresh tokens can be invalidated (logout, password change)
- **Standard**: Well-understood JWT ecosystem

### Negative

- **Token theft**: Access tokens valid until expiry (mitigated by short expiry)
- **Database lookup**: Refresh token validation requires DB query
- **Complexity**: Two token types to manage
- **localStorage risks**: XSS could steal tokens (mitigated by short expiry)

### Neutral

- Client must implement token refresh logic
- Need to handle token expiry gracefully in UI

## Alternatives Considered

### Alternative 1: Session-based Authentication

**Description:** Server stores session ID in database, client sends session cookie.

**Pros:**
- Simple to implement
- Easy revocation (delete session)
- No token theft concerns

**Cons:**
- Requires session storage (Redis/DB)
- Harder to scale horizontally
- CSRF protection needed

**Why not chosen:** Stateful sessions complicate horizontal scaling.

### Alternative 2: Single Long-lived JWT

**Description:** One JWT with long expiry (e.g., 30 days).

**Pros:**
- Simpler implementation
- No refresh flow needed

**Cons:**
- Long exposure if token stolen
- Cannot revoke without blacklist
- Security risk

**Why not chosen:** Unacceptable security risk from long-lived tokens.

### Alternative 3: OAuth 2.0 / OpenID Connect

**Description:** Full OAuth implementation with external identity provider.

**Pros:**
- Industry standard
- Supports social login
- Well-audited flows

**Cons:**
- Complexity overhead for single-tenant app
- External dependency (or self-hosted)
- Over-engineered for current needs

**Why not chosen:** Appropriate for multi-tenant SaaS, not needed here.

### Alternative 4: API Keys

**Description:** Static API keys per user.

**Pros:**
- Very simple
- Good for service-to-service

**Cons:**
- No expiry (security risk)
- No user login flow
- Key rotation is manual

**Why not chosen:** Not suitable for end-user authentication.

## Security Considerations

### Implemented Mitigations

| Threat | Mitigation |
|--------|------------|
| Token theft | Short 15-minute access token expiry |
| Brute force | Rate limiting (100 req/min) |
| Password cracking | bcrypt with cost factor |
| Token reuse after logout | Refresh token revocation in DB |
| Token forgery | HMAC signature verification |

### Token Storage Recommendations (Client)

```javascript
// Access token: memory only (lost on page refresh)
let accessToken = null;

// Refresh token: localStorage (persists)
localStorage.setItem('refresh_token', token);

// On page load: use refresh token to get new access token
```

## References

- [JWT Best Practices (RFC 8725)](https://datatracker.ietf.org/doc/html/rfc8725)
- [OWASP Authentication Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Authentication_Cheat_Sheet.html)
- [python-jose library](https://python-jose.readthedocs.io/)
