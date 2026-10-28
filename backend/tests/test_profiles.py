import pytest
from sqlalchemy import select

from test_auth import auth_context, login, register  # noqa: F401
from app.features.auth.models import AccountStatus, AffiliationStatus, User


PAYLOAD = {"full_name": "Jordan Test", "status": "student", "graduation_year": 2027, "major": "Computer Science"}


def member(context, email="student@ufl.edu", *, verified=True):
    response = register(context, email)
    user_id = response.json()["user"]["id"]
    if verified:
        with context.session_factory() as db:
            user = db.get(User, user_id)
            user.email_verified = True
            user.account_status = AccountStatus.ACTIVE
            user.affiliation_status = AffiliationStatus.VERIFIED
            db.commit()
    login(context, email)
    return user_id


def write(context, method="post", payload=None, path="/api/profiles/me", csrf=True):
    headers = {"X-CSRF-Token": context.client.cookies.get("swampspace_csrf")} if csrf else {}
    return getattr(context.client, method)(path, json=PAYLOAD if payload is None else payload, headers=headers)


def test_create_view_update_and_identity_consistency(auth_context):
    user_id = member(auth_context)
    assert auth_context.client.get("/api/profiles/me").status_code == 404
    result = write(auth_context, payload={**PAYLOAD, "full_name": "  Jordan   Test  "})
    assert result.status_code == 201
    assert result.json()["full_name"] == "Jordan Test"
    assert result.json()["user_id"] == user_id
    assert not {"email", "password_hash", "role"} & result.json().keys()
    assert write(auth_context).status_code == 409
    result = write(auth_context, "patch", {"full_name": "Jordan Updated", "status": "alumni", "major": ""})
    assert result.status_code == 200
    assert result.json()["graduation_year"] == 2027
    assert result.json()["major"] == ""
    assert auth_context.client.get(f"/api/profiles/{user_id}").json()["full_name"] == "Jordan Updated"
    account = auth_context.client.get("/api/auth/me").json()
    assert account["display_name"] == "Jordan Updated"
    assert account["affiliation"] == "alumni"
    assert account["affiliation_status"] == "verified"
    with auth_context.session_factory() as db:
        assert db.get(User, user_id).display_name == "Jordan Updated"


@pytest.mark.parametrize("field,value", [
    ("full_name", "  "), ("full_name", "x" * 101), ("status", "staff"),
    ("graduation_year", 1899), ("graduation_year", 9999),
    ("graduation_year", 2027.5), ("graduation_year", "2027"),
    ("major", "x" * 121),
])
def test_invalid_profile_not_saved(auth_context, field, value):
    member(auth_context)
    assert write(auth_context, payload={**PAYLOAD, field: value}).status_code == 422
    assert auth_context.client.get("/api/profiles/me").status_code == 404


@pytest.mark.parametrize("field", ["full_name", "status", "graduation_year"])
def test_required_fields(auth_context, field):
    member(auth_context)
    assert write(auth_context, payload={k: v for k, v in PAYLOAD.items() if k != field}).status_code == 422


def test_patch_validation_preserves_profile(auth_context):
    member(auth_context)
    write(auth_context)
    for invalid in [{}, {"full_name": None}, {"graduation_year": None}, {"role": "admin"}, {"user_id": "other"}]:
        assert write(auth_context, "patch", invalid).status_code == 422
    assert auth_context.client.get("/api/profiles/me").json()["full_name"] == PAYLOAD["full_name"]


def test_access_and_csrf(auth_context):
    for path in ["/api/profiles", "/api/profiles/me", "/api/profiles/unknown"]:
        assert auth_context.client.get(path).status_code == 401
    assert auth_context.client.post("/api/profiles/me", json=PAYLOAD).status_code == 401
    member(auth_context, verified=False)
    assert auth_context.client.get("/api/profiles").status_code == 403
    assert write(auth_context).status_code == 403
    with auth_context.session_factory() as db:
        user = db.scalar(select(User))
        user.email_verified = True
        user.account_status = AccountStatus.ACTIVE
        db.commit()
    assert auth_context.client.get("/api/profiles").status_code == 403
    with auth_context.session_factory() as db:
        user = db.scalar(select(User))
        user.affiliation_status = AffiliationStatus.VERIFIED
        db.commit()
    assert write(auth_context, csrf=False).status_code == 403
    assert write(auth_context).status_code == 201


def test_other_member_view_and_owner_only_writes(auth_context):
    first = member(auth_context)
    write(auth_context)
    member(auth_context, "second@ufl.edu")
    assert auth_context.client.get(f"/api/profiles/{first}").status_code == 200
    assert write(auth_context, "patch", {"full_name": "Attacker"}, path=f"/api/profiles/{first}").status_code == 405
    assert write(auth_context, "patch", {"full_name": "Attacker"}).status_code == 404
    assert auth_context.client.get(f"/api/profiles/{first}").json()["full_name"] == "Jordan Test"


def test_search_filters_pagination_and_hidden_members(auth_context):
    first = member(auth_context)
    write(auth_context)
    second = member(auth_context, "second@ufl.edu")
    write(auth_context, payload={**PAYLOAD, "full_name": "Alex Finance", "major": "Finance", "graduation_year": 2022})
    def search(**params):
        response = auth_context.client.get("/api/profiles", params=params)
        assert response.status_code == 200
        return response.json()
    assert search()["total"] == 2
    assert search(q="jordan computer")["items"][0]["user_id"] == first
    assert search(major="computer science", graduation_year=2027)["total"] == 1
    assert search(major="Finance", graduation_year=2027)["total"] == 0
    assert search(q="%_")["total"] == 0
    assert search(q="no such person")["items"] == []
    assert search(limit=1)["items"][0]["user_id"] == second
    assert search(limit=1, offset=1)["items"][0]["user_id"] == first
    with auth_context.session_factory() as db:
        db.get(User, first).account_status = AccountStatus.DISABLED
        db.commit()
    assert search()["total"] == 1
    assert auth_context.client.get(f"/api/profiles/{first}").status_code == 404
    assert auth_context.client.get("/api/profiles/unknown").status_code == 404
    assert auth_context.client.get("/api/profiles?limit=100").status_code == 422
