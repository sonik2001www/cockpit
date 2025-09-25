import uuid
from datetime import timedelta

import pytest
from django.utils import timezone
from rest_framework.test import APIClient
from crm.models import EntityType, Entity, EntityDetail


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def entity_type(db):
    person = EntityType.objects.create(code="PERSON", name="Person")
    company = EntityType.objects.create(code="COMPANY", name="Company")
    return {"person": person, "company": company}


# Unit test for SCD2 transitions ???
def test_scd2_transition_entity(db, entity_type):
    uid = uuid.uuid4()

    e1 = Entity.objects.create(
        entity_uid=uid,
        entity_type=entity_type["person"],
        display_name="Oleg Sem",
        valid_from=timezone.now(),
        is_current=True,
        hashdiff="h1",
    )

    e1.is_current = False
    e1.valid_to = timezone.now()
    e1.save()

    e2 = Entity.objects.create(
        entity_uid=uid,
        entity_type=entity_type["person"],
        display_name="Ivan Sem",
        valid_from=timezone.now(),
        is_current=True,
        hashdiff="h2",
    )

    assert Entity.objects.filter(entity_uid=uid, is_current=True).count() == 1
    assert Entity.objects.filter(entity_uid=uid).count() == 2
    assert e2.display_name == "Ivan Sem"


# create, list, retrieve
def test_api_entity_create_and_list(api_client, entity_type):
    payload = {"entity_type_code": "PERSON", "display_name": "Dan"}
    resp = api_client.post("/api/v1/entities/", payload, format="json")
    assert resp.status_code == 201
    uid = resp.data["entity_uid"]

    # list
    resp2 = api_client.get("/api/v1/entities/")
    assert resp2.status_code == 200
    uids = [e["entity_uid"] for e in resp2.data]
    assert uid in uids

    # detail
    resp3 = api_client.get(f"/api/v1/entities/{uid}/")
    assert resp3.status_code == 200
    assert resp3.data["display_name"] == "Dan"


# update with SCD2 (PATCH)
def test_api_entity_update_scd2(api_client, entity_type):
    payload = {"entity_type_code": "PERSON", "display_name": "Bob"}
    resp = api_client.post("/api/v1/entities/", payload, format="json")
    assert resp.status_code == 201
    uid = resp.data["entity_uid"]

    # PATCH display_name
    resp2 = api_client.patch(f"/api/v1/entities/{uid}/", {"display_name": "Alicia"}, format="json")
    assert resp2.status_code == 201
    assert resp2.data["display_name"] == "Alicia"

    # PATCH entity_type_code
    resp3 = api_client.patch(f"/api/v1/entities/{uid}/", {"entity_type_code": "COMPANY"}, format="json")
    assert resp3.status_code == 201
    assert resp3.data["entity_uid"] == uid

    # PATCH {}
    resp4 = api_client.patch(f"/api/v1/entities/{uid}/", {}, format="json")
    assert resp4.status_code == 200
    assert resp4.data["entity_uid"] == uid

    history = api_client.get(f"/api/v1/entities/{uid}/history/")
    assert history.status_code == 200
    assert len(history.data) == 3


# as-of snapshot
def test_api_asof(api_client, entity_type):
    payload = {"entity_type_code": "PERSON", "display_name": "Dan"}
    resp = api_client.post("/api/v1/entities/", payload, format="json")
    uid = resp.data["entity_uid"]

    as_of_date = (timezone.now() + timezone.timedelta(seconds=1)).strftime("%Y-%m-%dT%H:%M:%SZ")

    resp2 = api_client.get(f"/api/v1/entities/entities-asof/?as_of={as_of_date}")
    assert resp2.status_code == 200
    assert any(e["entity_uid"] == uid for e in resp2.data)


# diff
def test_api_diff(api_client, entity_type):
    payload = {"entity_type_code": "PERSON", "display_name": "Dima"}
    resp = api_client.post("/api/v1/entities/", payload, format="json")
    uid = resp.data["entity_uid"]

    now = timezone.now()
    f = (now - timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    t = (now + timedelta(minutes=1)).replace(microsecond=0).isoformat().replace("+00:00", "Z")

    resp2 = api_client.get(f"/api/v1/entities/diff/?from={f}&to={t}")
    assert resp2.status_code == 200
    assert uuid.UUID(uid) in resp2.data["entities_changed"]


# test for SCD2 transitions
def test_idempotency_entity(api_client, entity_type):
    payload = {"entity_type_code": "PERSON", "display_name": "Ivan"}
    resp1 = api_client.post("/api/v1/entities/", payload, format="json")
    uid = resp1.data["entity_uid"]

    payload["entity_uid"] = uid

    resp2 = api_client.post("/api/v1/entities/", payload, format="json")
    assert resp2.status_code == 200
    assert Entity.objects.filter(entity_uid=uid, is_current=True).count() == 1


# Negative test - invalid as_of
def test_api_asof_invalid(api_client):
    resp = api_client.get("/api/v1/entities/entities-asof/?as_of=not-a-date")
    assert resp.status_code == 400


# tests for EntityDetail
def test_api_entity_detail_create_and_update(api_client, entity_type):
    # define Entity
    payload = {"entity_type_code": "PERSON", "display_name": "Valentyn"}
    resp = api_client.post("/api/v1/entities/", payload, format="json")
    uid = resp.data["entity_uid"]

    # define detail
    d_payload = {"entity_uid": uid, "detail_code": "EMAIL", "detail_value": "valentyn@gmail.com"}
    resp2 = api_client.post("/api/v1/details/", d_payload, format="json")
    assert resp2.status_code == 201
    detail_id = resp2.data["id"]

    # update detail
    resp3 = api_client.patch(f"/api/v1/details/{detail_id}/", {"detail_value": "valentyn@new.com"}, format="json")
    assert resp3.status_code == 200
    assert resp3.data["detail_value"] == "valentyn@new.com"
    detail_id = resp3.data["id"]

    # delete detail
    resp4 = api_client.delete(f"/api/v1/details/{detail_id}/")
    assert resp4.status_code == 204
    obj = EntityDetail.objects.get(id=detail_id)
    assert obj.is_current is False
