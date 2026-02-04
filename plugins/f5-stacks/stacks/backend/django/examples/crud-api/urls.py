# apps/products/urls.py
"""
Product API URL configuration.

REQ-001: Product CRUD API
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from apps.products.views import ProductViewSet

app_name = 'products'

# Create router and register viewsets
router = DefaultRouter()
router.register('', ProductViewSet, basename='product')

# URL patterns
urlpatterns = [
    path('', include(router.urls)),
]

# Generated URL patterns:
# ---------------------------------------------------------
# List/Create:
#   GET    /products/              → ProductViewSet.list()
#   POST   /products/              → ProductViewSet.create()
#
# Detail/Update/Delete:
#   GET    /products/{pk}/         → ProductViewSet.retrieve()
#   PUT    /products/{pk}/         → ProductViewSet.update()
#   PATCH  /products/{pk}/         → ProductViewSet.partial_update()
#   DELETE /products/{pk}/         → ProductViewSet.destroy()
#
# Custom Actions:
#   POST   /products/{pk}/activate/    → ProductViewSet.activate()
#   POST   /products/{pk}/deactivate/  → ProductViewSet.deactivate()
#   POST   /products/{pk}/restore/     → ProductViewSet.restore()
#   POST   /products/bulk-delete/      → ProductViewSet.bulk_delete()
#   GET    /products/stats/            → ProductViewSet.stats()
# ---------------------------------------------------------
