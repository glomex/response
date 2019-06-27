from django.conf.urls import url, include
from django.urls import path

import ui.views as views

urlpatterns = [
    path('incidents/', views.incident_list, name='incident_list'),
    path('incident/<int:incident_id>/', views.incident_doc, name='incident_doc'),
]
