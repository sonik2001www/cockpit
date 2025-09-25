from rest_framework.routers import DefaultRouter
from .views import EntityViewSet, EntityDetailViewSet, EntityTypeViewSet

router = DefaultRouter()
router.register(r'api/v1/entities', EntityViewSet, basename='entity')
router.register(r'api/v1/details', EntityDetailViewSet, basename='detail')
router.register(r'api/v1/types', EntityTypeViewSet, basename='entitytype')

app_name = "crm"
urlpatterns = router.urls
