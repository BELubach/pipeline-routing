"""
Integration tests for authentication endpoints
"""
import asyncio
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.crud import crud_user
from app.schemas.user import UserCreate


@pytest.fixture
async def auth_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create authenticated user and return authorization headers"""
    from app.crud import crud_user
    from app.schemas.user import UserCreate
    
    # Try to get existing user first
    existing_user = await crud_user.get_user_by_email(db_session, email="test@example.com")
    
    if not existing_user:
        # Create test user
        user_in = UserCreate(
            email="test@example.com",
            password="testpass123",
            role="COMPANY_OWNER"
        )
        
        user = await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
    
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "test@example.com", "password": "testpass123"}
    )
    
    assert response.status_code == 200
    token_data = response.json()
    
    return {"Authorization": f"Bearer {token_data['access_token']}"}


@pytest.fixture
async def superuser_headers(client: AsyncClient, db_session: AsyncSession) -> dict:
    """Create superuser and return authorization headers"""
    from app.crud import crud_user
    from app.schemas.user import UserCreate
    
    # Try to get existing user first
    existing_user = await crud_user.get_user_by_email(db_session, email="admin@example.com")
    
    if not existing_user:
        # Create test superuser
        user_in = UserCreate(
            email="admin@example.com",
            password="adminpass123",
            role="CLUSTER_ADMIN",
            is_superuser=True
        )
        
        user = await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
    
    # Login to get token
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "admin@example.com", "password": "adminpass123"}
    )
    
    assert response.status_code == 200
    token_data = response.json()
    
    return {"Authorization": f"Bearer {token_data['access_token']}"}



@pytest.mark.integration
class TestRegisterEndpoint:
    """Test the /api/v1/auth/register endpoint"""
    
    async def test_register_new_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test registering a new user"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepass123",
                "role": "COMPANY_OWNER"
            }
        )
        
        # Debug output
        if response.status_code != 201:
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.json()}")
        
        assert response.status_code == 201
        data = response.json()
        
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "COMPANY_OWNER"
        assert data["is_active"] is True
        assert "password" not in data
        assert "id" in data
    
    async def test_register_duplicate_email(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that registering with existing email fails"""
        # Create first user
        user_in = UserCreate(
            email="existing@example.com",
            password="pass123",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        # Try to create another user with same email
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "existing@example.com",
                "password": "differentpass",
                "role": "COMPANY_OWNER"
            }
        )
        
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    async def test_register_invalid_email(
        self,
        client: AsyncClient
    ):
        """Test validation for invalid email format"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "notanemail",
                "password": "pass123",
                "role": "COMPANY_OWNER"
            }
        )
        
        assert response.status_code == 422
    
    async def test_register_missing_fields(
        self,
        client: AsyncClient
    ):
        """Test validation for missing required fields"""
        response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "user@example.com"
                # Missing password
            }
        )
        
        assert response.status_code == 422


@pytest.mark.integration
class TestLoginEndpoint:
    """Test the /api/v1/auth/login endpoint"""
    
    async def test_login_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test successful login"""
        # Create user
        user_in = UserCreate(
            email="login@example.com",
            password="mypassword",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        # Login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "mypassword"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert len(data["access_token"]) > 0
        assert len(data["refresh_token"]) > 0
    
    async def test_login_wrong_password(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test login with incorrect password"""
        # Create user
        user_in = UserCreate(
            email="user@example.com",
            password="correctpassword",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        # Try login with wrong password
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "user@example.com",
                "password": "wrongpassword"
            }
        )
        
        assert response.status_code == 401
        assert "Incorrect email or password" in response.json()["detail"]
    
    async def test_login_nonexistent_user(
        self,
        client: AsyncClient
    ):
        """Test login with non-existent email"""
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "somepassword"
            }
        )
        
        assert response.status_code == 401
    
    async def test_login_inactive_user(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that inactive users cannot login"""
        # Create inactive user
        user_in = UserCreate(
            email="inactive@example.com",
            password="password",
            role="COMPANY_OWNER",
            is_active=False
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        # Try to login
        response = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "inactive@example.com",
                "password": "password"
            }
        )
        
        assert response.status_code == 400
        assert "Inactive user" in response.json()["detail"]


@pytest.mark.integration
class TestRefreshTokenEndpoint:
    """Test the /api/v1/auth/refresh endpoint"""
    
    async def test_refresh_token_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test refreshing access token with valid refresh token"""
        # Create user and login
        user_in = UserCreate(
            email="refresh@example.com", 
            password="password",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "refresh@example.com", "password": "password"}
        )
        
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # Wait 1 second to ensure tokens have different timestamps
        await asyncio.sleep(1)
        
        # Use refresh token to get new access token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        
        assert "access_token" in new_tokens
        assert new_tokens["token_type"] == "bearer"
        # New access token should be different from original
        assert new_tokens["access_token"] != tokens["access_token"]
    
    async def test_refresh_with_invalid_token(
        self,
        client: AsyncClient
    ):
        """Test refresh with invalid token"""
        response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "invalid.token.here"}
        )
        
        assert response.status_code == 401
    
    async def test_refresh_with_access_token(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test that using access token for refresh fails"""
        # Create user and login
        user_in = UserCreate(
            email="wrongtoken@example.com",
            password="password",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "wrongtoken@example.com", "password": "password"}
        )
        
        tokens = login_response.json()
        
        # Try to use access token for refresh (should fail)
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["access_token"]}
        )
        
        assert refresh_response.status_code == 401


@pytest.mark.integration
class TestGetCurrentUserEndpoint:
    """Test the /api/v1/auth/me endpoint"""
    
    async def test_get_current_user(
        self,
        client: AsyncClient,
        auth_headers: dict
    ):
        """Test getting current authenticated user"""
        response = await client.get(
            "/api/v1/auth/me",
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data["email"] == "test@example.com"
        assert "password" not in data
    
    async def test_get_current_user_unauthorized(
        self,
        client: AsyncClient
    ):
        """Test that accessing /me without auth fails"""
        response = await client.get("/api/v1/auth/me")
        
        assert response.status_code == 401
    
    async def test_get_current_user_invalid_token(
        self,
        client: AsyncClient
    ):
        """Test that invalid token fails"""
        response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": "Bearer invalid.token.here"}
        )
        
        assert response.status_code == 401


@pytest.mark.integration
class TestOAuth2LoginEndpoint:
    """Test the /api/v1/auth/login/oauth2 endpoint"""
    
    async def test_oauth2_login_success(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test OAuth2 form login"""
        # Create user
        user_in = UserCreate(
            email="oauth@example.com",
            password="password",
            role="COMPANY_OWNER"
        )
        await crud_user.create_user(db_session, user_in=user_in)
        await db_session.commit()
        
        # Login using form data (OAuth2 format)
        response = await client.post(
            "/api/v1/auth/login/oauth2",
            data={
                "username": "oauth@example.com",
                "password": "password"
            }
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"


@pytest.mark.integration
class TestAuthenticationFlow:
    """Integration tests for complete authentication flows"""
    
    async def test_complete_auth_flow(
        self,
        client: AsyncClient,
        db_session: AsyncSession
    ):
        """Test complete flow: register -> login -> access protected endpoint -> refresh"""
        # 1. Register
        register_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "flow@example.com",
                "password": "password123",
                "role": "COMPANY_OWNER"
            }
        )
        assert register_response.status_code == 201
        user_data = register_response.json()
        user_id = user_data["id"]
        
        # 2. Login
        login_response = await client.post(
            "/api/v1/auth/login",
            json={"email": "flow@example.com", "password": "password123"}
        )
        assert login_response.status_code == 200
        tokens = login_response.json()
        
        # 3. Access protected endpoint
        me_response = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {tokens['access_token']}"}
        )
        assert me_response.status_code == 200
        me_data = me_response.json()
        assert me_data["id"] == user_id
        assert me_data["email"] == "flow@example.com"
        
        # 4. Refresh token
        refresh_response = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": tokens["refresh_token"]}
        )
        assert refresh_response.status_code == 200
        new_token = refresh_response.json()
        
        # 5. Use new access token
        me_response2 = await client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {new_token['access_token']}"}
        )
        assert me_response2.status_code == 200
