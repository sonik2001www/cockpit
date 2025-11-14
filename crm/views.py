import uuid
from drf_spectacular.utils import extend_schema
from .permissions import ReadOnlyOrTokenRequired
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.utils.dateparse import parse_datetime
from django.db.models import Q, ProtectedError
from .models import Entity, EntityDetail, EntityType
from .serializers import (
    EntityCreateSerializer,
    EntityResponseSerializer,
    EntityDetailSerializer,
    EntityTypeSerializer, EntityUpdateSerializer, DetailSerializer,
)
from .services.scd2 import upsert_entity, upsert_detail
from django.utils import timezone


@extend_schema(tags=["Types"])
class EntityTypeViewSet(viewsets.ModelViewSet):
    """
    GET /api/v1/types/         -> list
    POST /api/v1/types/        -> create
    GET /api/v1/types/{id}/    -> detail (id)
    PATCH /api/v1/types/{id}/  -> update (id)
    DELETE /api/v1/types/{id}/ -> delete (id)
    """

    queryset = EntityType.objects.all()
    serializer_class = EntityTypeSerializer
    permission_classes = [ReadOnlyOrTokenRequired]

    def destroy(self, request, pk=None):
        obj = EntityType.objects.filter(pk=pk).first()

        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        try:
            obj.delete()
        except ProtectedError:
            return Response(
                {"detail": "Cannot delete type: there are ENTITIES referencing it."},
                status=status.HTTP_409_CONFLICT,
            )
        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Entities"])
class EntityViewSet(viewsets.ViewSet):
    """
    GET /api/v1/entities?q=...&type=PERSON
    GET /api/v1/entities/{uid}
    POST /api/v1/entities
    PATCH /api/v1/entities/{uid}
    GET /api/v1/entities/{uid}/history
    GET /api/v1/entities-asof?as_of=YYYY-MM-DDTHH:MM:SSZ
    GET /api/v1/entities/diff?from=...&to=...
    """

    permission_classes = [ReadOnlyOrTokenRequired]

    # GET /api/v1/entities?q=...&type=PERSON
    def list(self, request):
        objs = Entity.objects.filter(is_current=True)
        q = request.query_params.get("q")
        if q:
            objs = objs.filter(display_name__icontains=q)
        t = request.query_params.get("type")
        if t:
            objs = objs.filter(entity_type__code=t)
        data = EntityResponseSerializer(objs, many=True).data
        return Response(data)

    # GET /api/v1/entities/{uid}
    def retrieve(self, request, pk=None):
        obj = Entity.objects.filter(entity_uid=pk, is_current=True).first()
        if not obj:
            return Response(status=404)
        data = EntityResponseSerializer(obj).data
        details = EntityDetail.objects.filter(entity_uid=pk, is_current=True).values(
            "detail_code", "detail_value"
        )
        data["details"] = list(details)
        return Response(data)

    # POST /api/v1/entities
    @extend_schema(
        request=EntityCreateSerializer,
        responses={201: EntityResponseSerializer, 200: EntityResponseSerializer},
    )
    def create(self, request):
        s = EntityCreateSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        payload = s.validated_data.copy()
        if "entity_uid" not in payload:
            payload["entity_uid"] = uuid.uuid4()

        row, created = upsert_entity(
            actor=request.user if request.user.is_authenticated else None,
            change_ts=None,
            **payload,
        )

        if created:
            st = status.HTTP_201_CREATED
        else:
            st = status.HTTP_200_OK

        return Response(EntityResponseSerializer(row).data, status=st)

    # PATCH /api/v1/entities/{uid}
    @extend_schema(
        request=EntityUpdateSerializer,
        responses={204: EntityResponseSerializer, 200: EntityResponseSerializer},
    )
    def partial_update(self, request, pk=None):
        obj = Entity.objects.filter(entity_uid=pk, is_current=True).first()
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload = {
            "entity_uid": pk,
            "entity_type_code": request.data.get("entity_type_code")
            or obj.entity_type.code,
            "display_name": request.data.get("display_name") or obj.display_name,
        }

        row, created = upsert_entity(
            actor=request.user if request.user.is_authenticated else None,
            change_ts=None,
            **payload,
        )

        if created:
            st = status.HTTP_204_NO_CONTENT
        else:
            st = status.HTTP_200_OK

        return Response(EntityResponseSerializer(row).data, status=st)

    # GET /api/v1/entities/{uid}/history
    @action(detail=True, methods=["get"])
    def history(self, request, pk=None):
        objs = (
            Entity.objects.filter(entity_uid=pk)
            .order_by("valid_from")
            .values("display_name", "entity_type", "valid_from", "valid_to", "is_current")
        )
        return Response(list(objs))

    # GET /api/v1/entities-asof?as_of=YYYY-MM-DDTHH:MM:SSZ
    @action(detail=False, methods=["get"], url_path="entities-asof")
    def asof(self, request):
        as_of = parse_datetime(request.query_params.get("as_of") or "")

        if not as_of:
            return Response({"detail": "Invalid as_of"}, status=400)

        objs = Entity.objects.filter(valid_from__lte=as_of).filter(
            Q(valid_to__isnull=True) | Q(valid_to__gt=as_of)
        )
        data = EntityResponseSerializer(objs, many=True).data
        return Response(data)

    # GET /api/v1/entities/diff?from=...&to=...
    @action(detail=False, methods=["get"], url_path="diff")
    def diff(self, request):
        f = parse_datetime(request.query_params.get("from") or "")
        t = parse_datetime(request.query_params.get("to") or "")

        if not (f and t and f < t):
            return Response({"detail": "Invalid range"}, status=400)

        changed_entities = (
            Entity.objects.filter(updated_at__gte=f, updated_at__lt=t)
            .values_list("entity_uid", flat=True)
            .distinct()
        )

        return Response({"entities_changed": list(changed_entities)})

    # DELETE /api/v1/entities/{uid}
    def destroy(self, request, pk=None):
        obj = Entity.objects.filter(entity_uid=pk, is_current=True).first()

        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.valid_to = timezone.now()
        obj.is_current = False
        obj.save(update_fields=["valid_to", "is_current"])

        return Response(status=status.HTTP_204_NO_CONTENT)


@extend_schema(tags=["Details"])
class EntityDetailViewSet(viewsets.ViewSet):
    permission_classes = [ReadOnlyOrTokenRequired]

    # GET /api/v1/details/?entity_uid=...
    def list(self, request):
        entity_uid = request.query_params.get("entity_uid")
        objs = EntityDetail.objects.filter(is_current=True)

        if entity_uid:
            objs = objs.filter(entity_uid=entity_uid)

        data = EntityDetailSerializer(objs, many=True).data
        return Response(data)

    # GET /api/v1/details/{id}
    def retrieve(self, request, pk=None):
        obj = EntityDetail.objects.filter(id=pk).first()
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(EntityDetailSerializer(obj).data)

    # POST /api/v1/details/
    @extend_schema(
        request=DetailSerializer,
        responses={201: EntityDetailSerializer, 200: EntityDetailSerializer},
    )
    def create(self, request):
        s = DetailSerializer(data=request.data)
        s.is_valid(raise_exception=True)

        row, created = upsert_detail(
            actor=request.user if request.user.is_authenticated else None,
            change_ts=timezone.now(),
            **s.validated_data,
        )

        return Response(
            EntityDetailSerializer(row).data,
            status=status.HTTP_201_CREATED if created else status.HTTP_200_OK,
        )

    # PATCH /api/v1/details/{uid}
    @extend_schema(
        request=EntityDetailSerializer,
        responses={204: EntityDetailSerializer, 200: EntityDetailSerializer},
    )
    def partial_update(self, request, pk=None):
        obj = EntityDetail.objects.filter(entity_uid=pk, is_current=True).first()

        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        payload = {
            "entity_uid": pk,
            "detail_code": request.data.get("detail_code") or obj.detail_code,
            "detail_value": request.data.get("detail_value") or obj.detail_value,
        }

        row, created = upsert_detail(
            actor=request.user if request.user.is_authenticated else None,
            change_ts=None,
            **payload,
        )

        if created:
            st = status.HTTP_204_NO_CONTENT
        else:
            st = status.HTTP_200_OK

        return Response(EntityDetailSerializer(row).data, status=st)

    # DELETE /api/v1/details/{id}
    def destroy(self, request, pk=None):
        obj = EntityDetail.objects.filter(pk=pk, is_current=True).first()

        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)

        obj.valid_to = timezone.now()
        obj.is_current = False
        obj.save(update_fields=["valid_to", "is_current"])

        return Response(status=status.HTTP_204_NO_CONTENT)
