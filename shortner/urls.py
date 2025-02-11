from django.urls import path
from . import views

urlpatterns = [
    path('api/urls/', views.create_short_url, name='create_short_url'),
    path('api/urls/<str:short_code>/analytics/', views.url_analytics, name='url_analytics'),
    path('<str:short_code>/', views.redirect_to_long_url, name='redirect_to_long_url'),
]