import requests
from jose import jwt
from jose.exceptions import JWTError, ExpiredSignatureError, JWTClaimsError
from rest_framework import authentication, exceptions
from django.conf import settings
from .models import Tenant, TenantUser
import logging

logger = logging.getLogger(__name__)

class AuthServiceJWTAuthentication(authentication.BaseAuthentication):
    """Validates JWTs issued by auth.pluggedspace.org."""
    
    def __init__(self):
        self.jwks_url = "https://auth.pluggedspace.org/auth/.well-known/jwks.json"
        self.issuer = "https://auth.pluggedspace.org"
        self.audience = "pluggedspace-api"
        self._jwks = None

    def get_jwks(self):
        """Cache the JWKS to avoid repeated requests"""
        if self._jwks is None:
            try:
                logger.info(f"🔐 Fetching JWKS from: {self.jwks_url}")
                response = requests.get(self.jwks_url, timeout=10)
                logger.info(f"🔐 JWKS response status: {response.status_code}")
                
                if response.status_code == 200:
                    self._jwks = response.json()
                    logger.info(f"✅ JWKS loaded successfully with {len(self._jwks.get('keys', []))} keys")
                else:
                    logger.warning(f"❌ Failed to fetch JWKS: {response.status_code} - {response.text}")
                    # Fallback to your known keys for development
                    self._jwks = {
                        "keys": [
                            {
                                "kty": "RSA",
                                "kid": "dev-key-1",
                                "use": "sig",
                                "alg": "RS256",
                                "n": "2ZO0Dsx83ItZFb_VsE7rN5UVOF6ZlOGpVl4fAuQn5WzGty8KoQoPZqf9Om7q3QRz5_fk8jw_EfngVRCOGolmcmKKy4bkT_6jyE-Nh_4M8RzPAy7w_43tK4gFKz8n_mbkRgjN3Q-JWMhL6SA_FIFKrWQWdrHhQLnEc1_ZbKT1fy7NqCLOhR82-HR9XjOqTByCvgLi63avL1K8MxH3uUvG37N3m3uZdVhbZFS3y6WVbSfjncpCK6oGJoJpt0M8I0qPy7s08g8UKiWa6hqaVCuRaF0M1LgifzjLEV8u-R00PHHmhSZ-T-_gSxnKm0BpBe815PxU-aq4J7dDlcMnvvuUuw",
                                "e": "AQAB"
                            }
                        ]
                    }
                    logger.info("🔄 Using fallback JWKS for development")
                    
            except requests.RequestException as e:
                logger.error(f"❌ JWKS request error: {e}")
                # Fallback keys for development
                self._jwks = {
                    "keys": [
                        {
                            "kty": "RSA",
                            "kid": "dev-key-1",
                            "use": "sig",
                            "alg": "RS256",
                            "n": "2ZO0Dsx83ItZFb_VsE7rN5UVOF6ZlOGpVl4fAuQn5WzGty8KoQoPZqf9Om7q3QRz5_fk8jw_EfngVRCOGolmcmKKy4bkT_6jyE-Nh_4M8RzPAy7w_43tK4gFKz8n_mbkRgjN3Q-JWMhL6SA_FIFKrWQWdrHhQLnEc1_ZbKT1fy7NqCLOhR82-HR9XjOqTByCvgLi63avL1K8MxH3uUvG37N3m3uZdVhbZFS3y6WVbSfjncpCK6oGJoJpt0M8I0qPy7s08g8UKiWa6hqaVCuRaF0M1LgifzjLEV8u-R00PHHmhSZ-T-_gSxnKm0BpBe815PxU-aq4J7dDlcMnvvuUuw",
                            "e": "AQAB"
                        }
                    ]
                }
                logger.info("🔄 Using fallback JWKS due to request error")
        
        return self._jwks

    def authenticate(self, request):
        auth_header = request.headers.get("Authorization")
        logger.info(f"🔐 Auth header present: {auth_header is not None}")
        
        if not auth_header or not auth_header.startswith("Bearer "):
            logger.warning("❌ No Bearer token found in header")
            return None

        token = auth_header.split("Bearer ")[1].strip()
        
        if not token or len(token) < 10:
            logger.warning("❌ Invalid token format - too short")
            return None

        logger.info(f"🔐 JWT Token received (first 50 chars): {token[:50]}...")

        try:
            # Get JWKS
            jwks = self.get_jwks()
            logger.info(f"🔐 JWKS keys available: {[k.get('kid') for k in jwks['keys']]}")
            
            # Decode header to get kid
            unverified_header = jwt.get_unverified_header(token)
            logger.info(f"🔐 JWT Header: {unverified_header}")
            
            kid = unverified_header.get("kid")
            if not kid:
                logger.warning("❌ No kid in token header")
                return None
                
            # Find the correct key
            key = next(
                (k for k in jwks["keys"] if k["kid"] == kid),
                None
            )
            if not key:
                logger.warning(f"❌ Key not found for kid: {kid}. Available kids: {[k.get('kid') for k in jwks['keys']]}")
                return None

            logger.info(f"✅ Found key for kid: {kid}")

            # Decode and verify the token
            logger.info(f"🔐 Verifying JWT with issuer: {self.issuer}, audience: {self.audience}")
            payload = jwt.decode(
                token,
                key,
                algorithms=["RS256"],
                audience=self.audience,
                issuer=self.issuer,
                options={"verify_aud": True, "verify_iss": True, "verify_exp": True}
            )

            logger.info(f"✅ JWT Payload validated successfully")
            logger.info(f"🔐 JWT Payload: {payload}")

            # Extract user information
            user_id = payload.get("sub")
            email = payload.get("email")
            tenant_id = payload.get("tenant")
            
            logger.info(f"🔐 Extracted - User ID: {user_id}, Email: {email}, Tenant ID: {tenant_id}")
            
            if not user_id:
                logger.error("❌ No user ID (sub) in token payload")
                return None

            if not tenant_id:
                logger.error("❌ No tenant ID in token payload")
                return None

            # Create or get TenantUser
            try:
                logger.info(f"🔐 Creating/getting TenantUser for tenant: {tenant_id}, user: {user_id}")
                tenant_user = TenantUser.get_or_create_from_jwt(
                    tenant_id=tenant_id,
                    user_id=user_id,
                    email=email,
                    full_name=payload.get('full_name')
                )
                logger.info(f"✅ TenantUser resolved: {tenant_user.id} - {tenant_user.email} @ {tenant_user.tenant.name}")
            except Exception as e:
                logger.error(f"❌ Failed to get or create TenantUser: {e}", exc_info=True)
                # Don't raise AuthenticationFailed here, just return None to try next auth method
                return None

            # Create a comprehensive user object that Django can work with
            class JWTUser:
                def __init__(self, tenant_user, payload):
                    self.tenant_user = tenant_user
                    self.tenant = tenant_user.tenant
                    self.id = tenant_user.user_id
                    self.email = tenant_user.email
                    self.tenant_id = tenant_user.tenant.id
                    self.full_name = tenant_user.full_name
                    self.role = tenant_user.role
                    self.permissions = payload.get('scope', '').split()
                    self.is_authenticated = True
                    self.is_active = True
                    self.username = tenant_user.email
                    self.pk = tenant_user.id
                
                def __str__(self):
                    return f"{self.email} ({self.tenant.name})"
                
                def has_perm(self, perm):
                    if self.role in ['owner', 'admin']:
                        return True
                    if perm == 'read':
                        return True
                    return perm in self.permissions
                
                def has_perms(self, perm_list):
                    return all(self.has_perm(perm) for perm in perm_list)
                
                def get_username(self):
                    return self.username
                
                @property
                def is_staff(self):
                    return self.role in ['owner', 'admin']
                
                @property 
                def is_superuser(self):
                    return self.role == 'owner'

            user = JWTUser(tenant_user, payload)
            
            # Set request attributes
            request.jwt_payload = payload
            request.tenant_id = tenant_id
            request.tenant_user = tenant_user
            request.tenant = tenant_user.tenant
            request.auth_type = 'jwt'
            
            logger.info(f"✅ JWT Authentication SUCCESS: {user.email} (tenant: {tenant_user.tenant.name}, role: {tenant_user.role})")
            
            return (user, None)

        except ExpiredSignatureError:
            logger.warning("❌ JWT token expired")
            raise exceptions.AuthenticationFailed("Token has expired")
        except JWTClaimsError as e:
            logger.warning(f"❌ JWT claims error: {e}")
            raise exceptions.AuthenticationFailed("Invalid token claims")
        except JWTError as e:
            logger.warning(f"❌ JWT validation error: {e}")
            raise exceptions.AuthenticationFailed("Invalid token")
        except Exception as e:
            logger.error(f"❌ Unexpected authentication error: {e}", exc_info=True)
            return None

    def authenticate_header(self, request):
        return 'Bearer realm="api", error="invalid_token", error_description="The access token is invalid or expired"'


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    Authenticate using headers set by Kong (no DB lookup).
    Expected headers:
      - X-Api-Key
      - X-Tenant-Id
      - X-App-Name (optional)
      - X-Permissions (optional)
    """

    def authenticate(self, request):
        api_key = request.headers.get("X-Api-Key")
        tenant_id = request.headers.get("X-Tenant-Id")

        if not api_key or not tenant_id:
            return None

        # Kong handles verification. We just consume the context.
        permissions = (request.headers.get("X-Permissions") or "").split()
        app_name = request.headers.get("X-App-Name", "unknown")

        class APIKeyUser:
            def __init__(self):
                self.id = api_key
                self.tenant_id = tenant_id
                self.email = f"apikey@{tenant_id}"
                self.username = f"apikey-{tenant_id}"
                self.permissions = permissions
                self.app = app_name
                self.is_authenticated = True
                self.is_active = True
                self.is_api_key = True

            def has_perm(self, perm):
                return perm in self.permissions or "admin" in self.permissions

            def has_perms(self, perm_list):
                return all(self.has_perm(p) for p in perm_list)

        user = APIKeyUser()
        request.tenant_id = tenant_id
        request.auth_type = "apikey"

        return (user, None)

    def authenticate_header(self, request):
        return 'ApiKey realm="api"'


class APIKeyOrJWTAuthentication(authentication.BaseAuthentication):
    """
    Try JWT authentication first, then fall back to API key authentication
    """
    
    def __init__(self):
        self.jwt_auth = AuthServiceJWTAuthentication()
        self.api_key_auth = APIKeyAuthentication()

    def authenticate(self, request):
        # Try JWT first
        user_auth = self.jwt_auth.authenticate(request)
        if user_auth is not None:
            return user_auth
        
        # Fall back to API key
        api_key_auth = self.api_key_auth.authenticate(request)
        if api_key_auth is not None:
            return api_key_auth
        
        # Neither worked
        return None

    def authenticate_header(self, request):
        return 'Bearer realm="api"'