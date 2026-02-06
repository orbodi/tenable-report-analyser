from django.urls import path

from . import views

app_name = "reports"

urlpatterns = [
    path("", views.upload_view, name="upload"),
    path("result/", views.result_view, name="result"),
    path("history/", views.history_view, name="history"),
    path("history/<int:pk>/", views.comparison_detail, name="comparison_detail"),
    path("history/<int:pk>/delete/", views.delete_comparison, name="delete_comparison"),
    path("export/<str:kind>/", views.export_csv, name="export_csv"),
]

