from rest_framework.routers import DefaultRouter
from .views import EntityViewSet, EntityDetailViewSet, EntityTypeViewSet

router = DefaultRouter()
router.register(r"entities", EntityViewSet, basename="entity")
router.register(r"details", EntityDetailViewSet, basename="detail")
router.register(r"types", EntityTypeViewSet, basename="entitytype")

app_name = "crm"
urlpatterns = router.urls
