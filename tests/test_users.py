import pytest
from flask import Flask
from app import create_app
from app.extensions import db
from app.models.user import User, RoleEnum


@pytest.fixture
def app():
    app = create_app("testing")  # Define "testing" config later
    app.config["TESTING"] = True
    # In-memory DB for fast tests
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    return app.test_client()


def test_ping(client):
    res = client.get("/ping")
    assert res.status_code == 200
    assert res.get_json() == {"status": "ok"}


def test_user_registration(client):
    # Given
    user_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "secure123"
    }

    # When
    res = client.post("/api/v1/register", json=user_data)

    # Then
    assert res.status_code == 201
    data = res.get_json()
    assert data["username"] == user_data["username"]
    assert data["email"] == user_data["email"]
    assert data["role"] == "member"  # default role
    assert "id" in data
    assert "created_at" in data
    assert "password" not in data  # Ensure password is not exposed


def test_login_success(client):
    # First, register a user
    client.post("/api/v1/register", json={
        "username": "loginuser",
        "email": "login@test.com",
        "password": "mypassword"
    })

    # Then, try logging in
    res = client.post("/api/v1/login", json={
        "email": "login@test.com",
        "password": "mypassword"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert "token" in data
    assert data["user"]["email"] == "login@test.com"
    assert data["user"]["username"] == "loginuser"


def test_login_wrong_password(client):
    client.post("/api/v1/register", json={
        "username": "wrongpassuser",
        "email": "wrongpass@test.com",
        "password": "correctpassword"
    })

    res = client.post("/api/v1/login", json={
        "email": "wrongpass@test.com",
        "password": "wrongpassword"
    })

    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


def test_login_nonexistent_email(client):
    res = client.post("/api/v1/login", json={
        "email": "nonexistent@test.com",
        "password": "whatever"
    })

    assert res.status_code == 401
    assert res.get_json()["error"] == "Invalid email or password"


def test_login_missing_fields(client):
    res = client.post("/api/v1/login", json={
        "email": "missing@test.com"
        # password is missing
    })

    assert res.status_code == 400
    assert res.get_json()["error"] == "Missing email or password"


def test_guild_leader_can_access(client):
    # Register as a guild leader
    client.post("/api/v1/register", json={
        "username": "guildleader",
        "email": "leader@test.com",
        "password": "leaderpass"
    })

    # Manually promote to guild leader via SQL or mock
    with client.application.app_context():
        user = db.session.execute(db.select(User).filter_by(
            email="leader@test.com")).scalar_one()
        user.role = RoleEnum.guild_leader
        db.session.commit()

    # Login to get token
    res = client.post("/api/v1/login", json={
        "email": "leader@test.com",
        "password": "leaderpass"
    })
    token = res.get_json()["token"]

    # Access protected route
    res = client.get("/api/v1/guild-leader-only", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 200
    assert "Welcome Guild Leader!" in res.get_json()["message"]


def test_member_cannot_access_guild_leader_only(client):
    # Register as regular member
    client.post("/api/v1/register", json={
        "username": "normaluser",
        "email": "member@test.com",
        "password": "memberpass"
    })

    # Login to get token
    res = client.post("/api/v1/login", json={
        "email": "member@test.com",
        "password": "memberpass"
    })
    token = res.get_json()["token"]

    # Try accessing restricted route
    res = client.get("/api/v1/guild-leader-only", headers={
        "Authorization": f"Bearer {token}"
    })
    assert res.status_code == 403
    assert res.get_json()["error"] == "Forbidden: Insufficient role"


def test_protected_route_without_token(client):
    res = client.get("/api/v1/guild-leader-only")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Token is missing!"


def test_creator_is_promoted_to_guild_leader(client):
    # Step 1: Register the user
    client.post("/api/v1/register", json={
        "username": "guildadmin",
        "email": "admin@test.com",
        "password": "securepass"
    })

    # Step 2: Login to get token
    res = client.post("/api/v1/login", json={
        "email": "admin@test.com",
        "password": "securepass"
    })
    token = res.get_json()["token"]

    # Step 3: Create a guild
    res = client.post("/api/v1/guilds", json={
        "name": "Test Guild",
        "description": "Guild created in test"
    }, headers={
        "Authorization": f"Bearer {token}"
    })

    assert res.status_code == 201

    # Step 4: Verify user is now a guild leader and assigned to the new guild

    with client.application.app_context():
        user = db.session.get(User, 1)
        assert user.role == RoleEnum.guild_leader
        assert user.guild_id == 1


def test_get_guild_by_id(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "viewer",
        "email": "viewer@test.com",
        "password": "testpass"
    })

    login_res = client.post("/api/v1/login", json={
        "email": "viewer@test.com",
        "password": "testpass"
    })
    token = login_res.get_json()["token"]

    # Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Visible Guild",
        "description": "This should be viewable"
    }, headers={"Authorization": f"Bearer {token}"})

    # Get the guild details
    res = client.get("/api/v1/guilds/1", headers={
        "Authorization": f"Bearer {token}"
    })

    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "Visible Guild"
    assert data["id"] == 1


def test_get_guild_by_invalid_id_returns_404(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "ghost",
        "email": "ghost@test.com",
        "password": "ghostpass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "ghost@test.com",
        "password": "ghostpass"
    })
    token = login_res.get_json()["token"]

    # Try to access a non-existent guild
    res = client.get("/api/v1/guilds/999", headers={
        "Authorization": f"Bearer {token}"
    })

    assert res.status_code == 404
    assert res.get_json()["error"] == "Guild not found"


def test_duplicate_guild_name_fails(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "dupeuser",
        "email": "dupe@test.com",
        "password": "pass123"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "dupe@test.com",
        "password": "pass123"
    })
    token = login_res.get_json()["token"]

    # Create first guild
    client.post("/api/v1/guilds", json={
        "name": "Duped Guild",
        "description": "First attempt"
    }, headers={"Authorization": f"Bearer {token}"})

    # Register a second user
    client.post("/api/v1/register", json={
        "username": "dupeuser2",
        "email": "dupe2@test.com",
        "password": "pass123"
    })
    login_res_2 = client.post("/api/v1/login", json={
        "email": "dupe2@test.com",
        "password": "pass123"
    })
    token2 = login_res_2.get_json()["token"]

    # Try to create guild with the same name
    res = client.post("/api/v1/guilds", json={
        "name": "Duped Guild",
        "description": "Should fail"
    }, headers={"Authorization": f"Bearer {token2}"})

    assert res.status_code == 400
    assert "already exists" in res.get_json()["error"]


def test_user_cannot_create_multiple_guilds(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "repeatuser",
        "email": "repeat@test.com",
        "password": "repeatpass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "repeat@test.com",
        "password": "repeatpass"
    })
    token = login_res.get_json()["token"]

    # First guild creation
    client.post("/api/v1/guilds", json={
        "name": "First Guild",
        "description": "Allowed"
    }, headers={"Authorization": f"Bearer {token}"})

    # Second guild creation (should fail)
    res = client.post("/api/v1/guilds", json={
        "name": "Second Guild",
        "description": "Should be blocked"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 400
    assert "already in a guild" in res.get_json()["error"]


def test_guild_creation_missing_name(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "nonamer",
        "email": "noname@test.com",
        "password": "nonamepass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "noname@test.com",
        "password": "nonamepass"
    })
    token = login_res.get_json()["token"]

    # Missing name in payload
    res = client.post("/api/v1/guilds", json={
        "description": "Missing name field"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 400
    assert res.get_json()["error"] == "Guild name is required"


def test_registration_missing_fields(client):
    # Missing password
    res1 = client.post("/api/v1/register", json={
        "username": "incomplete",
        "email": "incomplete@test.com"
    })
    assert res1.status_code == 400
    assert res1.get_json()["error"] == "Missing fields"

    # Missing email
    res2 = client.post("/api/v1/register", json={
        "username": "noemail",
        "password": "pass123"
    })
    assert res2.status_code == 400
    assert res2.get_json()["error"] == "Missing fields"

    # Missing username
    res3 = client.post("/api/v1/register", json={
        "email": "nouser@test.com",
        "password": "pass123"
    })
    assert res3.status_code == 400
    assert res3.get_json()["error"] == "Missing fields"


def test_guild_creation_requires_auth(client):
    res = client.post("/api/v1/guilds", json={
        "name": "Unauthorized Guild",
        "description": "No token should block this"
    })
    assert res.status_code == 401
    assert res.get_json()["error"] == "Token is missing!"


def test_list_guild_members(client):
    # Step 1: Register and log in a user who will create the guild
    client.post("/api/v1/register", json={
        "username": "creator",
        "email": "creator@test.com",
        "password": "securepass"
    })

    login_res = client.post("/api/v1/login", json={
        "email": "creator@test.com",
        "password": "securepass"
    })
    token = login_res.get_json()["token"]

    # Step 2: Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Pytest Guild",
        "description": "Guild for testing"
    }, headers={"Authorization": f"Bearer {token}"})

    # Step 3: Call the /guilds/1/members endpoint
    res = client.get("/api/v1/guilds/1/members", headers={
        "Authorization": f"Bearer {token}"
    })

    assert res.status_code == 200
    members = res.get_json()
    assert isinstance(members, list)
    assert len(members) == 1
    assert members[0]["username"] == "creator"
    assert members[0]["role"] == "guild_leader"
    assert members[0]["guild_id"] == 1


def test_list_guild_members_unauthorized(client):
    # Try accessing members list without token
    res = client.get("/api/v1/guilds/1/members")
    assert res.status_code == 401
    assert res.get_json()["error"] == "Token is missing!"


def test_guild_leader_can_update_guild(client):
    # Step 1: Register and log in
    client.post("/api/v1/register", json={
        "username": "leader",
        "email": "leader@test.com",
        "password": "leaderpass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "leader@test.com",
        "password": "leaderpass"
    })
    token = login_res.get_json()["token"]

    # Step 2: Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Old Guild Name",
        "description": "Old description"
    }, headers={"Authorization": f"Bearer {token}"})

    # Step 3: Update the guild
    res = client.patch("/api/v1/guilds/1", json={
        "name": "New Guild Name",
        "description": "Updated description"
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 200
    data = res.get_json()
    assert data["name"] == "New Guild Name"
    assert data["description"] == "Updated description"
    assert data["id"] == 1


def test_member_can_leave_guild(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "member",
        "email": "member@test.com",
        "password": "securepass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "member@test.com",
        "password": "securepass"
    })
    token = login_res.get_json()["token"]

    # Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Temp Guild",
        "description": "Temporary guild"
    }, headers={"Authorization": f"Bearer {token}"})

    # Register a second user who will join the guild
    client.post("/api/v1/register", json={
        "username": "seconduser",
        "email": "second@test.com",
        "password": "securepass"
    })
    login2 = client.post("/api/v1/login", json={
        "email": "second@test.com",
        "password": "securepass"
    })
    token2 = login2.get_json()["token"]

    # Manually add second user to the guild
    with client.application.app_context():
        from app.models.user import User
        leader = db.session.get(User, 1)
        second = db.session.get(User, 2)
        second.guild_id = leader.guild_id
        db.session.commit()

    # Second user leaves the guild
    res = client.delete("/api/v1/guilds/1/leave", headers={
        "Authorization": f"Bearer {token2}"
    })

    assert res.status_code == 200
    assert "successfully left" in res.get_json()["message"]


def test_guild_leader_cannot_leave_guild(client):
    # Register and login
    client.post("/api/v1/register", json={
        "username": "leader",
        "email": "leader@test.com",
        "password": "securepass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "leader@test.com",
        "password": "securepass"
    })
    token = login_res.get_json()["token"]

    # Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Leader Guild",
        "description": "Guild with leader"
    }, headers={"Authorization": f"Bearer {token}"})

    # Attempt to leave as guild leader
    res = client.delete("/api/v1/guilds/1/leave", headers={
        "Authorization": f"Bearer {token}"
    })

    assert res.status_code == 400
    assert "must transfer leadership" in res.get_json()["error"]


def test_guild_leader_can_transfer_leadership(client):
    # Register and login as the current leader
    client.post("/api/v1/register", json={
        "username": "leader",
        "email": "leader@test.com",
        "password": "securepass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "leader@test.com",
        "password": "securepass"
    })
    token1 = login_res.get_json()["token"]

    # Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Transfer Guild",
        "description": "Guild for testing leadership transfer"
    }, headers={"Authorization": f"Bearer {token1}"})

    # Register and login the new leader
    client.post("/api/v1/register", json={
        "username": "newleader",
        "email": "newleader@test.com",
        "password": "securepass"
    })
    login2 = client.post("/api/v1/login", json={
        "email": "newleader@test.com",
        "password": "securepass"
    })
    token2 = login2.get_json()["token"]

    # Add newleader to the same guild manually
    with client.application.app_context():
        from app.models.user import User
        leader = db.session.get(User, 1)
        new_leader = db.session.get(User, 2)
        new_leader.guild_id = leader.guild_id
        db.session.commit()

    # Transfer leadership to newleader
    res = client.post("/api/v1/guilds/1/transfer-leadership", json={
        "new_leader_id": 2
    }, headers={"Authorization": f"Bearer {token1}"})

    assert res.status_code == 200
    assert "successfully transferred" in res.get_json()["message"]

    # Verify new roles
    with client.application.app_context():
        leader = db.session.get(User, 1)
        new_leader = db.session.get(User, 2)
        assert leader.role == RoleEnum.member
        assert new_leader.role == RoleEnum.guild_leader


def test_cannot_transfer_leadership_to_non_member(client):
    # Register and login as leader
    client.post("/api/v1/register", json={
        "username": "soleleader",
        "email": "soleleader@test.com",
        "password": "securepass"
    })
    login1 = client.post("/api/v1/login", json={
        "email": "soleleader@test.com",
        "password": "securepass"
    })
    token = login1.get_json()["token"]

    # Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Solo Guild",
        "description": "Testing invalid transfer"
    }, headers={"Authorization": f"Bearer {token}"})

    # Register new user who is NOT in the guild
    client.post("/api/v1/register", json={
        "username": "outsider",
        "email": "outsider@test.com",
        "password": "securepass"
    })

    # Attempt to transfer leadership
    res = client.post("/api/v1/guilds/1/transfer-leadership", json={
        "new_leader_id": 2
    }, headers={"Authorization": f"Bearer {token}"})

    assert res.status_code == 400
    assert "must be a member of the same guild" in res.get_json()["error"]


def test_guild_leader_can_kick_member(client):
    # Step 1: Register and login as guild leader
    client.post("/api/v1/register", json={
        "username": "leader",
        "email": "leader@test.com",
        "password": "securepass"
    })
    login_res = client.post("/api/v1/login", json={
        "email": "leader@test.com",
        "password": "securepass"
    })
    leader_token = login_res.get_json()["token"]

    # Step 2: Create a guild
    client.post("/api/v1/guilds", json={
        "name": "Kickable Guild",
        "description": "Testing kicking members"
    }, headers={"Authorization": f"Bearer {leader_token}"})

    # Step 3: Register and login a second user
    client.post("/api/v1/register", json={
        "username": "kickeduser",
        "email": "kicked@test.com",
        "password": "securepass"
    })
    login_res_2 = client.post("/api/v1/login", json={
        "email": "kicked@test.com",
        "password": "securepass"
    })
    kicked_token = login_res_2.get_json()["token"]

    # Step 4: Manually add kicked user to the guild
    with client.application.app_context():
        from app.models.user import User
        leader = db.session.get(User, 1)
        kicked = db.session.get(User, 2)
        kicked.guild_id = leader.guild_id
        db.session.commit()

    # Step 5: Kick the member
    res = client.delete("/api/v1/guilds/1/members/2", headers={
        "Authorization": f"Bearer {leader_token}"
    })

    assert res.status_code == 200
    assert res.get_json()[
        "message"] == "Member has been removed from the guild."

    # Step 6: Confirm kicked user's guild_id is now None
    with client.application.app_context():
        kicked = db.session.get(User, 2)
        assert kicked.guild_id is None
