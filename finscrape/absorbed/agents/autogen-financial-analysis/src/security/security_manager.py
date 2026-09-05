"""
Security Manager
Comprehensive security management system for the AutoGen financial platform
"""

import hashlib
import hmac
import secrets
import jwt
import bcrypt
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import logging
import asyncio
import re
from ipaddress import ip_address
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
# Note: default_backend is deprecated in newer cryptography versions
import base64
import json
import aiofiles
from concurrent.futures import ThreadPoolExecutor


class SecurityLevel(Enum):
    """Security levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Permission(Enum):
    """System permissions"""
    READ = "read"
    WRITE = "write"
    EXECUTE = "execute"
    DELETE = "delete"
    ADMIN = "admin"


class SecurityEventType(Enum):
    """Security event types"""
    LOGIN_SUCCESS = "login_success"
    LOGIN_FAILURE = "login_failure"
    LOGOUT = "logout"
    PERMISSION_DENIED = "permission_denied"
    SUSPICIOUS_ACTIVITY = "suspicious_activity"
    DATA_ACCESS = "data_access"
    CONFIG_CHANGE = "config_change"
    API_ACCESS = "api_access"
    RATE_LIMIT_EXCEEDED = "rate_limit_exceeded"


@dataclass
class User:
    """User account definition"""
    user_id: str
    username: str
    email: str
    password_hash: str
    salt: str
    roles: List[str]
    permissions: List[Permission]
    is_active: bool = True
    is_verified: bool = False
    failed_login_attempts: int = 0
    last_login: Optional[datetime] = None
    last_password_change: Optional[datetime] = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)
    mfa_enabled: bool = False
    mfa_secret: Optional[str] = None
    api_keys: List[str] = field(default_factory=list)


@dataclass
class Role:
    """Role definition"""
    role_id: str
    name: str
    description: str
    permissions: List[Permission]
    inherits_from: List[str] = field(default_factory=list)
    is_active: bool = True


@dataclass
class SecurityPolicy:
    """Security policy definition"""
    name: str
    description: str
    password_min_length: int = 8
    password_require_uppercase: bool = True
    password_require_lowercase: bool = True
    password_require_numbers: bool = True
    password_require_special: bool = True
    password_expiry_days: int = 90
    max_login_attempts: int = 5
    session_timeout_minutes: int = 30
    mfa_required: bool = False
    api_rate_limit: int = 100
    ip_whitelist: List[str] = field(default_factory=list)
    ip_blacklist: List[str] = field(default_factory=list)


@dataclass
class SecurityEvent:
    """Security event log"""
    event_id: str
    event_type: SecurityEventType
    user_id: Optional[str]
    ip_address: str
    user_agent: str
    timestamp: datetime
    description: str
    severity: SecurityLevel
    metadata: Dict[str, Any] = field(default_factory=dict)
    is_resolved: bool = False


@dataclass
class APIKey:
    """API key definition"""
    key_id: str
    user_id: str
    key_hash: str
    permissions: List[Permission]
    rate_limit: int
    expires_at: Optional[datetime]
    last_used: Optional[datetime]
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)


class SecurityManager:
    """Comprehensive security management system"""

    def __init__(self, config: Dict[str, Any] = None):
        self.logger = logging.getLogger(__name__)
        self.config = config or {}
        self.users: Dict[str, User] = {}
        self.roles: Dict[str, Role] = {}
        self.api_keys: Dict[str, APIKey] = {}
        self.security_events: List[SecurityEvent] = []
        self.session_tokens: Dict[str, Dict[str, Any]] = {}
        self.rate_limits: Dict[str, List[datetime]] = {}
        self.failed_attempts: Dict[str, List[datetime]] = {}

        # Cryptography setup
        self.encryption_key = self._setup_encryption()
        self.jwt_secret = self.config.get('jwt_secret', secrets.token_urlsafe(32))

        # Security policies
        self.security_policies = self._initialize_security_policies()

        # Background tasks
        self.cleanup_task = None
        self.thread_pool = ThreadPoolExecutor(max_workers=4)

        # Initialize
        self._initialize_roles()
        self._start_background_tasks()

    def _setup_encryption(self) -> bytes:
        """Setup encryption key"""
        key_file = self.config.get('encryption_key_file', 'encryption_key.key')

        try:
            # Try to load existing key
            with open(key_file, 'rb') as f:
                key = f.read()
                if len(key) == 32:  # Fernet key is 32 bytes
                    return key
        except FileNotFoundError:
            pass

        # Generate new key
        key = Fernet.generate_key()
        with open(key_file, 'wb') as f:
            f.write(key)

        # Set restrictive permissions
        import os
        os.chmod(key_file, 0o600)

        return key

    def _initialize_security_policies(self) -> Dict[str, SecurityPolicy]:
        """Initialize security policies"""
        policies = {}

        # Default policy
        policies['default'] = SecurityPolicy(
            name="default",
            description="Default security policy",
            password_min_length=8,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_numbers=True,
            password_require_special=True,
            password_expiry_days=90,
            max_login_attempts=5,
            session_timeout_minutes=30,
            mfa_required=False,
            api_rate_limit=100
        )

        # High security policy
        policies['high_security'] = SecurityPolicy(
            name="high_security",
            description="High security policy",
            password_min_length=12,
            password_require_uppercase=True,
            password_require_lowercase=True,
            password_require_numbers=True,
            password_require_special=True,
            password_expiry_days=60,
            max_login_attempts=3,
            session_timeout_minutes=15,
            mfa_required=True,
            api_rate_limit=50
        )

        return policies

    def _initialize_roles(self):
        """Initialize default roles"""
        # Admin role
        self.roles['admin'] = Role(
            role_id='admin',
            name='Administrator',
            description='Full system access',
            permissions=list(Permission)
        )

        # Analyst role
        self.roles['analyst'] = Role(
            role_id='analyst',
            name='Financial Analyst',
            description='Financial analysis access',
            permissions=[Permission.READ, Permission.WRITE, Permission.EXECUTE]
        )

        # Viewer role
        self.roles['viewer'] = Role(
            role_id='viewer',
            name='Viewer',
            description='Read-only access',
            permissions=[Permission.READ]
        )

    def _start_background_tasks(self):
        """Start background security tasks"""
        self.cleanup_task = asyncio.create_task(self._cleanup_expired_sessions())

    async def _cleanup_expired_sessions(self):
        """Clean up expired sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []

                for token, session_data in self.session_tokens.items():
                    session_time = datetime.fromisoformat(session_data['created_at'])
                    timeout_minutes = self.security_policies['default'].session_timeout_minutes

                    if current_time - session_time > timedelta(minutes=timeout_minutes):
                        expired_sessions.append(token)

                # Remove expired sessions
                for token in expired_sessions:
                    del self.session_tokens[token]

                # Clean up rate limits
                for ip_key, timestamps in self.rate_limits.items():
                    self.rate_limits[ip_key] = [
                        ts for ts in timestamps
                        if current_time - ts < timedelta(hours=1)
                    ]

                # Clean up failed attempts
                for user_id, attempts in self.failed_attempts.items():
                    self.failed_attempts[user_id] = [
                        ts for ts in attempts
                        if current_time - ts < timedelta(minutes=15)
                    ]

                await asyncio.sleep(300)  # Run every 5 minutes

            except Exception as e:
                self.logger.error(f"Error in session cleanup: {str(e)}")
                await asyncio.sleep(60)

    def hash_password(self, password: str) -> Tuple[str, str]:
        """Hash password with salt"""
        salt = bcrypt.gensalt()
        password_hash = bcrypt.hashpw(password.encode('utf-8'), salt)
        return password_hash.decode('utf-8'), salt.decode('utf-8')

    def verify_password(self, password: str, password_hash: str, salt: str) -> bool:
        """Verify password against hash"""
        try:
            salt_bytes = salt.encode('utf-8')
            hash_bytes = password_hash.encode('utf-8')
            password_bytes = password.encode('utf-8')

            return bcrypt.checkpw(password_bytes, hash_bytes)
        except Exception as e:
            self.logger.error(f"Password verification error: {str(e)}")
            return False

    def validate_password_strength(self, password: str, policy: SecurityPolicy = None) -> List[str]:
        """Validate password strength against policy"""
        if policy is None:
            policy = self.security_policies['default']

        errors = []

        # Check length
        if len(password) < policy.password_min_length:
            errors.append(f"Password must be at least {policy.password_min_length} characters long")

        # Check uppercase
        if policy.password_require_uppercase and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")

        # Check lowercase
        if policy.password_require_lowercase and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")

        # Check numbers
        if policy.password_require_numbers and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")

        # Check special characters
        if policy.password_require_special and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")

        return errors

    def create_user(self, username: str, email: str, password: str,
                   roles: List[str] = None) -> Optional[User]:
        """Create new user account"""
        try:
            # Validate password strength
            password_errors = self.validate_password_strength(password)
            if password_errors:
                raise ValueError(f"Password validation failed: {', '.join(password_errors)}")

            # Check if user already exists
            if any(user.username == username for user in self.users.values()):
                raise ValueError("Username already exists")

            if any(user.email == email for user in self.users.values()):
                raise ValueError("Email already exists")

            # Hash password
            password_hash, salt = self.hash_password(password)

            # Create user
            user_id = secrets.token_urlsafe(16)
            user = User(
                user_id=user_id,
                username=username,
                email=email,
                password_hash=password_hash,
                salt=salt,
                roles=roles or ['viewer'],
                permissions=self._get_permissions_for_roles(roles or ['viewer'])
            )

            self.users[user_id] = user

            # Log security event
            self.log_security_event(
                SecurityEventType.SUSPICIOUS_ACTIVITY,
                user_id=user_id,
                ip_address="system",
                user_agent="system",
                description=f"User account created: {username}",
                severity=SecurityLevel.INFO,
                metadata={'username': username}
            )

            return user

        except Exception as e:
            self.logger.error(f"Error creating user: {str(e)}")
            return None

    def authenticate_user(self, username: str, password: str,
                         ip_address: str, user_agent: str) -> Optional[str]:
        """Authenticate user and return session token"""
        try:
            # Find user by username
            user = next((u for u in self.users.values() if u.username == username), None)
            if not user:
                self.log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description=f"Login attempt with unknown username: {username}",
                    severity=SecurityLevel.MEDIUM
                )
                return None

            # Check if account is locked
            if self._is_account_locked(user):
                self.log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="Login attempt on locked account",
                    severity=SecurityLevel.HIGH
                )
                return None

            # Verify password
            if not self.verify_password(password, user.password_hash, user.salt):
                self._record_failed_login(user.user_id, ip_address, user_agent)
                return None

            # Check if account is active
            if not user.is_active:
                self.log_security_event(
                    SecurityEventType.LOGIN_FAILURE,
                    user_id=user.user_id,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    description="Login attempt on inactive account",
                    severity=SecurityLevel.MEDIUM
                )
                return None

            # Generate session token
            session_token = self._generate_session_token(user)

            # Update user info
            user.last_login = datetime.now()
            user.failed_login_attempts = 0
            self._remove_failed_attempts(user.user_id)

            # Log successful login
            self.log_security_event(
                SecurityEventType.LOGIN_SUCCESS,
                user_id=user.user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                description="User logged in successfully",
                severity=SecurityLevel.INFO
            )

            return session_token

        except Exception as e:
            self.logger.error(f"Error authenticating user: {str(e)}")
            return None

    def _generate_session_token(self, user: User) -> str:
        """Generate JWT session token"""
        payload = {
            'user_id': user.user_id,
            'username': user.username,
            'roles': user.roles,
            'permissions': [p.value for p in user.permissions],
            'created_at': datetime.now().isoformat(),
            'expires_at': (datetime.now() + timedelta(hours=1)).isoformat()
        }

        token = jwt.encode(payload, self.jwt_secret, algorithm='HS256')
        return token

    def verify_session_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode session token"""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=['HS256'])

            # Check expiration
            expires_at = datetime.fromisoformat(payload['expires_at'])
            if datetime.now() > expires_at:
                return None

            # Check if session is still active
            if token not in self.session_tokens:
                return None

            return payload

        except jwt.ExpiredSignatureError:
            self.logger.warning("Expired session token used")
            return None
        except jwt.InvalidTokenError:
            self.logger.warning("Invalid session token used")
            return None
        except Exception as e:
            self.logger.error(f"Error verifying session token: {str(e)}")
            return None

    def create_api_key(self, user_id: str, permissions: List[Permission] = None,
                      expires_in_days: int = None) -> Optional[APIKey]:
        """Create API key for user"""
        try:
            user = self.users.get(user_id)
            if not user:
                return None

            # Generate API key
            api_key = f"ak_{secrets.token_urlsafe(32)}"
            key_id = secrets.token_urlsafe(16)

            # Hash the API key for storage
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            api_key_obj = APIKey(
                key_id=key_id,
                user_id=user_id,
                key_hash=key_hash,
                permissions=permissions or user.permissions,
                rate_limit=self.security_policies['default'].api_rate_limit,
                expires_at=(datetime.now() + timedelta(days=expires_in_days)) if expires_in_days else None
            )

            self.api_keys[key_id] = api_key_obj
            user.api_keys.append(key_id)

            # Log event
            self.log_security_event(
                SecurityEventType.API_ACCESS,
                user_id=user_id,
                ip_address="system",
                user_agent="system",
                description=f"API key created: {key_id}",
                severity=SecurityLevel.INFO
            )

            # Return only the API key (this is the only time it's shown)
            return api_key_obj

        except Exception as e:
            self.logger.error(f"Error creating API key: {str(e)}")
            return None

    def verify_api_key(self, api_key: str) -> Optional[APIKey]:
        """Verify API key and return API key object"""
        try:
            key_hash = hashlib.sha256(api_key.encode()).hexdigest()

            for api_key_obj in self.api_keys.values():
                if api_key_obj.key_hash == key_hash and api_key_obj.is_active:
                    # Check expiration
                    if api_key_obj.expires_at and datetime.now() > api_key_obj.expires_at:
                        api_key_obj.is_active = False
                        return None

                    # Update last used
                    api_key_obj.last_used = datetime.now()
                    return api_key_obj

            return None

        except Exception as e:
            self.logger.error(f"Error verifying API key: {str(e)}")
            return None

    def check_rate_limit(self, identifier: str, limit: int = 100,
                        window_minutes: int = 60) -> bool:
        """Check rate limit for identifier"""
        current_time = datetime.now()

        if identifier not in self.rate_limits:
            self.rate_limits[identifier] = []

        # Clean old requests
        self.rate_limits[identifier] = [
            ts for ts in self.rate_limits[identifier]
            if current_time - ts < timedelta(minutes=window_minutes)
        ]

        # Check limit
        if len(self.rate_limits[identifier]) >= limit:
            self.log_security_event(
                SecurityEventType.RATE_LIMIT_EXCEEDED,
                ip_address=identifier,
                user_agent="unknown",
                description=f"Rate limit exceeded for {identifier}",
                severity=SecurityLevel.MEDIUM
            )
            return False

        # Record request
        self.rate_limits[identifier].append(current_time)
        return True

    def check_permission(self, user_id: str, permission: Permission) -> bool:
        """Check if user has permission"""
        user = self.users.get(user_id)
        if not user:
            return False

        return permission in user.permissions

    def log_security_event(self, event_type: SecurityEventType,
                         user_id: Optional[str] = None,
                         ip_address: str = "unknown",
                         user_agent: str = "unknown",
                         description: str = "",
                         severity: SecurityLevel = SecurityLevel.INFO,
                         metadata: Dict[str, Any] = None):
        """Log security event"""
        try:
            event = SecurityEvent(
                event_id=secrets.token_urlsafe(16),
                event_type=event_type,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                timestamp=datetime.now(),
                description=description,
                severity=severity,
                metadata=metadata or {}
            )

            self.security_events.append(event)

            # Keep only recent events
            if len(self.security_events) > 10000:
                self.security_events = self.security_events[-5000:]

            # Log to regular logger as well
            self.logger.warning(f"Security Event: {event_type.value} - {description}")

        except Exception as e:
            self.logger.error(f"Error logging security event: {str(e)}")

    def _is_account_locked(self, user: User) -> bool:
        """Check if user account is locked due to failed attempts"""
        policy = self.security_policies['default']
        if user.failed_login_attempts >= policy.max_login_attempts:
            # Check if lockout period has expired
            recent_failures = self.failed_attempts.get(user.user_id, [])
            if recent_failures:
                last_failure = max(recent_failures)
                if datetime.now() - last_failure < timedelta(minutes=15):
                    return True

        return False

    def _record_failed_login(self, user_id: str, ip_address: str, user_agent: str):
        """Record failed login attempt"""
        user = self.users.get(user_id)
        if user:
            user.failed_login_attempts += 1

            # Record failed attempt
            if user_id not in self.failed_attempts:
                self.failed_attempts[user_id] = []

            self.failed_attempts[user_id].append(datetime.now())

            # Log security event
            self.log_security_event(
                SecurityEventType.LOGIN_FAILURE,
                user_id=user_id,
                ip_address=ip_address,
                user_agent=user_agent,
                description=f"Failed login attempt ({user.failed_login_attempts}/{self.security_policies['default'].max_login_attempts})",
                severity=SecurityLevel.MEDIUM
            )

    def _remove_failed_attempts(self, user_id: str):
        """Remove failed login attempts for user"""
        if user_id in self.failed_attempts:
            del self.failed_attempts[user_id]

    def _get_permissions_for_roles(self, roles: List[str]) -> List[Permission]:
        """Get permissions for roles"""
        permissions = []

        for role_name in roles:
            role = self.roles.get(role_name)
            if role:
                permissions.extend(role.permissions)

                # Check inherited roles
                for inherited_role in role.inherits_from:
                    inherited = self.roles.get(inherited_role)
                    if inherited:
                        permissions.extend(inherited.permissions)

        # Remove duplicates while preserving order
        seen = set()
        unique_permissions = []
        for permission in permissions:
            if permission not in seen:
                seen.add(permission)
                unique_permissions.append(permission)

        return unique_permissions

    def encrypt_data(self, data: Union[str, bytes]) -> str:
        """Encrypt sensitive data"""
        try:
            if isinstance(data, str):
                data = data.encode('utf-8')

            f = Fernet(self.encryption_key)
            encrypted_data = f.encrypt(data)
            return base64.b64encode(encrypted_data).decode('utf-8')

        except Exception as e:
            self.logger.error(f"Error encrypting data: {str(e)}")
            raise

    def decrypt_data(self, encrypted_data: str) -> str:
        """Decrypt sensitive data"""
        try:
            encrypted_bytes = base64.b64decode(encrypted_data.encode('utf-8'))
            f = Fernet(self.encryption_key)
            decrypted_data = f.decrypt(encrypted_bytes)
            return decrypted_data.decode('utf-8')

        except Exception as e:
            self.logger.error(f"Error decrypting data: {str(e)}")
            raise

    def validate_ip_address(self, ip_address: str, policy: SecurityPolicy = None) -> bool:
        """Validate IP address against whitelist/blacklist"""
        if policy is None:
            policy = self.security_policies['default']

        try:
            ip = ip_address(ip_address)

            # Check blacklist first
            for blacklisted_ip in policy.ip_blacklist:
                if ip_address == blacklisted_ip:
                    return False

            # If whitelist is not empty, IP must be in whitelist
            if policy.ip_whitelist:
                return ip_address in policy.ip_whitelist

            return True

        except ValueError:
            self.logger.warning(f"Invalid IP address: {ip_address}")
            return False

    def get_security_stats(self) -> Dict[str, Any]:
        """Get security statistics"""
        current_time = datetime.now()

        # Count recent events by type
        recent_events = [e for e in self.security_events
                        if current_time - e.timestamp < timedelta(hours=24)]

        event_counts = {}
        for event in recent_events:
            event_counts[event.event_type.value] = event_counts.get(event.event_type.value, 0) + 1

        # Count active sessions
        active_sessions = len(self.session_tokens)

        # Count failed login attempts
        total_failed_attempts = sum(len(attempts) for attempts in self.failed_attempts.values())

        return {
            'total_users': len(self.users),
            'active_users': len([u for u in self.users.values() if u.is_active]),
            'active_sessions': active_sessions,
            'total_api_keys': len(self.api_keys),
            'active_api_keys': len([k for k in self.api_keys.values() if k.is_active]),
            'recent_security_events': len(recent_events),
            'security_events_by_type': event_counts,
            'failed_login_attempts': total_failed_attempts,
            'locked_accounts': len([u for u in self.users.values() if self._is_account_locked(u)])
        }

    def shutdown(self):
        """Shutdown security manager"""
        if self.cleanup_task:
            self.cleanup_task.cancel()
        self.thread_pool.shutdown(wait=True)


# Global security instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager(config: Dict[str, Any] = None) -> SecurityManager:
    """Get global security manager instance"""
    global _security_manager
    if _security_manager is None:
        _security_manager = SecurityManager(config)
    return _security_manager