from app.features.auth.models import AccountStatus, AffiliationStatus, User
from test_auth import auth_context, login, register


def member(context, email="student@ufl.edu", *, verified=True):
    response = register(context, email=email)
    assert response.status_code == 201
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

def write(
        context,
        method="post",
        payload=None,
        path="/api/community/posts",
        csrf=True
):
    headers = {}
    if csrf:
        token = context.client.cookies.get("swampspace_csrf")
        headers["X-CSRF-Token"] = token

    kwargs = {"headers": headers}
    if payload is not None:
        kwargs["json"] = payload

    return getattr(context.client, method)(path, **kwargs)

def test_create_and_list_posts(auth_context):
    user_id = member(auth_context)

    created = write(
        auth_context,
        payload={"content": "I've just lost The Game."}
    )

    assert created.status_code == 201
    post = created.json()
    assert post["user_id"] == user_id
    assert post["content"] == "I've just lost The Game."
    assert post["author_name"]

    response = auth_context.client.get("/api/community/posts")
    assert response.status_code == 200
    assert len(response.json()) == 1
    assert response.json()[0]["id"] == post["id"]

def test_create_post_rejects_empty_content(auth_context):
    member(auth_context)

    response = write(auth_context, payload={"content": ""})

    assert response.status_code == 422

def test_create_post_rejects_whitespace_content(auth_context):
    member(auth_context)

    response = write(auth_context, payload={"content": "   \n\t  "})

    assert response.status_code == 422

def test_create_post_rejects_content_over_limit(auth_context):
    member(auth_context)

    response = write(auth_context, payload={"content": 'A' * 9001})

    assert response.status_code == 422

def test_create_post_strips_surrounding_whitespace(auth_context):
    member(auth_context)

    response1 = write(
        auth_context,
        payload={"content": "\f \tI've just lost The Game. Again. \n \r"}
    )

    assert response1.status_code == 201
    assert response1.json()["content"] == "\tI've just lost The Game. Again."

    response2 = write(
        auth_context,
        payload={"content": "\t\t\t\t\t\t\t"}
    )

    assert response2.status_code == 422

def test_author_can_edit_post(auth_context):
    member(auth_context)

    created = write(
        auth_context,
        payload={"content": "Original post"}
    )
    post_id = created.json()["id"]

    response = write(
        auth_context,
        method="patch",
        path=f"/api/community/posts/{post_id}",
        payload={"content": "Updated post"}
    )

    assert response.status_code == 200
    assert response.json()["content"] == "Updated post"

def test_user_cannot_edit_anothers_post(auth_context):
    member(auth_context, email="first@ufl.edu")

    created = write(
        auth_context,
        payload={"content": "Original post"}
    )
    post_id = created.json()["id"]

    member(auth_context, email="second@ufl.edu")

    response = write(
        auth_context,
        method="patch",
        path=f"/api/community/posts/{post_id}",
        payload={"content": "Unauthorized edit"}
    )

    assert response.status_code == 404

def test_author_can_delete_post(auth_context):
    member(auth_context)

    created = write(
        auth_context,
        payload={"content": "To be deleted"}
    )
    post_id = created.json()["id"]

    response = write(
        auth_context,
        method="delete",
        path=f"/api/community/posts/{post_id}"
    )

    assert response.status_code == 204

    posts = auth_context.client.get("/api/community/posts")
    assert posts.status_code == 200
    assert all(post["id"] != post_id for post in posts.json())

def test_user_cannot_delete_anothers_post(auth_context):
    member(auth_context, email="first@ufl.edu")

    created = write(
        auth_context,
        payload={"content": "First user's post"}
    )
    post_id = created.json()["id"]

    member(auth_context, email="second@ufl.edu")

    response = write(
        auth_context,
        method="delete",
        path=f"/api/community/posts/{post_id}"
    )

    assert response.status_code == 404

    posts = auth_context.client.get("/api/community/posts")
    assert any(post["id"] == post_id for post in posts.json())

def test_unverified_user_cannot_post(auth_context):
    member(auth_context, verified=False)

    response = write(
        auth_context,
        payload={"content": "Reject this"}
    )

    assert response.status_code == 403

def test_create_post_requires_csrf(auth_context):
    member(auth_context)

    response = write(
        auth_context,
        payload={"content": "Missing CSTF token"},
        csrf=False
    )

    assert response.status_code == 403

def test_edit_post_requires_csrf(auth_context):
    member(auth_context)

    created = write(
        auth_context,
        payload={"content": "To be edited"},
    )
    post_id = created.json()["id"]

    response = write(
        auth_context,
        method="patch",
        path=f"/api/community/posts/{post_id}",
        payload={"content": "Updated post"},
        csrf=False
    )

    assert response.status_code == 403

def test_delete_post_requires_csrf(auth_context):
    member(auth_context)

    created = write(
        auth_context,
        payload={"content": "To be deleted"},
    )
    post_id = created.json()["id"]

    response = write(
        auth_context,
        method="delete",
        path=f"/api/community/posts/{post_id}",
        csrf=False
    )

    assert response.status_code == 403

    posts = auth_context.client.get("/api/community/posts")
    assert any(post["id"] == post_id for post in posts.json())

def test_edit_updates_timestamp(auth_context):
    member(auth_context)

    created = write(
        auth_context,
        payload={"content": "Original post"}
    )
    assert created.status_code == 201
    post_id = created.json()["id"]
    updated_at_initial = created.json()["updated_at"]

    response = write(
        auth_context,
        method="patch",
        path=f"/api/community/posts/{post_id}",
        payload={"content": "Updated post"}
    )

    assert response.status_code == 200
    assert response.json()["updated_at"] != updated_at_initial