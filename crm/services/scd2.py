import hashlib
from django.utils import timezone
from django.db import transaction
from crm.models import Entity, EntityDetail, AuditLog, EntityType


def _hashdiff(payload: dict) -> str:
    import json
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False)
    return hashlib.sha256(blob.encode("utf-8")).hexdigest()


@transaction.atomic
def upsert_entity(*, entity_uid, entity_type_code, display_name, change_ts, actor):
    et = EntityType.objects.get(code=entity_type_code)
    payload = {"entity_uid": str(entity_uid), "entity_type": et.code, "display_name": display_name}
    h = _hashdiff(payload)

    current = Entity.objects.filter(entity_uid=entity_uid, is_current=True).first()

    if current and current.hashdiff == h:
        return current, False

    now = change_ts or timezone.now()
    if current:
        current.valid_to = now
        current.is_current = False
        current.save(update_fields=["valid_to", "is_current", "updated_at"])

    new_row = Entity.objects.create(
        entity_uid=entity_uid,
        entity_type=et,
        display_name=display_name,
        valid_from=now,
        is_current=True,
        hashdiff=h,
    )

    AuditLog.objects.create(
        entity_uid=entity_uid,
        detail_code=None,
        before_value=(current.display_name if current else None),
        after_value=display_name,
        actor=actor,
    )
    return new_row, True


@transaction.atomic
def upsert_detail(*, entity_uid, detail_code, detail_value, change_ts, actor):
    payload = {"entity_uid": str(entity_uid), "detail_code": detail_code, "detail_value": detail_value}
    h = _hashdiff(payload)
    current = EntityDetail.objects.filter(
        entity_uid=entity_uid, detail_code=detail_code, is_current=True
    ).first()
    if current and current.hashdiff == h:
        return current, False
    now = change_ts or timezone.now()
    if current:
        current.valid_to = now
        current.is_current = False
        current.save(update_fields=["valid_to", "is_current", "updated_at"])
    new_row = EntityDetail.objects.create(
        entity_uid=entity_uid,
        detail_code=detail_code,
        detail_value=detail_value,
        valid_from=now,
        is_current=True,
        hashdiff=h,
    )
    AuditLog.objects.create(
        entity_uid=entity_uid,
        detail_code=detail_code,
        before_value=(current.detail_value if current else None),
        after_value=detail_value,
        actor=actor,
    )
    return new_row, True
