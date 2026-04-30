from fastapi.testclient import TestClient

from app.core.auth import create_access_token, decode_access_token, get_current_user, hash_password, verify_password
from app.core.database import get_db
from app.main import app


def test_hash_and_verify():
    hashed = hash_password("secret123")
    assert verify_password("secret123", hashed)
    assert not verify_password("wrong", hashed)


def test_create_and_decode_token():
    token = create_access_token("admin")
    subject = decode_access_token(token)
    assert subject == "admin"


def test_unauthenticated_request_blocked(db_session):
    """인증 없이 보호 엔드포인트 접근 시 401."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    # 인증 override 제거 → 실제 인증 적용
    app.dependency_overrides.pop(get_current_user, None)

    client = TestClient(app)
    response = client.get("/api/orders")
    assert response.status_code == 401

    app.dependency_overrides.clear()


def test_authenticated_request_passes(db_session):
    """유효한 토큰으로 보호 엔드포인트 접근."""

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides.pop(get_current_user, None)

    token = create_access_token("admin")
    client = TestClient(app)
    response = client.get("/api/orders", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200

    app.dependency_overrides.clear()


def test_health_is_public():
    """헬스체크는 인증 없이 접근 가능."""
    app.dependency_overrides.pop(get_current_user, None)
    client = TestClient(app)
    response = client.get("/health")
    assert response.status_code == 200
    app.dependency_overrides.clear()
