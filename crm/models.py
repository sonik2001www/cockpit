import uuid
from django.db import models
from django.db.models import Q


class EntityType(models.Model):
    code = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.code


class Entity(models.Model):

    entity_uid = models.UUIDField(default=uuid.uuid4, db_index=True)
    entity_type = models.ForeignKey(EntityType, on_delete=models.PROTECT)
    display_name = models.TextField()

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    hashdiff = models.CharField(max_length=128, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entity_uid"],
                condition=Q(is_current=True),
                name="uniq_entity_current",
            ),
        ]
        indexes = [
            models.Index(fields=["entity_uid", "is_current"]),
            models.Index(fields=["valid_from"]),
        ]


class EntityDetail(models.Model):
    entity_uid = models.UUIDField(db_index=True)
    detail_code = models.CharField(max_length=64)
    detail_value = models.TextField()

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField(null=True, blank=True)
    is_current = models.BooleanField(default=True)

    hashdiff = models.CharField(max_length=128, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["entity_uid", "detail_code"],
                condition=Q(is_current=True),
                name="uniq_entity_detail_current",
            ),
        ]
        indexes = [
            models.Index(fields=["entity_uid", "detail_code", "is_current"]),
            models.Index(fields=["valid_from"]),
        ]


class AuditLog(models.Model):
    entity_uid = models.UUIDField()
    detail_code = models.CharField(max_length=64, null=True, blank=True)
    before_value = models.TextField(null=True, blank=True)
    after_value = models.TextField(null=True, blank=True)
    actor = models.CharField(max_length=128)
    changed_at = models.DateTimeField(auto_now_add=True)
