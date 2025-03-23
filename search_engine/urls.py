from django.urls import path
from .views import IndexView, SearchView

urlpatterns = [
    path('index/', IndexView.as_view(), name='index'),
    path('search/', SearchView.as_view(), name='search'),
]
