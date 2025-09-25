from django.contrib import admin
from .models import EntityType, Entity, EntityDetail, AuditLog

admin.site.register([EntityType, Entity, EntityDetail, AuditLog])
