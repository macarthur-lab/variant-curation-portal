# pylint: disable=redefined-outer-name,unused-argument
import pytest
from rest_framework.test import APIClient

from curation_portal.models import CurationAssignment, Project, User, Variant

pytestmark = pytest.mark.django_db  # pylint: disable=invalid-name


@pytest.fixture(scope="module")
def db_setup(django_db_setup, django_db_blocker, create_variant):
    with django_db_blocker.unblock():
        project = Project.objects.create(id=1, name="Test Project")
        variant1 = create_variant(project, "1-100-A-G")
        create_variant(project, "1-120-G-A")
        create_variant(project, "1-150-C-G")
        create_variant(project, "1-200-A-T")

        user1 = User.objects.create(username="user1")
        user2 = User.objects.create(username="user2")
        user3 = User.objects.create(username="user3")

        project.owners.set([user1])
        CurationAssignment.objects.create(curator=user2, variant=variant1)

        yield

        project.delete()

        user1.delete()
        user2.delete()
        user3.delete()


def test_creating_project_assignments_requires_authentication(db_setup):
    client = APIClient()
    response = client.post("/api/project/1/assignments/")
    assert response.status_code == 403


@pytest.mark.parametrize(
    "username,expected_status_code", [("user1", 200), ("user2", 403), ("user3", 404)]
)
def test_project_assignments_can_only_be_set_by_project_owners(
    db_setup, username, expected_status_code
):
    client = APIClient()
    client.force_authenticate(User.objects.get(username=username))
    response = client.post(
        "/api/project/1/assignments/",
        {"assignments": [{"curator": "user3", "variant_id": "1-100-A-G"}]},
        format="json",
    )
    assert response.status_code == expected_status_code

    CurationAssignment.objects.filter(curator__username="user3", variant__project=1).delete()


def test_create_projects_assignments(db_setup):
    client = APIClient()
    client.force_authenticate(User.objects.get(username="user1"))
    response = client.post(
        "/api/project/1/assignments/",
        {
            "assignments": [
                {"curator": "user3", "variant_id": "1-100-A-G"},
                {"curator": "user3", "variant_id": "1-120-G-A"},
                {"curator": "user3", "variant_id": "1-150-C-G"},
            ]
        },
        format="json",
    )
    assert response.status_code == 200

    for variant_id in ["1-100-A-G", "1-120-G-A", "1-150-C-G"]:
        assert CurationAssignment.objects.filter(
            curator__username="user3", variant__variant_id=variant_id, variant__project=1
        ).exists()

    CurationAssignment.objects.filter(curator__username="user3", variant__project=1).delete()


def test_create_project_assignments_validates_variant_exists(db_setup):
    client = APIClient()
    client.force_authenticate(User.objects.get(username="user1"))
    response = client.post(
        "/api/project/1/assignments/",
        {
            "assignments": [
                {"curator": "user3", "variant_id": "1-100-G-T"},
                {"curator": "user3", "variant_id": "1-100-A-G"},
            ]
        },
        format="json",
    )
    assert response.status_code == 400

    assert (
        CurationAssignment.objects.filter(curator__username="user3", variant__project=1).count()
        == 0
    )


def test_create_project_assignments_creates_user_if_necessary(db_setup):
    assert not User.objects.filter(username="user4").exists()

    client = APIClient()
    client.force_authenticate(User.objects.get(username="user1"))
    response = client.post(
        "/api/project/1/assignments/",
        {"assignments": [{"curator": "user4", "variant_id": "1-100-A-G"}]},
        format="json",
    )
    assert response.status_code == 200

    assert User.objects.filter(username="user4").exists()
    assert CurationAssignment.objects.filter(
        curator__username="user4", variant__variant_id="1-100-A-G", variant__project=1
    ).exists()

    CurationAssignment.objects.filter(curator__username="user4", variant__project=1).delete()
    User.objects.filter(username="user4").delete()


def test_create_project_assignments_rejects_assignments_that_already_exist(db_setup):
    assignment = CurationAssignment.objects.create(
        curator=User.objects.get(username="user3"),
        variant=Variant.objects.get(project=1, variant_id="1-120-G-A"),
    )

    client = APIClient()
    client.force_authenticate(User.objects.get(username="user1"))
    response = client.post(
        "/api/project/1/assignments/",
        {
            "assignments": [
                {"curator": "user3", "variant_id": "1-120-G-A"},
                {"curator": "user3", "variant_id": "1-150-C-G"},
            ]
        },
        format="json",
    )
    assert response.status_code == 400

    assert (
        CurationAssignment.objects.filter(curator__username="user3", variant__project=1).count()
        == 1
    )

    assignment.delete()


def test_create_project_assignments_rejects_duplicate_assignments(db_setup):
    client = APIClient()
    client.force_authenticate(User.objects.get(username="user1"))
    response = client.post(
        "/api/project/1/assignments/",
        {
            "assignments": [
                {"curator": "user1", "variant_id": "1-100-A-G"},
                {"curator": "user1", "variant_id": "1-100-A-G"},
                {"curator": "user3", "variant_id": "1-120-G-A"},
                {"curator": "user3", "variant_id": "1-120-G-A"},
            ]
        },
        format="json",
    )
    assert response.status_code == 400

    response = response.json()
    assert "non_field_errors" in response
    assert (
        "Duplicate assignments for user1 (variants 1-100-A-G), user3 (variants 1-120-G-A)"
        in response["non_field_errors"]
    )

    assert not CurationAssignment.objects.filter(
        curator__username="user1", variant__variant_id="1-100-A-G"
    ).exists()
    assert not CurationAssignment.objects.filter(
        curator__username="user3", variant__variant_id="1-120-G-A"
    ).exists()
