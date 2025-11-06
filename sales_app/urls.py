from django.urls import path
from . import views

app_name = 'sales_app'
urlpatterns = [
    path('', views.index, name='index'),
    path('save-data/', views.save_data, name='save_data'),
    path('upload-xml/', views.upload_xml, name='upload_xml'),
    path('edit-sale/<int:pk>/', views.edit_sale, name='edit_sale'),
    path('delete-sale/<int:pk>/', views.delete_sale, name='delete_sale'),
    path('search-sales/', views.search_sales, name='search_sales'),
]