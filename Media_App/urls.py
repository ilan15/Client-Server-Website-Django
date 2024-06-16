

from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('QueryResults', views.QueryResults, name='QueryResults'),
    path('Rankings', views.Rankings, name='Rankings'),
    path('RecordsManagement', views.RecordsManagement, name='RecordsManagement')
]

