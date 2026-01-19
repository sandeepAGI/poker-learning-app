# Azure Deployment Plan - Poker Learning App

**Status:** FINAL - Ready for Execution
**Version:** 3.0 (User Authentication Added)
**Created:** 2026-01-12
**Last Updated:** 2026-01-12

---

## Executive Summary

This plan details the deployment of the Poker Learning App to Microsoft Azure with GitHub Actions CI/CD integration. The architecture includes user authentication, persistent storage, scalability, and comprehensive monitoring.

### Key Highlights

- **Backend**: Azure App Service (Linux B2, Python 3.12) with WebSocket support
- **Frontend**: Azure App Service (Linux B1, Node.js 20) for Next.js 15
- **Authentication**: Auth0 (OAuth + email/password, passwordless magic links)
- **Data Layer**: Redis (session/game state) + PostgreSQL (hand history + user data)
- **Secrets**: Azure Key Vault with managed identity
- **Monitoring**: Application Insights with comprehensive alerting
- **CI/CD**: GitHub Actions with automated testing and deployment
- **Monthly Cost**: ~$145/month (production), ~$47/month (staging)

### Architecture Improvements from Review

✅ **Added persistent storage** (Redis + PostgreSQL)
✅ **Added user authentication** (Auth0 with OAuth + passwordless)
✅ **User accounts & progress tracking** (game history, stats, analysis cache)
✅ **Fixed startup command** (gunicorn + uvicorn workers)
✅ **Right-sized tiers** (B2 instead of over-provisioned P1v3)
✅ **Enhanced security** (CORS, rate limiting, TLS config, Auth0 JWT validation)
✅ **Comprehensive monitoring** (10+ alert rules)
✅ **Added pre-deployment phase** (fixes required before Azure setup)

### New User Features Enabled

✅ **"My Games" dashboard** - View all past games with stats
✅ **Analysis history** - Access cached analyses (saves Anthropic API costs)
✅ **Progress tracking** - Win rate, hands played, improvement over time
✅ **Resume games** - Continue games across sessions/devices
✅ **Personalized coaching** - AI references play history for better insights

---

## Table of Contents

1. [Architecture Overview](#architecture-overview)
2. [Azure Services Selection](#azure-services-selection)
3. [Authentication Strategy](#authentication-strategy-new)
4. [Database Schema](#database-schema-with-users)
5. [Environment Strategy](#environment-strategy)
6. [Pre-Deployment Requirements](#pre-deployment-requirements-new)
7. [Deployment Steps](#deployment-steps)
8. [Security Configuration](#security-configuration)
9. [Cost Analysis](#cost-analysis)
10. [Monitoring & Operations](#monitoring--operations)
11. [Rollback & Disaster Recovery](#rollback--disaster-recovery)
12. [Deployment Checklist](#deployment-checklist)

---

## Architecture Overview

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        GitHub Repository                         │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Backend Code │  │Frontend Code │  │ GitHub       │          │
│  │              │  │              │  │ Actions      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────┬───────────────────────────────────┘
                              │ CI/CD Deployment
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         Azure Cloud                              │
│                                                                   │
│  ┌────────────────────────────────────────────────────────────┐ │
│  │              Resource Group: poker-learning-app-rg          │ │
│  │                                                             │ │
│  │  ┌──────────────────────┐    ┌──────────────────────┐    │ │
│  │  │  App Service         │    │ App Service          │    │ │
│  │  │  (Backend API)       │◄───┤ (Frontend)           │    │ │
│  │  │                      │    │                      │    │ │
│  │  │  - Python 3.12       │    │  - Node.js 20        │    │ │
│  │  │  - FastAPI           │    │  - Next.js 15        │    │ │
│  │  │  - WebSocket         │    │  - React 19          │    │ │
│  │  │  - JWT validation    │    │  - Auth0 SDK         │    │ │
│  │  │  - B2 Tier           │    │  - B1 Tier           │    │ │
│  │  └──────────────────────┘    └──────────────────────┘    │ │
│  │           │                            │                  │ │
│  │           │                            │                  │ │
│  │           ▼                            ▼                  │ │
│  │  ┌──────────────────────┐    ┌──────────────────────┐   │ │
│  │  │  Redis Cache         │    │ PostgreSQL Database  │   │ │
│  │  │  - Session/Game State│    │  - Users             │   │ │
│  │  │  - Standard C1       │    │  - Games & History   │   │ │
│  │  └──────────────────────┘    │  - User Stats        │   │ │
│  │           │                   │  - Analysis Cache    │   │ │
│  │           │                   │  - B1ms Burstable    │   │ │
│  │           │                   └──────────────────────┘   │ │
│  │           ▼                            ▲                 │ │
│  │  ┌──────────────────────┐             │                 │ │
│  │  │  Azure Key Vault     │             │                 │ │
│  │  │  - API Keys          │             │                 │ │
│  │  │  - Auth0 Secrets     │             │                 │ │
│  │  │  - DB Credentials    │             │                 │ │
│  │  └──────────────────────┘             │                 │ │
│  │           │                            │                 │ │
│  │           ▼                            │                 │ │
│  │  ┌──────────────────────┐             │                 │ │
│  │  │ Application Insights │             │                 │ │
│  │  │  - Logs & Metrics    │             │                 │ │
│  │  │  - User Analytics    │             │                 │ │
│  │  │  - Alerts            │             │                 │ │
│  │  └──────────────────────┘             │                 │ │
│  │                                        │                 │ │
│  └────────────────────────────────────────┼─────────────────┘ │
└─────────────────────────────────────────┼───────────────────┘
                                          │
                    ┌─────────────────────┼──────────────────┐
                    │                     │                  │
                    ▼                     ▼                  ▼
          ┌──────────────┐    ┌──────────────┐   ┌─────────────┐
          │  Auth0       │    │ Anthropic API│   │ PostgreSQL  │
          │  - OAuth     │    │ (Claude AI)  │   │ (User Data) │
          │  - Passwordless│  └──────────────┘   └─────────────┘
          │  - User Mgmt │
          └──────────────┘
```

### Data Flow

1. **User Authentication**: Browser → Frontend → Auth0 → Frontend (JWT token)
2. **Authenticated Request**: Frontend (with JWT) → Backend → Validate JWT → Process
3. **Game State**: Backend ↔ Redis (active games, sessions)
4. **User Data**: Backend ↔ PostgreSQL (users, games, history, stats)
5. **WebSocket**: Authenticated persistent connection for real-time game updates
6. **AI Analysis**: Backend → Anthropic API → PostgreSQL (cached by user_id + hand_id)
7. **Monitoring**: All services → Application Insights

---

## Azure Services Selection

### 1. Backend: Azure App Service (Linux, Python 3.12)

**Selected Tier**: Basic B2
**Cost**: $26.06/month
**Specs**: 2 vCore, 3.5 GB RAM, 10 GB storage

**Why App Service?**
- ✅ Native WebSocket support (critical for real-time game updates)
- ✅ Built-in Python 3.12 runtime
- ✅ Always-on capability (no cold starts)
- ✅ Simple deployment model
- ✅ Built-in SSL/TLS
- ✅ Integrated with Application Insights

---

### 2. Frontend: Azure App Service (Linux, Node.js 20)

**Selected Tier**: Basic B1
**Cost**: $13.14/month (separate App Service Plan)
**Specs**: 1 vCore, 1.75 GB RAM, 10 GB storage

**Why App Service (Not Static Web Apps)?**
- ✅ Full Next.js 15 support (SSR, API routes, middleware)
- ✅ App Router compatibility
- ✅ Server-side Auth0 session management
- ✅ Future-proof for server components

---

### 3. Data Layer: Redis + PostgreSQL

#### Redis (Azure Cache for Redis)

**Selected Tier**: Standard C1
**Cost**: $61.68/month
**Specs**: 1 GB cache, High Availability (99.9% SLA)

**Purpose**:
- Active game state storage (linked to user_id)
- WebSocket session management
- Rate limiting counters (per user)
- Temporary analysis cache (TTL-based)

#### PostgreSQL (Azure Database for PostgreSQL Flexible Server)

**Selected Tier**: Burstable B1ms
**Cost**: $13.63/month
**Specs**: 1 vCore, 2 GB RAM, 32 GB storage

**Purpose**:
- **User accounts** (email, display name, auth metadata)
- **User games** (game history, final stacks, timestamps)
- **Hand history** (for analysis feature)
- **User statistics** (win rate, hands played, improvement metrics)
- **Analysis cache** (per user + hand, saves Anthropic API costs)
- **Audit logs** (user actions, security events)

---

### 4. Authentication: Auth0

**Selected Tier**: Free (up to 7,000 monthly active users)
**Cost**: $0/month (Free tier), scales to $23/month (Essentials) at 1,000+ users
**Specs**: Unlimited logins, social connections, passwordless

**Why Auth0?**
- ✅ **No password management** (OAuth + passwordless magic links)
- ✅ **Social login** (Google, GitHub, Apple)
- ✅ **Passwordless** (email magic links - best UX)
- ✅ **Built-in UI** (Universal Login, customizable)
- ✅ **JWT tokens** (secure, stateless authentication)
- ✅ **User management** (admin dashboard included)
- ✅ **Azure integration** (seamless with App Service)
- ✅ **MFA support** (optional, for premium users)
- ✅ **SDKs available** (Python, JavaScript/React)

**Alternatives Considered**:
- Self-hosted auth: ❌ Complex, security risks, 1-2 weeks development
- Firebase Auth: ⚠️ Good, but Auth0 has better enterprise features
- Azure AD B2C: ⚠️ More expensive, complex setup

---

### 5. Secrets Management: Azure Key Vault

**Selected Tier**: Standard
**Cost**: ~$5/month
**Operations**: $0.03 per 10,000 operations

**Secrets Stored**:
- `ANTHROPIC_API_KEY` (production key)
- `REDIS_PASSWORD` (Redis connection password)
- `DATABASE_URL` (PostgreSQL connection string)
- `AUTH0_DOMAIN` (Auth0 tenant domain)
- `AUTH0_CLIENT_ID` (Auth0 application client ID)
- `AUTH0_CLIENT_SECRET` (Auth0 application secret)
- `AUTH0_API_AUDIENCE` (Auth0 API identifier)

---

### 6. Monitoring: Application Insights

**Selected Tier**: Pay-as-you-go
**Cost**: ~$5-10/month (30-day retention)
**Data Ingestion**: First 5 GB/month free, then $2.30/GB

**Monitored Metrics**:
- Request/response times (P50, P95, P99)
- Error rates (HTTP 5xx)
- **User authentication events** (login, logout, failures)
- WebSocket connection health
- Anthropic API call costs (per user)
- Memory and CPU usage
- **User engagement** (daily/monthly active users, session duration)
- **Game metrics** (games per user, hands played, win rates)

---

## Authentication Strategy (NEW)

### Auth0 Configuration

**Authentication Methods**:
1. **Passwordless (Magic Links)** - Recommended default
   - User enters email → Receives magic link → Clicks to login
   - No password to remember or reset
   - Best UX, highest security

2. **Social OAuth** - Optional
   - Google (most popular)
   - GitHub (for developer audience)
   - Apple (iOS users)

3. **Email/Password** - Fallback
   - Traditional method
   - Requires password reset flow
   - Only if users prefer it

### JWT Token Flow

```
1. User clicks "Login" on frontend
   ↓
2. Frontend redirects to Auth0 Universal Login
   ↓
3. User authenticates (magic link / social / password)
   ↓
4. Auth0 redirects back to frontend with authorization code
   ↓
5. Frontend exchanges code for JWT access token + ID token
   ↓
6. Frontend stores tokens in secure HTTP-only cookies
   ↓
7. Frontend sends API requests with JWT in Authorization header
   ↓
8. Backend validates JWT signature (Auth0 public key)
   ↓
9. Backend extracts user_id from JWT claims
   ↓
10. Backend processes request with user context
```

### Backend JWT Validation

```python
# backend/auth.py
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError
import requests
import os

security = HTTPBearer()

# Auth0 configuration
AUTH0_DOMAIN = os.getenv("AUTH0_DOMAIN")  # e.g., poker-app.us.auth0.com
AUTH0_API_AUDIENCE = os.getenv("AUTH0_API_AUDIENCE")  # API identifier
AUTH0_ALGORITHMS = ["RS256"]

# Cache JWKs (JSON Web Keys) for JWT signature verification
jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
jwks = requests.get(jwks_url).json()

def verify_token(credentials: HTTPAuthorizationCredentials = Security(security)):
    """Verify JWT token from Auth0"""
    token = credentials.credentials

    try:
        # Decode and verify JWT
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = {}

        for key in jwks["keys"]:
            if key["kid"] == unverified_header["kid"]:
                rsa_key = {
                    "kty": key["kty"],
                    "kid": key["kid"],
                    "use": key["use"],
                    "n": key["n"],
                    "e": key["e"]
                }

        if rsa_key:
            payload = jwt.decode(
                token,
                rsa_key,
                algorithms=AUTH0_ALGORITHMS,
                audience=AUTH0_API_AUDIENCE,
                issuer=f"https://{AUTH0_DOMAIN}/"
            )
            return payload  # Contains user_id (sub), email, etc.

        raise HTTPException(status_code=401, detail="Unable to find appropriate key")

    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Invalid token: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")

# Dependency for protected endpoints
async def get_current_user(payload: dict = Security(verify_token)) -> dict:
    """Extract user info from JWT payload"""
    user_id = payload.get("sub")  # Auth0 user ID
    email = payload.get("email")

    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token: missing user_id")

    return {
        "user_id": user_id,
        "email": email,
        "name": payload.get("name"),
        "picture": payload.get("picture"),
    }

# Usage in endpoints
@app.post("/games")
async def create_game(
    current_user: dict = Depends(get_current_user),
    num_ai_players: int = 3
):
    user_id = current_user["user_id"]
    # Create game for this user...
```

### Frontend Auth0 Integration

```typescript
// frontend/lib/auth0.ts
import { Auth0Provider, useAuth0 } from '@auth0/auth0-react';

// Auth0 configuration
const auth0Config = {
  domain: process.env.NEXT_PUBLIC_AUTH0_DOMAIN!,
  clientId: process.env.NEXT_PUBLIC_AUTH0_CLIENT_ID!,
  authorizationParams: {
    redirect_uri: typeof window !== 'undefined' ? window.location.origin : '',
    audience: process.env.NEXT_PUBLIC_AUTH0_AUDIENCE,
    scope: 'openid profile email'
  }
};

// Wrap app in Auth0Provider
export function AuthProvider({ children }: { children: React.ReactNode }) {
  return (
    <Auth0Provider {...auth0Config}>
      {children}
    </Auth0Provider>
  );
}

// Hook to use in components
export function useAuth() {
  const {
    isAuthenticated,
    isLoading,
    user,
    loginWithRedirect,
    logout,
    getAccessTokenSilently
  } = useAuth0();

  const getToken = async () => {
    try {
      return await getAccessTokenSilently();
    } catch (error) {
      console.error('Error getting token:', error);
      return null;
    }
  };

  return {
    isAuthenticated,
    isLoading,
    user,
    login: loginWithRedirect,
    logout: () => logout({ logoutParams: { returnTo: window.location.origin } }),
    getToken
  };
}

// API client with auth
export async function apiClient(endpoint: string, options: RequestInit = {}) {
  const { getToken } = useAuth();
  const token = await getToken();

  const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}${endpoint}`, {
    ...options,
    headers: {
      ...options.headers,
      'Content-Type': 'application/json',
      ...(token && { 'Authorization': `Bearer ${token}` })
    }
  });

  if (!response.ok) {
    throw new Error(`API error: ${response.statusText}`);
  }

  return response.json();
}
```

### User Profile Component

```typescript
// frontend/components/UserProfile.tsx
import { useAuth } from '@/lib/auth0';

export function UserProfile() {
  const { isAuthenticated, isLoading, user, login, logout } = useAuth();

  if (isLoading) {
    return <div>Loading...</div>;
  }

  if (!isAuthenticated) {
    return (
      <button onClick={() => login()}>
        Login
      </button>
    );
  }

  return (
    <div className="flex items-center gap-4">
      <img
        src={user?.picture}
        alt={user?.name}
        className="w-10 h-10 rounded-full"
      />
      <div>
        <p className="font-semibold">{user?.name}</p>
        <p className="text-sm text-gray-500">{user?.email}</p>
      </div>
      <button onClick={() => logout()}>
        Logout
      </button>
    </div>
  );
}
```

---

## Database Schema (With Users)

### Complete PostgreSQL Schema

```sql
-- ============================================================================
-- USER MANAGEMENT
-- ============================================================================

-- Users table (Auth0 user data)
CREATE TABLE users (
    user_id VARCHAR(255) PRIMARY KEY,  -- Auth0 user ID (e.g., "auth0|...")
    email VARCHAR(255) UNIQUE NOT NULL,
    display_name VARCHAR(100),
    picture_url VARCHAR(500),  -- Profile picture from social login
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP,
    email_verified BOOLEAN DEFAULT FALSE,
    metadata JSONB,  -- Extra user preferences, settings

    -- Indexes
    INDEX idx_users_email (email),
    INDEX idx_users_created_at (created_at)
);

-- User statistics (aggregated metrics)
CREATE TABLE user_stats (
    user_id VARCHAR(255) PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    total_games INT DEFAULT 0,
    total_hands INT DEFAULT 0,
    total_time_played INT DEFAULT 0,  -- seconds

    -- Win/loss tracking
    hands_won INT DEFAULT 0,
    hands_lost INT DEFAULT 0,
    win_rate FLOAT GENERATED ALWAYS AS (
        CASE WHEN total_hands > 0
        THEN (hands_won::FLOAT / total_hands::FLOAT) * 100
        ELSE 0 END
    ) STORED,

    -- Financial metrics
    total_profit INT DEFAULT 0,  -- Net profit/loss across all games
    biggest_win INT DEFAULT 0,
    biggest_loss INT DEFAULT 0,
    avg_final_stack INT DEFAULT 0,

    -- Skill metrics
    avg_vpip FLOAT,  -- Voluntarily Put $ In Pot %
    avg_pfr FLOAT,   -- Pre-Flop Raise %
    avg_aggression FLOAT,  -- Aggression factor

    -- Improvement tracking
    initial_win_rate FLOAT,  -- Win rate from first 100 hands
    last_30_days_win_rate FLOAT,
    improvement_score FLOAT,  -- Calculated improvement metric

    -- Analysis usage
    analyses_requested INT DEFAULT 0,
    total_analysis_cost FLOAT DEFAULT 0.0,  -- Total $ spent on AI analysis

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ============================================================================
-- GAME MANAGEMENT
-- ============================================================================

-- Games table (now linked to users)
CREATE TABLE games (
    game_id VARCHAR(50) PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,

    -- Game configuration
    num_ai_players INT NOT NULL,
    starting_stack INT NOT NULL,
    small_blind INT NOT NULL,
    big_blind INT NOT NULL,

    -- Game state
    current_hand INT DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',  -- active, completed, abandoned

    -- Timestamps
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Final results
    final_stack INT,
    total_hands_played INT DEFAULT 0,
    session_duration INT,  -- seconds
    profit_loss INT GENERATED ALWAYS AS (final_stack - starting_stack) STORED,

    -- Indexes
    INDEX idx_games_user_id (user_id),
    INDEX idx_games_status (status),
    INDEX idx_games_started_at (started_at),
    INDEX idx_games_user_started (user_id, started_at)
);

-- Hands table (detailed hand history)
CREATE TABLE hands (
    hand_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    game_id VARCHAR(50) NOT NULL REFERENCES games(game_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    hand_number INT NOT NULL,

    -- Hand details
    board_cards JSONB,  -- Community cards
    pot INT NOT NULL,
    winner_id VARCHAR(50),  -- player_id of winner
    winner_name VARCHAR(100),

    -- User's hand
    user_hole_cards JSONB,  -- User's private cards
    user_position VARCHAR(10),  -- button, SB, BB, etc.
    user_starting_stack INT,
    user_final_stack INT,
    user_won BOOLEAN,

    -- Hand metadata
    phases_played JSONB,  -- [pre_flop, flop, turn, river, showdown]
    total_actions INT,
    hand_duration INT,  -- seconds

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_hands_game_id (game_id),
    INDEX idx_hands_user_id (user_id),
    INDEX idx_hands_created_at (created_at),
    INDEX idx_hands_user_game (user_id, game_id, hand_number)
);

-- Actions table (granular action tracking)
CREATE TABLE actions (
    action_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    hand_id UUID NOT NULL REFERENCES hands(hand_id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id),

    -- Action details
    player_id VARCHAR(50) NOT NULL,  -- ID of player taking action
    player_name VARCHAR(100),
    action VARCHAR(20) NOT NULL,  -- fold, call, raise, check, all_in
    amount INT,

    -- Context
    phase VARCHAR(20),  -- pre_flop, flop, turn, river
    position VARCHAR(10),
    stack_before INT,
    stack_after INT,
    pot_before INT,
    pot_after INT,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_actions_hand_id (hand_id),
    INDEX idx_actions_user_id (user_id),
    INDEX idx_actions_timestamp (timestamp)
);

-- ============================================================================
-- ANALYSIS & CACHING
-- ============================================================================

-- Analysis cache (saves Anthropic API costs)
CREATE TABLE analysis_cache (
    cache_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL REFERENCES users(user_id) ON DELETE CASCADE,
    hand_id UUID NOT NULL REFERENCES hands(hand_id) ON DELETE CASCADE,

    -- Analysis details
    analysis_type VARCHAR(20) NOT NULL,  -- quick, deep
    model_used VARCHAR(50) NOT NULL,  -- claude-haiku-4-5, claude-sonnet-4-5
    cost FLOAT NOT NULL,

    -- Analysis content
    analysis_data JSONB NOT NULL,  -- Full analysis response
    summary TEXT,
    tips JSONB,  -- Array of improvement tips

    -- Caching
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    accessed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    access_count INT DEFAULT 1,

    -- UNIQUE constraint: one analysis per user+hand+type
    UNIQUE (user_id, hand_id, analysis_type),

    -- Indexes
    INDEX idx_analysis_user_id (user_id),
    INDEX idx_analysis_hand_id (hand_id),
    INDEX idx_analysis_created_at (created_at)
);

-- ============================================================================
-- AUDIT & SECURITY
-- ============================================================================

-- Audit log (user actions, security events)
CREATE TABLE audit_log (
    log_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) REFERENCES users(user_id) ON DELETE SET NULL,

    -- Event details
    event_type VARCHAR(50) NOT NULL,  -- login, logout, game_created, etc.
    event_data JSONB,

    -- Security
    ip_address INET,
    user_agent TEXT,

    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- Indexes
    INDEX idx_audit_user_id (user_id),
    INDEX idx_audit_event_type (event_type),
    INDEX idx_audit_timestamp (timestamp)
);

-- ============================================================================
-- VIEWS (Materialized for performance)
-- ============================================================================

-- User dashboard summary
CREATE MATERIALIZED VIEW user_dashboard AS
SELECT
    u.user_id,
    u.display_name,
    u.email,
    u.picture_url,
    u.created_at,
    u.last_login,

    -- Game stats
    us.total_games,
    us.total_hands,
    us.win_rate,
    us.total_profit,
    us.avg_final_stack,
    us.improvement_score,

    -- Recent activity
    (SELECT COUNT(*) FROM games WHERE user_id = u.user_id AND started_at > NOW() - INTERVAL '7 days') as games_last_7_days,
    (SELECT COUNT(*) FROM hands WHERE user_id = u.user_id AND created_at > NOW() - INTERVAL '7 days') as hands_last_7_days,

    -- Analysis stats
    us.analyses_requested,
    us.total_analysis_cost,

    -- Latest game
    (SELECT game_id FROM games WHERE user_id = u.user_id ORDER BY started_at DESC LIMIT 1) as latest_game_id,
    (SELECT started_at FROM games WHERE user_id = u.user_id ORDER BY started_at DESC LIMIT 1) as latest_game_started

FROM users u
LEFT JOIN user_stats us ON u.user_id = us.user_id;

-- Refresh command (run periodically or after significant updates)
-- REFRESH MATERIALIZED VIEW user_dashboard;

-- ============================================================================
-- FUNCTIONS & TRIGGERS
-- ============================================================================

-- Update user stats after game completion
CREATE OR REPLACE FUNCTION update_user_stats_on_game_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.status = 'completed' AND OLD.status != 'completed' THEN
        UPDATE user_stats
        SET
            total_games = total_games + 1,
            total_hands = total_hands + NEW.total_hands_played,
            total_time_played = total_time_played + COALESCE(NEW.session_duration, 0),
            total_profit = total_profit + (NEW.final_stack - NEW.starting_stack),
            avg_final_stack = (avg_final_stack * total_games + NEW.final_stack) / (total_games + 1),
            updated_at = NOW()
        WHERE user_id = NEW.user_id;

        -- Create user_stats if doesn't exist
        INSERT INTO user_stats (user_id)
        VALUES (NEW.user_id)
        ON CONFLICT (user_id) DO NOTHING;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_user_stats
AFTER UPDATE ON games
FOR EACH ROW
EXECUTE FUNCTION update_user_stats_on_game_complete();

-- Update hands won/lost after hand completion
CREATE OR REPLACE FUNCTION update_user_stats_on_hand_complete()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.user_won IS NOT NULL THEN
        UPDATE user_stats
        SET
            hands_won = hands_won + CASE WHEN NEW.user_won THEN 1 ELSE 0 END,
            hands_lost = hands_lost + CASE WHEN NEW.user_won THEN 0 ELSE 1 END,
            updated_at = NOW()
        WHERE user_id = NEW.user_id;
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_hands_stats
AFTER INSERT ON hands
FOR EACH ROW
EXECUTE FUNCTION update_user_stats_on_hand_complete();

-- Update analysis cost tracking
CREATE OR REPLACE FUNCTION update_analysis_costs()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE user_stats
    SET
        analyses_requested = analyses_requested + 1,
        total_analysis_cost = total_analysis_cost + NEW.cost,
        updated_at = NOW()
    WHERE user_id = NEW.user_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_analysis_costs
AFTER INSERT ON analysis_cache
FOR EACH ROW
EXECUTE FUNCTION update_analysis_costs();

-- Update last_activity on games
CREATE OR REPLACE FUNCTION update_game_activity()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE games
    SET last_activity = NOW()
    WHERE game_id = NEW.game_id;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_game_activity_on_hand
AFTER INSERT ON hands
FOR EACH ROW
EXECUTE FUNCTION update_game_activity();

-- ============================================================================
-- SAMPLE QUERIES
-- ============================================================================

-- Get user's game history with stats
-- SELECT
--     g.game_id,
--     g.started_at,
--     g.completed_at,
--     g.total_hands_played,
--     g.final_stack,
--     g.profit_loss,
--     g.session_duration,
--     (SELECT COUNT(*) FROM hands WHERE game_id = g.game_id AND user_won = TRUE) as hands_won
-- FROM games g
-- WHERE g.user_id = 'auth0|123456789'
--   AND g.status = 'completed'
-- ORDER BY g.started_at DESC
-- LIMIT 20;

-- Get user's recent analyses (cached)
-- SELECT
--     h.hand_number,
--     h.created_at as hand_played_at,
--     ac.analysis_type,
--     ac.model_used,
--     ac.summary,
--     ac.tips,
--     ac.created_at as analyzed_at,
--     ac.cost
-- FROM analysis_cache ac
-- JOIN hands h ON ac.hand_id = h.hand_id
-- WHERE ac.user_id = 'auth0|123456789'
-- ORDER BY ac.created_at DESC
-- LIMIT 10;

-- Get leaderboard (top players by win rate, min 100 hands)
-- SELECT
--     u.display_name,
--     u.picture_url,
--     us.total_games,
--     us.total_hands,
--     us.win_rate,
--     us.total_profit,
--     us.improvement_score
-- FROM user_stats us
-- JOIN users u ON us.user_id = u.user_id
-- WHERE us.total_hands >= 100
-- ORDER BY us.win_rate DESC
-- LIMIT 20;
```

### Schema Migration Strategy

```python
# backend/alembic/versions/001_add_user_tables.py
"""Add user authentication and user-specific tables

Revision ID: 001
Revises:
Create Date: 2026-01-12

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Create users table
    op.create_table('users',
        sa.Column('user_id', sa.String(255), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('display_name', sa.String(100)),
        sa.Column('picture_url', sa.String(500)),
        sa.Column('created_at', sa.TIMESTAMP(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('last_login', sa.TIMESTAMP()),
        sa.Column('email_verified', sa.Boolean(), server_default=sa.text('FALSE')),
        sa.Column('metadata', postgresql.JSONB()),
        sa.PrimaryKeyConstraint('user_id'),
        sa.UniqueConstraint('email')
    )
    op.create_index('idx_users_email', 'users', ['email'])
    op.create_index('idx_users_created_at', 'users', ['created_at'])

    # Create user_stats table
    op.create_table('user_stats',
        sa.Column('user_id', sa.String(255), nullable=False),
        # ... all other columns from schema above
        sa.PrimaryKeyConstraint('user_id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.user_id'], ondelete='CASCADE')
    )

    # Add user_id to existing games table
    op.add_column('games', sa.Column('user_id', sa.String(255), nullable=True))
    op.create_foreign_key('fk_games_user_id', 'games', 'users', ['user_id'], ['user_id'], ondelete='CASCADE')
    op.create_index('idx_games_user_id', 'games', ['user_id'])

    # Add user_id to hands table
    op.add_column('hands', sa.Column('user_id', sa.String(255), nullable=True))
    op.create_foreign_key('fk_hands_user_id', 'hands', 'users', ['user_id'], ['user_id'], ondelete='CASCADE')

    # ... continue for all tables

def downgrade():
    # Reverse all changes
    op.drop_table('user_stats')
    op.drop_table('analysis_cache')
    op.drop_column('hands', 'user_id')
    op.drop_column('games', 'user_id')
    op.drop_table('users')
```

---

## Environment Strategy

### Three Environments

| Environment | Purpose | Backend | Frontend | Redis | PostgreSQL | Auth0 | Monthly Cost |
|-------------|---------|---------|----------|-------|------------|-------|--------------|
| **Development** | Local dev | localhost | localhost | Docker | Docker | Dev tenant | $0 |
| **Staging** | Pre-prod testing | B1 | B1 (shared) | Basic C0 | B1ms | Staging tenant | ~$47 |
| **Production** | Live users | B2 | B1 | Standard C1 | B1ms | Prod tenant | ~$145 |

### Environment Configuration

```yaml
# Development (Local)
ENVIRONMENT: development
BACKEND_URL: http://localhost:8000
NEXT_PUBLIC_API_URL: http://localhost:8000
ANTHROPIC_API_KEY: <dev-key>
REDIS_HOST: localhost:6379
DATABASE_URL: postgresql://localhost/poker_dev

# Auth0 (Development)
AUTH0_DOMAIN: poker-app-dev.us.auth0.com
AUTH0_CLIENT_ID: <dev-client-id>
AUTH0_CLIENT_SECRET: <dev-secret>
AUTH0_API_AUDIENCE: https://api.poker-dev.local
NEXT_PUBLIC_AUTH0_DOMAIN: poker-app-dev.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID: <dev-client-id>
NEXT_PUBLIC_AUTH0_AUDIENCE: https://api.poker-dev.local

# Staging (Azure)
ENVIRONMENT: staging
BACKEND_URL: https://poker-api-staging.azurewebsites.net
NEXT_PUBLIC_API_URL: https://poker-api-staging.azurewebsites.net
ANTHROPIC_API_KEY: @KeyVault(ANTHROPIC-API-KEY-STAGING)
REDIS_HOST: poker-cache-staging.redis.cache.windows.net
DATABASE_URL: @KeyVault(DATABASE-URL-STAGING)

# Auth0 (Staging)
AUTH0_DOMAIN: @KeyVault(AUTH0-DOMAIN-STAGING)
AUTH0_CLIENT_ID: @KeyVault(AUTH0-CLIENT-ID-STAGING)
AUTH0_CLIENT_SECRET: @KeyVault(AUTH0-CLIENT-SECRET-STAGING)
AUTH0_API_AUDIENCE: @KeyVault(AUTH0-AUDIENCE-STAGING)
NEXT_PUBLIC_AUTH0_DOMAIN: poker-app-staging.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID: <staging-client-id>
NEXT_PUBLIC_AUTH0_AUDIENCE: https://api.poker-staging.app

# Production (Azure)
ENVIRONMENT: production
BACKEND_URL: https://poker-api-prod.azurewebsites.net
NEXT_PUBLIC_API_URL: https://poker-api-prod.azurewebsites.net
ANTHROPIC_API_KEY: @KeyVault(ANTHROPIC-API-KEY-PROD)
REDIS_HOST: poker-cache-prod.redis.cache.windows.net
DATABASE_URL: @KeyVault(DATABASE-URL-PROD)

# Auth0 (Production)
AUTH0_DOMAIN: @KeyVault(AUTH0-DOMAIN-PROD)
AUTH0_CLIENT_ID: @KeyVault(AUTH0-CLIENT-ID-PROD)
AUTH0_CLIENT_SECRET: @KeyVault(AUTH0-CLIENT-SECRET-PROD)
AUTH0_API_AUDIENCE: @KeyVault(AUTH0-AUDIENCE-PROD)
NEXT_PUBLIC_AUTH0_DOMAIN: poker-app.us.auth0.com
NEXT_PUBLIC_AUTH0_CLIENT_ID: <prod-client-id>
NEXT_PUBLIC_AUTH0_AUDIENCE: https://api.poker.app
```

---

## Pre-Deployment Requirements (NEW)

### Critical Fixes Required BEFORE Azure Setup

These changes must be implemented in the codebase **before starting Azure deployment**. Estimated time: **5-7 days** (was 3-4 days, +2-3 days for auth).

#### 1. User Authentication Implementation (2-3 days)

**Task**: Integrate Auth0 for user authentication

**Steps**:

```bash
# 1. Create Auth0 account and applications
# Visit: https://auth0.com/signup
# Create 3 tenants: dev, staging, production
# Create Application (Single Page Application) for each

# 2. Configure Auth0 applications
# - Allowed Callback URLs: http://localhost:3000, https://poker-web-staging.azurewebsites.net
# - Allowed Logout URLs: (same as callback)
# - Allowed Web Origins: (same as callback)
# - Enable Connections: Email (passwordless), Google, GitHub

# 3. Create Auth0 API (for backend)
# - Name: Poker Learning API
# - Identifier: https://api.poker.app (production), https://api.poker-staging.app (staging)
# - Signing Algorithm: RS256
# - Enable RBAC: No (not needed yet)

# 4. Add backend dependencies
# Add to backend/requirements.txt:
python-jose[cryptography]>=3.3.0
requests>=2.31.0
fastapi-jwt-auth>=0.5.0  # Optional, for easier JWT handling

# 5. Implement backend auth module (see Authentication Strategy section above)
# Create: backend/auth.py with JWT validation

# 6. Update backend endpoints to require authentication
# backend/main.py:
from auth import get_current_user

@app.post("/games")
async def create_game(
    current_user: dict = Depends(get_current_user),  # NEW
    num_ai_players: int = 3
):
    user_id = current_user["user_id"]
    # Create game linked to user...

@app.get("/games/{game_id}")
async def get_game(
    game_id: str,
    current_user: dict = Depends(get_current_user)  # NEW
):
    # Verify game belongs to user...

# 7. Add frontend dependencies
# frontend/package.json:
npm install @auth0/auth0-react @auth0/auth0-spa-js

# 8. Implement frontend auth (see Authentication Strategy section above)
# Create: frontend/lib/auth0.ts
# Create: frontend/components/UserProfile.tsx
# Update: frontend/pages/_app.tsx to wrap with AuthProvider

# 9. Update API client to include JWT
# frontend/lib/api.ts:
const token = await getToken();
const response = await fetch(url, {
  headers: {
    'Authorization': `Bearer ${token}`
  }
});

# 10. Add login/logout UI
# Create: frontend/pages/login.tsx
# Update: frontend/components/Header.tsx with login button
```

**Validation**:
```bash
# Test authentication flow
1. Start backend: cd backend && python main.py
2. Start frontend: cd frontend && npm run dev
3. Click "Login" → Redirects to Auth0
4. Login with email magic link
5. Redirected back to app with JWT
6. Create game → Backend receives valid JWT
7. Logout → Token cleared
```

---

#### 2. Database Implementation with Users (2-3 days)

**Task**: Replace in-memory storage with Redis + PostgreSQL, add user tables

**Changes** (see Database Schema section for complete schema):

```python
# 1. Add dependencies to backend/requirements.txt
redis>=5.0.0
psycopg2-binary>=2.9.9
sqlalchemy>=2.0.23
alembic>=1.13.0

# 2. Create database models (backend/models.py)
# Include User, UserStats, Game (with user_id), Hand, Action, AnalysisCache

# 3. Update backend to use database
# backend/main.py:
from models import User, Game, Hand, Action
from sqlalchemy.orm import Session

@app.post("/games")
async def create_game(
    current_user: dict = Depends(get_current_user),
    num_ai_players: int = 3,
    db: Session = Depends(get_db)
):
    # Create user if doesn't exist
    user = db.query(User).filter(User.user_id == current_user["user_id"]).first()
    if not user:
        user = User(
            user_id=current_user["user_id"],
            email=current_user["email"],
            display_name=current_user.get("name"),
            picture_url=current_user.get("picture")
        )
        db.add(user)
        db.commit()

    # Create game linked to user
    game = Game(
        game_id=str(uuid.uuid4()),
        user_id=user.user_id,
        num_ai_players=num_ai_players,
        ...
    )
    db.add(game)
    db.commit()

    # Save active game state to Redis (transient)
    save_game_to_redis(game.game_id, poker_game_state)

    return {"game_id": game.game_id}

# 4. Implement user dashboard endpoint
@app.get("/users/me/dashboard")
async def get_user_dashboard(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    stats = db.query(UserStats).filter(UserStats.user_id == current_user["user_id"]).first()
    recent_games = db.query(Game).filter(
        Game.user_id == current_user["user_id"]
    ).order_by(Game.started_at.desc()).limit(10).all()

    return {
        "user": current_user,
        "stats": stats,
        "recent_games": recent_games
    }

# 5. Implement game history endpoint
@app.get("/users/me/games")
async def get_user_games(
    current_user: dict = Depends(get_current_user),
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    games = db.query(Game).filter(
        Game.user_id == current_user["user_id"],
        Game.status == 'completed'
    ).order_by(Game.started_at.desc()).offset(offset).limit(limit).all()

    return {"games": games, "total": len(games)}

# 6. Update analysis endpoint to use cache
@app.get("/games/{game_id}/analysis-llm")
async def get_analysis(
    game_id: str,
    depth: str = "quick",
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Get last hand
    hand = db.query(Hand).filter(
        Hand.game_id == game_id,
        Hand.user_id == current_user["user_id"]
    ).order_by(Hand.hand_number.desc()).first()

    # Check cache
    cached = db.query(AnalysisCache).filter(
        AnalysisCache.user_id == current_user["user_id"],
        AnalysisCache.hand_id == hand.hand_id,
        AnalysisCache.analysis_type == depth
    ).first()

    if cached:
        # Return cached result (saves Anthropic API cost!)
        return {
            "analysis": cached.analysis_data,
            "model_used": cached.model_used,
            "cost": 0.0,  # No cost for cached result
            "cached": True
        }

    # Call Anthropic API
    result = await call_anthropic_api(hand, depth)

    # Save to cache
    cache_entry = AnalysisCache(
        user_id=current_user["user_id"],
        hand_id=hand.hand_id,
        analysis_type=depth,
        model_used=result["model"],
        cost=result["cost"],
        analysis_data=result["analysis"]
    )
    db.add(cache_entry)
    db.commit()

    return result

# 7. Create migrations
alembic init alembic
alembic revision --autogenerate -m "Add user tables"
alembic upgrade head
```

**Frontend Changes**:
```typescript
// Create user dashboard page
// frontend/pages/dashboard.tsx
export default function Dashboard() {
  const { user } = useAuth();
  const [stats, setStats] = useState(null);
  const [recentGames, setRecentGames] = useState([]);

  useEffect(() => {
    async function loadDashboard() {
      const data = await apiClient('/users/me/dashboard');
      setStats(data.stats);
      setRecentGames(data.recent_games);
    }
    loadDashboard();
  }, []);

  return (
    <div>
      <h1>Welcome back, {user.name}!</h1>

      <div className="stats-grid">
        <StatCard title="Total Games" value={stats?.total_games} />
        <StatCard title="Win Rate" value={`${stats?.win_rate?.toFixed(1)}%`} />
        <StatCard title="Total Hands" value={stats?.total_hands} />
        <StatCard title="Total Profit" value={`$${stats?.total_profit}`} />
      </div>

      <h2>Recent Games</h2>
      <GameList games={recentGames} />
    </div>
  );
}

// Create game history page
// frontend/pages/games/index.tsx
export default function GameHistory() {
  const [games, setGames] = useState([]);
  const [page, setPage] = useState(0);

  useEffect(() => {
    async function loadGames() {
      const data = await apiClient(`/users/me/games?limit=20&offset=${page * 20}`);
      setGames(data.games);
    }
    loadGames();
  }, [page]);

  return (
    <div>
      <h1>My Games</h1>
      <table>
        <thead>
          <tr>
            <th>Date</th>
            <th>Hands Played</th>
            <th>Final Stack</th>
            <th>Profit/Loss</th>
            <th>Duration</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          {games.map(game => (
            <tr key={game.game_id}>
              <td>{new Date(game.started_at).toLocaleDateString()}</td>
              <td>{game.total_hands_played}</td>
              <td>${game.final_stack}</td>
              <td className={game.profit_loss >= 0 ? 'text-green' : 'text-red'}>
                ${game.profit_loss}
              </td>
              <td>{formatDuration(game.session_duration)}</td>
              <td>
                <Link href={`/games/${game.game_id}/review`}>
                  Review
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>

      <Pagination page={page} onPageChange={setPage} />
    </div>
  );
}
```

---

#### 3. Fix Startup Command (30 minutes)

(No changes from previous version - see original plan)

---

#### 4. Security Fixes (1 day)

**Task**: Fix CORS, add rate limiting, security headers, **add JWT validation**

(See original plan plus Auth0 JWT validation from Authentication Strategy section)

---

#### 5. Application Insights Integration (2 hours)

**Task**: Add custom metrics tracking including **user analytics**

```python
# backend/main.py
from opencensus.ext.azure import metrics_exporter

# Track user events
def track_user_event(user_id: str, event_type: str, properties: dict = None):
    logger.info(
        event_type,
        extra={
            "custom_dimensions": {
                "user_id": user_id,
                "event_type": event_type,
                **(properties or {})
            }
        }
    )

# Track in endpoints
@app.post("/games")
async def create_game(current_user: dict = Depends(get_current_user), ...):
    track_user_event(current_user["user_id"], "game_created", {
        "num_ai_players": num_ai_players
    })
    ...

@app.get("/games/{game_id}/analysis-llm")
async def get_analysis(current_user: dict = Depends(get_current_user), ...):
    if cached:
        track_user_event(current_user["user_id"], "analysis_cache_hit", {
            "hand_id": hand.hand_id,
            "cost_saved": cached.cost
        })
    else:
        track_user_event(current_user["user_id"], "analysis_requested", {
            "hand_id": hand.hand_id,
            "depth": depth,
            "cost": result["cost"]
        })
    ...
```

---

### Pre-Deployment Checklist

- [ ] Auth0 account created (dev, staging, production tenants)
- [ ] Auth0 applications configured (SPAs + APIs)
- [ ] Backend JWT validation implemented
- [ ] Frontend Auth0 SDK integrated
- [ ] Login/logout UI created
- [ ] User tables added to PostgreSQL schema
- [ ] Database migrations created
- [ ] Redis client implementation complete
- [ ] Backend endpoints updated to require auth
- [ ] Backend endpoints linked to user_id
- [ ] User dashboard endpoint created
- [ ] Game history endpoint created
- [ ] Analysis caching by user implemented
- [ ] Startup command updated to gunicorn
- [ ] CORS configuration environment-specific
- [ ] Rate limiting implemented
- [ ] Security headers middleware added
- [ ] Application Insights user tracking added
- [ ] All tests passing with new infrastructure
- [ ] Local testing with Auth0 + Redis + PostgreSQL completed

**Estimated Timeline**: **5-7 days** of development work

---

## Deployment Steps

### Phase 1: Azure Account Setup (15 minutes)

(No changes from previous version - same as before)

---

### Phase 2: Backend Deployment Setup (120 minutes, was 90 minutes)

(Includes all previous steps PLUS Auth0 configuration)

#### 2.5 Create Key Vaults (Updated)

```bash
# Production Key Vault
az keyvault create \
  --name poker-kv-prod \
  --resource-group poker-learning-app-rg \
  --location eastus \
  --sku standard \
  --enable-rbac-authorization false \
  --bypass AzureServices \
  --default-action Deny \
  --tags environment=production

# Add Auth0 secrets (NEW)
az keyvault secret set \
  --vault-name poker-kv-prod \
  --name AUTH0-DOMAIN \
  --value "poker-app.us.auth0.com"

az keyvault secret set \
  --vault-name poker-kv-prod \
  --name AUTH0-CLIENT-ID \
  --value "<auth0-client-id>"

az keyvault secret set \
  --vault-name poker-kv-prod \
  --name AUTH0-CLIENT-SECRET \
  --value "<auth0-client-secret>"

az keyvault secret set \
  --vault-name poker-kv-prod \
  --name AUTH0-API-AUDIENCE \
  --value "https://api.poker.app"

# Add other secrets (ANTHROPIC_API_KEY, REDIS_PASSWORD, DATABASE_URL) as before
```

#### 2.7 Configure App Service Environment Variables (Updated)

```bash
# Production backend configuration (UPDATED with Auth0)
az webapp config appsettings set \
  --name poker-api-prod \
  --resource-group poker-learning-app-rg \
  --settings \
    ENVIRONMENT=production \
    TEST_MODE=0 \
    ANTHROPIC_API_KEY="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/ANTHROPIC-API-KEY/)" \
    REDIS_HOST="poker-cache-prod.redis.cache.windows.net" \
    REDIS_PORT=6380 \
    REDIS_PASSWORD="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/REDIS-PASSWORD/)" \
    DATABASE_URL="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/DATABASE-URL/)" \
    AUTH0_DOMAIN="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/AUTH0-DOMAIN/)" \
    AUTH0_CLIENT_ID="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/AUTH0-CLIENT-ID/)" \
    AUTH0_CLIENT_SECRET="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/AUTH0-CLIENT-SECRET/)" \
    AUTH0_API_AUDIENCE="@Microsoft.KeyVault(SecretUri=https://poker-kv-prod.vault.azure.net/secrets/AUTH0-API-AUDIENCE/)" \
    PYTHONUNBUFFERED=1 \
    SCM_DO_BUILD_DURING_DEPLOYMENT=true \
    WEBSITES_PORT=8000
```

---

### Phase 3: Frontend Deployment Setup (45 minutes)

#### 3.2 Configure Frontend Environment Variables (Updated)

```bash
# Production frontend (UPDATED with Auth0)
az webapp config appsettings set \
  --name poker-web-prod \
  --resource-group poker-learning-app-rg \
  --settings \
    NEXT_PUBLIC_API_URL="https://poker-api-prod.azurewebsites.net" \
    NEXT_PUBLIC_ENVIRONMENT="production" \
    NEXT_PUBLIC_AUTH0_DOMAIN="poker-app.us.auth0.com" \
    NEXT_PUBLIC_AUTH0_CLIENT_ID="<auth0-client-id-for-frontend>" \
    NEXT_PUBLIC_AUTH0_AUDIENCE="https://api.poker.app" \
    NODE_ENV=production \
    PORT=8080
```

---

### Phase 4: CI/CD Pipeline Setup (90 minutes)

(Add Auth0 callback URLs to GitHub Actions)

#### 4.3 Configure GitHub Secrets (Updated)

```
# Existing secrets (unchanged)
AZURE_CREDENTIALS
AZURE_WEBAPP_NAME_BACKEND_STAGING
AZURE_WEBAPP_NAME_BACKEND_PROD
...

# NEW: Auth0 secrets
AUTH0_DOMAIN_STAGING: poker-app-staging.us.auth0.com
AUTH0_CLIENT_ID_STAGING: <staging-client-id>
AUTH0_CLIENT_SECRET_STAGING: <staging-client-secret>
AUTH0_DOMAIN_PROD: poker-app.us.auth0.com
AUTH0_CLIENT_ID_PROD: <prod-client-id>
AUTH0_CLIENT_SECRET_PROD: <prod-client-secret>
```

---

### Phase 5: Monitoring & Alerts Setup (60 minutes)

(Add user-specific alerts)

```bash
# NEW: Alert for high authentication failures
az monitor metrics alert create \
  --name "High Auth Failures" \
  --resource-group poker-learning-app-rg \
  --scopes $BACKEND_ID \
  --condition "avg Http401 > 20" \
  --window-size 5m \
  --evaluation-frequency 1m \
  --severity 2 \
  --description "High rate of 401 authentication failures" \
  --action $ACTION_GROUP_ID
```

---

## Security Configuration

(All previous sections PLUS additional auth security)

### User Data Protection

**GDPR Compliance**:
```python
# backend/main.py
@app.delete("/users/me")
async def delete_user_account(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GDPR: Right to be forgotten"""
    user_id = current_user["user_id"]

    # Delete user data (CASCADE deletes related records)
    db.query(User).filter(User.user_id == user_id).delete()
    db.commit()

    # Also delete from Auth0
    # ... use Auth0 Management API

    return {"message": "Account deleted successfully"}

@app.get("/users/me/data")
async def export_user_data(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """GDPR: Right to data portability"""
    user_id = current_user["user_id"]

    # Export all user data as JSON
    user = db.query(User).filter(User.user_id == user_id).first()
    games = db.query(Game).filter(Game.user_id == user_id).all()
    hands = db.query(Hand).filter(Hand.user_id == user_id).all()

    return {
        "user": user.to_dict(),
        "games": [g.to_dict() for g in games],
        "hands": [h.to_dict() for h in hands]
    }
```

---

## Cost Analysis

### Monthly Cost Breakdown (UPDATED)

#### Staging Environment

| Service | Tier | Specs | Monthly Cost |
|---------|------|-------|--------------|
| App Service Plan B1 | Shared (backend + frontend) | 1 vCore, 1.75GB RAM | $13.14 |
| Redis Cache Basic C0 | No HA | 250 MB | $16.79 |
| PostgreSQL B1ms | Burstable | 1 vCore, 2 GB RAM | $13.63 |
| Key Vault Standard | - | - | ~$3 |
| Application Insights | 1 GB/mo | 30-day retention | Free tier |
| **Auth0 Free Tier** | **NEW** | **7,000 MAU** | **$0** |
| **Staging Total** | | | **$46.56/mo** |

#### Production Environment

| Service | Tier | Specs | Monthly Cost |
|---------|------|-------|--------------|
| App Service Plan B2 (backend) | Dedicated | 2 vCore, 3.5GB RAM | $26.06 |
| App Service Plan B1 (frontend) | Dedicated | 1 vCore, 1.75GB RAM | $13.14 |
| Redis Cache Standard C1 | HA, 99.9% SLA | 1 GB | $61.68 |
| PostgreSQL B1ms | Burstable | 1 vCore, 2GB RAM | $13.63 |
| Key Vault Standard | - | - | ~$5 |
| Application Insights | ~2 GB/mo | 30-day retention | ~$5 |
| **Auth0 Free Tier** | **NEW** | **7,000 MAU, unlimited logins** | **$0** |
| **Production Total** | | | **$124.51/mo** |

**Auth0 Pricing Notes**:
- Free tier: 7,000 monthly active users (MAU)
- Essentials tier: $23/month for 1,000 MAU, then $4/100 MAU
- Upgrade trigger: If you exceed 7,000 active users/month
- Social connections: Included in free tier (Google, GitHub, etc.)
- Passwordless: Included in free tier

#### Combined Total

**Staging + Production**: **$171.07/month** (no change, Auth0 is free tier)

**When Auth0 costs kick in**:
- At 7,001+ monthly active users → $23/month (Essentials tier)
- At 10,000 MAU → $59/month ($23 base + $36 for extra 9,000 users)
- At 50,000 MAU → $1,623/month (Professional tier recommended)

**Benefit**: At scale, Auth0 cost is negligible compared to revenue potential:
- 10,000 MAU = $59/month Auth0 cost
- If 10% convert to paid ($10/month) = 1,000 users × $10 = $10,000/month revenue
- Auth0 is 0.59% of revenue

---

### Cost Savings from User Accounts

**Analysis Caching ROI**:
```
Without caching:
- User analyzes same hand 3 times (reviewing strategy)
- Cost: 3 × $0.016 (Haiku) = $0.048 per hand
- 100 users × 10 hands/day × 3 re-analyses = 3,000 API calls
- Monthly cost: 3,000 calls × $0.016 × 30 days = $1,440/month

With caching:
- First analysis: $0.016 (stored in database)
- Subsequent views: $0 (from cache)
- Monthly cost: 1,000 unique analyses × $0.016 × 30 days = $480/month

Savings: $960/month ($11,520/year)
```

**Storage cost**: $13.63/month PostgreSQL
**Net savings**: $946.37/month

---

## Monitoring & Operations

(Add user analytics queries)

### Custom KQL Queries (UPDATED)

```kql
// User authentication events
customEvents
| where name in ("user_login", "user_logout", "auth_failure")
| summarize count() by name, bin(timestamp, 1h)
| render timechart

// Daily/Monthly Active Users (DAU/MAU)
customEvents
| where name == "user_login"
| extend user_id = tostring(customDimensions.user_id)
| summarize dcount(user_id) by bin(timestamp, 1d)
| render timechart

// User engagement (session duration)
customEvents
| where name == "game_completed"
| extend user_id = tostring(customDimensions.user_id),
         duration = toint(customDimensions.session_duration)
| summarize avg(duration), percentile(duration, 50), percentile(duration, 95) by bin(timestamp, 1d)

// Analysis cache hit rate
customEvents
| where name in ("analysis_requested", "analysis_cache_hit")
| summarize
    total_requests = countif(name == "analysis_requested"),
    cache_hits = countif(name == "analysis_cache_hit"),
    cache_hit_rate = (countif(name == "analysis_cache_hit") * 100.0) / count()
| project cache_hit_rate, total_requests, cache_hits

// Anthropic API cost per user
customEvents
| where name == "analysis_requested"
| extend user_id = tostring(customDimensions.user_id),
         cost = toreal(customDimensions.cost)
| summarize total_cost = sum(cost), analyses = count() by user_id
| order by total_cost desc
| take 20

// Top users by activity
customEvents
| where name in ("game_created", "hand_played", "analysis_requested")
| extend user_id = tostring(customDimensions.user_id)
| summarize
    games = countif(name == "game_created"),
    hands = countif(name == "hand_played"),
    analyses = countif(name == "analysis_requested")
by user_id
| order by hands desc
| take 20

// User retention (7-day, 30-day)
let first_activity = customEvents
| extend user_id = tostring(customDimensions.user_id)
| summarize first_seen = min(timestamp) by user_id;
customEvents
| extend user_id = tostring(customDimensions.user_id)
| join kind=inner first_activity on user_id
| where timestamp between (first_seen .. datetime_add('day', 7, first_seen))
| summarize dcount(user_id) by cohort = bin(first_seen, 1d)
| order by cohort asc
```

---

## Rollback & Disaster Recovery

(Add user data backup/restore procedures)

### User Data Backups

**PostgreSQL User Data**:
```bash
# Manual backup of user tables
pg_dump -h poker-db-prod.postgres.database.azure.com \
  -U pokeradmin \
  -d pokerapp \
  -t users -t user_stats -t games -t hands -t actions -t analysis_cache \
  > user_data_backup_$(date +%Y%m%d).sql

# Restore from backup
psql -h poker-db-prod.postgres.database.azure.com \
  -U pokeradmin \
  -d pokerapp \
  < user_data_backup_20260112.sql
```

**Auth0 User Export**:
```bash
# Export users from Auth0 (via Management API)
# Visit Auth0 Dashboard → User Management → Import/Export
# Or use Auth0 Management API:
curl -X POST "https://poker-app.us.auth0.com/api/v2/jobs/users-exports" \
  -H "Authorization: Bearer <management-api-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "connection_id": "<connection-id>",
    "format": "json"
  }'
```

---

## Deployment Checklist

### Pre-Deployment (5-7 days, was 3-4 days)

#### Auth0 Setup (NEW)
- [ ] Auth0 account created (dev, staging, production tenants)
- [ ] Applications created (3 SPAs: dev, staging, prod)
- [ ] APIs created (3 APIs: dev, staging, prod)
- [ ] Callback URLs configured
- [ ] Connections enabled (Email passwordless, Google, GitHub)
- [ ] Branding customized (logo, colors)
- [ ] Test tenants working locally

#### Code Changes (UPDATED)
- [ ] Backend JWT validation implemented
- [ ] Backend endpoints require authentication
- [ ] User tables added to PostgreSQL schema
- [ ] Database migrations created and tested
- [ ] Redis session store implemented
- [ ] Frontend Auth0 SDK integrated
- [ ] Login/logout UI created
- [ ] User dashboard page created
- [ ] Game history page created
- [ ] Analysis caching by user implemented
- [ ] Startup command updated (gunicorn)
- [ ] CORS configuration environment-specific
- [ ] Rate limiting implemented (per user)
- [ ] Security headers added
- [ ] Application Insights user tracking added
- [ ] All tests passing with authentication

#### Local Testing (UPDATED)
- [ ] Auth0 login flow works locally
- [ ] JWT validation works
- [ ] Backend creates user on first login
- [ ] Games linked to users
- [ ] User dashboard shows stats
- [ ] Game history displays correctly
- [ ] Analysis caching prevents duplicate API calls
- [ ] WebSocket connections authenticated
- [ ] Database migrations apply successfully
- [ ] Integration tests pass with auth

---

### Azure Setup (Phase 1-5: ~5 hours, was 4 hours)

(All previous checklist items PLUS Auth0 configuration)

#### Phase 2: Backend Infrastructure (UPDATED)
- [ ] Auth0 secrets added to Key Vault (domain, client ID, client secret, audience)
- [ ] App Service environment variables include Auth0 config
- [ ] JWT validation tested in staging

#### Phase 3: Frontend Infrastructure (UPDATED)
- [ ] Frontend environment variables include Auth0 config (public)
- [ ] Auth0 callback URLs updated with actual Azure URLs

---

### Post-Deployment Validation (1-2 hours)

#### Auth Flow Tests (NEW)
- [ ] Login with email magic link works
- [ ] Login with Google OAuth works
- [ ] Login with GitHub OAuth works
- [ ] JWT token received and stored
- [ ] Authenticated API requests work
- [ ] Logout clears session
- [ ] Token refresh works (automatic)
- [ ] Expired token handled gracefully (re-login)

#### User Feature Tests (NEW)
- [ ] User dashboard loads with stats
- [ ] Game history shows past games
- [ ] "Resume game" works (loads from database)
- [ ] Analysis caching works (no re-analysis cost)
- [ ] Multi-device: Login on phone, continue on desktop
- [ ] User settings persist across sessions

#### Security Validation (UPDATED)
- [ ] Unauthenticated API requests rejected (401)
- [ ] User can only access their own games (403 for others)
- [ ] JWT signature validation works
- [ ] Expired JWTs rejected
- [ ] Rate limiting per user works
- [ ] CORS only allows configured origins

#### Performance Tests (UPDATED)
- [ ] Load test with 10 authenticated users
- [ ] JWT validation latency < 50ms
- [ ] Database queries optimized (user_id indexes)
- [ ] Analysis cache hit rate > 70% (after 1 hour)

---

## Summary

This deployment plan provides a production-ready Azure architecture for the Poker Learning App with **comprehensive user authentication** and account management:

✅ **User Accounts**: Auth0 integration with OAuth + passwordless
✅ **User Features**: Dashboard, game history, stats tracking, analysis caching
✅ **Scalability**: Redis + PostgreSQL enable horizontal scaling
✅ **Cost Savings**: Analysis caching saves $960+/month in API costs
✅ **Reliability**: High availability Redis, automatic backups
✅ **Security**: Auth0 JWT validation, Key Vault, managed identity, rate limiting per user
✅ **Monitoring**: User analytics, engagement metrics, retention tracking
✅ **Cost-Effective**: $171/month total (Auth0 free tier for <7K users)
✅ **CI/CD**: Automated GitHub Actions deployments
✅ **User Privacy**: GDPR compliance (data export, account deletion)

**Estimated Total Effort**: **1.5-2 weeks** (5-7 days pre-deployment + 1 day Azure setup + 1-2 days testing)

**User Value Proposition**:
- ❌ Without accounts: "Practice poker, forget everything"
- ✅ With accounts: "Track progress, review history, improve over time, access from anywhere"

**Next Steps**: Complete pre-deployment requirements (auth + database), then execute Phase 1-5 in sequence.

---

**Document Version**: 3.0 (User Authentication Added)
**Last Updated**: 2026-01-12
**Review Status**: ✅ Updated with Auth0 Integration
**Changes**: Added user authentication, user accounts, game history, analysis caching, user dashboard, updated database schema, updated costs, updated timeline (+2-3 days)
