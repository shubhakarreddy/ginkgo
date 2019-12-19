from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('fetch_data', views.fetch_data, name='fetch_data'),
    path('find_protein', views.find_protein, name='find_protein'),
    path('search_results', views.search_results, name='search_results'),
    path('show_samples', views.show_samples, name='show_samples'),
]
