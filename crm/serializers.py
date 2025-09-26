from rest_framework import serializers
from .models import EntityType, Entity, EntityDetail


class EntityTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityType
        fields = ["id", "code", "name"]


class EntityCreateSerializer(serializers.Serializer):
    entity_uid = serializers.UUIDField(required=False)
    entity_type_code = serializers.CharField()
    display_name = serializers.CharField()


class EntityResponseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Entity
        fields = ["entity_uid", "display_name", "valid_from", "valid_to", "is_current"]


class DetailSerializer(serializers.Serializer):
    entity_uid = serializers.UUIDField()
    detail_code = serializers.CharField()
    detail_value = serializers.CharField()


class EntityDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = EntityDetail
        fields = [
            "id",
            "entity_uid",
            "detail_code",
            "detail_value",
            "valid_from",
            "valid_to",
            "is_current",
        ]
        read_only_fields = ["id", "valid_from", "valid_to", "is_current"]
