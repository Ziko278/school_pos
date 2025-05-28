from django.urls import path
from inventory.views import *

urlpatterns = [

    
    path('category/create', CategoryCreateView.as_view(), name='inventory_category_create'),
    path('category/index', CategoryListView.as_view(), name='inventory_category_index'),
    path('category/<int:pk>/edit', CategoryUpdateView.as_view(), name='inventory_category_edit'),
    path('category/<int:pk>/delete', CategoryDeleteView.as_view(), name='inventory_category_delete'),

    path('product/create', ProductCreateView.as_view(), name='product_create'),
    path('product/index', ProductListView.as_view(), name='product_index'),
    path('product/<int:pk>/detail', ProductDetailView.as_view(), name='product_detail'),
    path('product/<int:pk>/edit', ProductUpdateView.as_view(), name='product_edit'),
    path('product/<int:pk>/delete', ProductDeleteView.as_view(), name='product_delete'),
    path('product/stock-in', product_stock_in_view, name='product_stock_in'),
    path('product/stock-in/<int:pk>/detail', product_stock_in_detail_view, name='product_stock_in_detail'),
    path('api/product-lookup-by-barcode/', api_product_lookup_by_barcode, name='api_product_lookup_by_barcode'),
    path('place-order/', place_order_view, name='place_order'),
    path('orders/', view_orders, name='view_orders'),
    path('orders/pending', view_pending_orders, name='view_pending_orders'),
    path('order/<int:sale_id>/confirm/', confirm_order_view, name='confirm_order'),
    path('order/<int:sale_id>/cancel/', cancel_order_view, name='cancel_order'),

    path('orders/<int:pk>/', order_detail, name='order_detail'),

    path('api/students/', api_student_search, name='api_student_search'),
    path('api/products/', api_product_search, name='api_product_search'),
    path('api/barcode-lookup/', api_barcode_lookup, name='api_barcode_lookup'),

    path('supplier/create', SupplierCreateView.as_view(), name='supplier_create'),
    path('supplier/index', SupplierListView.as_view(), name='supplier_index'),
    path('supplier/<int:pk>/detail', SupplierDetailView.as_view(), name='supplier_detail'),
    path('supplier/<int:pk>/edit', SupplierUpdateView.as_view(), name='supplier_edit'),
    path('supplier/<int:pk>/delete', SupplierDeleteView.as_view(), name='supplier_delete'),
]
