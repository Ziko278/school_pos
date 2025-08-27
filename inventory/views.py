import base64
import json
import random

from django.utils.timezone import now
from pytz import timezone as pytz_timezone
from django.contrib.auth.decorators import login_required, permission_required
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.contrib.messages.views import SuccessMessageMixin, messages
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from django.views.generic import TemplateView
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.views.generic.list import ListView
from django.contrib.auth import authenticate, login
from django.views.generic.detail import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.sessions.models import Session

from admin_site.models import SchoolSettingModel, ActivityLogModel
from inventory.models import *
from django.db.models import Q, Count, Sum
from datetime import datetime, date
from urllib.parse import urlencode
from django.contrib.auth import logout
from django.http import HttpResponse, JsonResponse, HttpResponseBadRequest
from inventory.models import *
from inventory.forms import *
from collections import OrderedDict

from student.models import StudentWalletModel, FingerprintModel
from student.signals import get_day_ordinal_suffix
from user_site.models import UserProfileModel


class CategoryCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = CategoryModel
    permission_required = 'inventory.add_productmodel'
    form_class = CategoryForm
    success_message = 'Category Added Successfully'
    template_name = 'inventory/category/index.html'

    def get_success_url(self):
        return reverse('inventory_category_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_category_list'] = CategoryModel.objects.all().order_by('name')
        return context


class CategoryListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = CategoryModel
    permission_required = 'inventory.view_productmodel'
    fields = '__all__'
    template_name = 'inventory/category/index.html'
    context_object_name = "inventory_category_list"

    def get_queryset(self):
        return CategoryModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['form'] = CategoryForm

        return context


class CategoryUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = CategoryModel
    permission_required = 'inventory.change_productmodel'
    form_class = CategoryForm
    success_message = 'Category Updated Successfully'
    template_name = 'inventory/category/index.html'

    def get_success_url(self):
        return reverse('inventory_category_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['inventory_category_list'] = CategoryModel.objects.all().order_by('name')
        return context


class CategoryDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = CategoryModel
    permission_required = 'inventory.delete_productmodel'
    success_message = 'Category Deleted Successfully'
    fields = '__all__'
    template_name = 'inventory/category/delete.html'
    context_object_name = "category"

    def get_success_url(self):
        return reverse("inventory_category_index")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = ProductModel
    permission_required = 'inventory.add_productmodel'
    form_class = ProductForm
    success_message = 'Product Added Successfully'
    template_name = 'inventory/product/create.html'

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class ProductListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = ProductModel
    permission_required = 'inventory.view_productmodel'
    fields = '__all__'
    template_name = 'inventory/product/index.html'
    context_object_name = "product_list"

    def get_queryset(self):
        return ProductModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = CategoryModel.objects.all()
        context['form'] = ProductForm
        return context


class ProductDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = ProductModel
    permission_required = 'inventory.view_productmodel'
    fields = '__all__'
    template_name = 'inventory/product/detail.html'
    context_object_name = "product"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Get the current school setting for session and term
        school_setting = SchoolSettingModel.objects.first()
        context['school_setting'] = school_setting

        # Filter suppliers related to the current product
        context['supplier_list'] = SupplierModel.objects.filter(products__id__in=[self.object.id])

        # Get all sales items for the current product
        all_sale_items = SaleItemModel.objects.filter(product=self.object)

        # Filter sales items for the current term and session
        current_term_sale_items = all_sale_items.filter(
            sale__session=school_setting.session,
            sale__term=school_setting.term
        )

        # Calculate Current Term Metrics
        # Aggregate total quantity, total price, and total profit for the current term
        current_term_aggregates = current_term_sale_items.aggregate(
            total_quantity=Sum('quantity'),
            total_price=Sum('subtotal'),  # Changed from 'total_price' to 'subtotal'
            total_profit=Sum('profit')
        )
        context['total_quantity_current_term'] = current_term_aggregates['total_quantity'] or 0
        context['total_price_current_term'] = current_term_aggregates['total_price'] or 0.00
        context['total_profit_current_term'] = current_term_aggregates['total_profit'] or 0.00

        # Calculate All Time Metrics
        # Aggregate total quantity, total price, and total profit for all time
        all_time_aggregates = all_sale_items.aggregate(
            total_quantity=Sum('quantity'),
            total_price=Sum('subtotal'),  # Changed from 'total_price' to 'subtotal'
            total_profit=Sum('profit')
        )
        context['total_quantity_all_time'] = all_time_aggregates['total_quantity'] or 0
        context['total_price_all_time'] = all_time_aggregates['total_price'] or 0.00
        context['total_profit_all_time'] = all_time_aggregates['total_profit'] or 0.00

        # The original context['order_list'] was for current term, now we have more specific data
        # If you still need the queryset of current term sale items, you can keep this:
        context['order_list'] = current_term_sale_items
        context['stock_list'] = StockInModel.objects.filter(product=self.object).order_by('-created_at')[:20]

        price_history_list = PriceHistoryModel.objects.filter(product=self.object).order_by('change_date')
        context['price_history_list'] = price_history_list
        context['stock_out_form'] = StockOutForm
        return context


class ProductUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = ProductModel
    permission_required = 'inventory.change_productmodel'
    form_class = ProductForm
    success_message = 'Product Updated Successfully'
    template_name = 'inventory/product/edit.html'

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['product_list'] = ProductModel.objects.all().order_by('name')
        return context


class ProductDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = ProductModel
    permission_required = 'inventory.delete_productmodel'
    success_message = 'Product Deleted Successfully'
    fields = '__all__'
    template_name = 'inventory/product/delete.html'
    context_object_name = "product"

    def get_success_url(self):
        return reverse('product_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context
    
    
class SupplierCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = SupplierModel
    permission_required = 'inventory.add_productmodel'
    form_class = SupplierForm
    success_message = 'Supplier Added Successfully'
    template_name = 'inventory/supplier/create.html'

    def get_success_url(self):
        return reverse('supplier_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class SupplierListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = SupplierModel
    permission_required = 'inventory.view_productmodel'
    fields = '__all__'
    template_name = 'inventory/supplier/index.html'
    context_object_name = "supplier_list"

    def get_queryset(self):
        return SupplierModel.objects.all().order_by('name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category_list'] = CategoryModel.objects.all()
        context['form'] = SupplierForm
        return context


class SupplierDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    model = SupplierModel
    permission_required = 'inventory.view_productmodel'
    fields = '__all__'
    template_name = 'inventory/supplier/detail.html'
    context_object_name = "supplier"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context['category_list'] = CategoryModel.objects.all().order_by('name')
        context['supplier_list'] = SupplierModel.objects.all().order_by('name')
        return context


class SupplierUpdateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, UpdateView):
    model = SupplierModel
    permission_required = 'inventory.change_productmodel'
    form_class = SupplierForm
    success_message = 'Supplier Updated Successfully'
    template_name = 'inventory/supplier/edit.html'

    def get_success_url(self):
        return reverse('supplier_detail', kwargs={'pk': self.object.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['supplier_list'] = SupplierModel.objects.all().order_by('name')
        return context


class SupplierDeleteView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, DeleteView):
    model = SupplierModel
    permission_required = 'inventory.delete_productmodel'
    success_message = 'Supplier Deleted Successfully'
    fields = '__all__'
    template_name = 'inventory/supplier/delete.html'
    context_object_name = "supplier"

    def get_success_url(self):
        return reverse('supplier_index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


# from users.models import StaffModel # Adjust import based on your StaffModel location

# Helper function to get StaffModel instance (adjust based on your auth setup)
def get_staff_instance(user):
    # Example: If your User model has a one-to-one link to StaffModel
    return UserProfileModel.objects.get(user=user).staff
    # Or if StaffModel itself is your User model, just return user
    #return user  # Assuming request.user is a StaffModel instance


@login_required
@permission_required("inventory.add_stockinmodel", raise_exception=True)
def product_stock_in_view(request):
    stock_in_summary_form = StockInSummaryForm()
    formset = StockInFormSet(queryset=StockInModel.objects.none())

    if request.method == 'POST':
        stock_in_summary_form = StockInSummaryForm(request.POST)
        formset = StockInFormSet(request.POST, queryset=StockInModel.objects.none())

        if stock_in_summary_form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    staff_member = get_staff_instance(request.user)

                    # 1. Save the StockInSummary (Header)
                    stock_in_summary = stock_in_summary_form.save(commit=False)
                    stock_in_summary.created_by = staff_member
                    stock_in_summary.save()

                    newly_added_stock_in_items = []

                    # 2. Save the individual StockInModel items from the formset
                    for form in formset:
                        if form.has_changed() and not form.cleaned_data.get('DELETE'):
                            stock_in_item = form.save(commit=False)
                            stock_in_item.created_by = staff_member
                            stock_in_item.save()  # This save triggers StockInModel's save method and post_save signal
                            newly_added_stock_in_items.append(stock_in_item)

                    # 3. Manually link StockInModel instances to StockInSummaryModel via ManyToMany
                    stock_in_summary.products.set(newly_added_stock_in_items)

                messages.success(request, 'Stock received successfully!')
                return redirect(reverse('product_stock_in_detail', kwargs={'pk': stock_in_summary.id}))

            except Exception as e:
                messages.error(request, f'Error processing stock-in: {e}')
                import logging
                logger = logging.getLogger(__name__)
                logger.exception("Stock-in transaction failed")
        else:
            messages.error(request, 'Please correct the errors below.')

    context = {
        'stock_in_summary_form': stock_in_summary_form,
        'formset': formset,
        'title': 'Receive New Stock',
    }
    return render(request, 'inventory/stock/stock_in.html', context)


class StockInListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StockInSummaryModel
    permission_required = 'inventory.view_stockinmodel'
    fields = '__all__'
    template_name = 'inventory/stock/index.html'
    context_object_name = "inventory_stock_list"

    def get_queryset(self):
        return StockInSummaryModel.objects.annotate(
            num_products=Count('products') # Annotate each summary with the count of its related products
        ).filter(num_products__gt=0)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@login_required
def api_product_lookup_by_barcode(request):
    barcode = request.GET.get('barcode', None)
    if barcode:
        try:
            # Assuming your ProductModel has a 'barcode' field
            product = ProductModel.objects.get(barcode=barcode)
            data = {
                'product_id': product.pk,
                'product_name': product.name, # Or whatever display name you want
                'unit_cost_price': str(product.cost_price), # Assuming a cost_price field
                # Add any other product details you need in the frontend
            }
            return JsonResponse(data)
        except ProductModel.DoesNotExist:
            return JsonResponse({'error': 'Product not found'}, status=404)
    return JsonResponse({'error': 'No barcode provided'}, status=400)


@login_required
@permission_required("inventory.add_stockinmodel", raise_exception=True)
def product_stock_in_detail_view(request, pk):
    """
    Displays the details of a specific stock-in summary and its associated products.
    """
    # Get the StockInSummary instance or return a 404 error if not found
    stock_in_summary = get_object_or_404(StockInSummaryModel, pk=pk)

    # Fetch all StockInModel items linked to this summary.
    # IMPORTANT: This assumes StockInModel has a ForeignKey named 'stock_in_summary'
    # pointing back to StockInSummaryModel. If not, you'll need to adjust your model
    # and run migrations.
    stock_in_items = stock_in_summary.products.all()

    # Calculate the total cost for all items in this receipt
    total_receipt_cost = sum(
        (item.quantity_added * item.unit_cost_price) for item in stock_in_items
    )

    context = {
        'stock_in_summary': stock_in_summary,
        'stock_in_items': stock_in_items,
        'total_receipt_cost': total_receipt_cost,
        'title': f'Stock Receipt #{stock_in_summary.id} Details', # Dynamic title for the page
    }
    return render(request, 'inventory/stock/detail.html', context)


class StockOutCreateView(LoginRequiredMixin, PermissionRequiredMixin, SuccessMessageMixin, CreateView):
    model = StockOutModel
    permission_required = 'inventory.add_stockinmodel'
    form_class = StockOutForm
    success_message = 'Product Stocked Out'
    template_name = 'inventory/product/detail.html'

    def form_valid(self, form):
        """
        Sets the 'created_by' field to the staff member associated with the
        current logged-in user's UserProfile before saving.
        """
        try:
            # Get the UserProfile linked to the current user
            user_profile = UserProfileModel.objects.get(user=self.request.user)
            # Assign the associated staff object to created_by
            form.instance.created_by = user_profile.staff
        except UserProfileModel.DoesNotExist:
            # Handle case where a UserProfile does not exist for the user
            # You might log this, raise an error, or assign None/default
            # For example, to prevent saving if profile is missing:
            form.add_error(None, "User profile not found. Cannot assign staff.")
            return self.form_invalid(form)
        except AttributeError:
            # Handle case where user_profile exists but 'staff' attribute is missing or None
            form.add_error(None, "Staff association missing in user profile. Cannot assign staff.")
            return self.form_invalid(form)

        return super().form_valid(form)

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.stock.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


class StockOutIndexView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = StockOutModel
    permission_required = 'inventory.add_stockinmodel'
    template_name = 'inventory/stock/stock_out_index.html'
    fields = '__all__'
    context_object_name = "stock_out_list"

    def get_queryset(self):
        return StockOutModel.objects.order_by('-created_at')[:100]

    def get_success_url(self):
        return reverse('product_detail', kwargs={'pk': self.object.stock.product.pk})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        return context


@require_GET
@login_required
def api_student_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)
    terms = q.split()
    query = Q()
    for term in terms:
        term_q = (
            Q(surname__icontains=term) |
            Q(last_name__icontains=term) |
            Q(registration_number__icontains=term)
        )
        query &= term_q
    students = StudentModel.objects.filter(query)[:10]
    results = []
    for s in students:
        wallet = getattr(s, 'student_wallet', None)
        balance = wallet.balance if wallet else 0.0
        debt = wallet.debt if wallet else 0.0
        results.append({
            'id': s.id,
            'name': f"{s.surname} {s.last_name}",
            'reg_number': s.registration_number,
            'student_class': f"{s.student_class.name} {s.class_section.name}",
            'wallet_balance': float(balance),
            'wallet_debt': float(debt),
            'image_url': s.photo.url if hasattr(s, 'photo') and s.photo else ''
        })
    return JsonResponse(results, safe=False)


@require_GET
@login_required
def api_product_search(request):
    q = request.GET.get('q', '').strip()
    if not q:
        return JsonResponse([], safe=False)
    products = ProductModel.objects.filter(name__icontains=q)[:10]
    results = [
        {
            'id': p.id,
            'name': p.name,
            'qty_remaining': p.quantity,
            'selling_price': float(p.price),
        }
        for p in products
    ]
    return JsonResponse(results, safe=False)


@csrf_exempt
@login_required
@require_POST
def api_barcode_lookup(request):
    code = request.POST.get('barcode', '').strip()
    product = ProductModel.objects.filter(barcode=code).first()
    if product:
        data = {
            'id': product.id,
            'name': product.name,
            'qty_remaining': product.quantity,
            'selling_price': float(product.sell_price),
        }
        return JsonResponse({'type': 'product', 'data': data})
    student = StudentModel.objects.filter(barcode=code).first()
    if student:
        wallet = getattr(student, 'student_wallet', None)
        balance = wallet.balance if wallet else 0.0
        debt = wallet.debt if wallet else 0.0
        data = {
            'id': student.id,
            'name': f"{student.surname} {student.last_name}",
            'reg_number': student.registration_number,
            'student_class': getattr(student, 'student_class', ''),
            'wallet_balance': float(balance),
            'wallet_debt': float(debt),
            'image_url': student.photo.url if hasattr(student, 'photo') and student.photo else ''
        }
        return JsonResponse({'type': 'student', 'data': data})
    return JsonResponse({'type': None, 'data': {}}, status=404)


@login_required
@permission_required("inventory.add_salemodel", raise_exception=True)
@transaction.atomic
def place_order_view(request):
    if request.method == 'GET':
        settings_obj = SchoolSettingModel.objects.last()
        context = {
            'settings': settings_obj,
            'products': ProductModel.objects.all(),
        }
        return render(request, 'inventory/sales/place_order.html', context)

    # --- POST: Process the sale ---
    pk = request.POST.get('student_id')
    if not pk:
        messages.error(request, 'Please Select a Student')
        return redirect(reverse('place_order'))
    student = get_object_or_404(StudentModel, pk=pk)
    wallet, _ = StudentWalletModel.objects.get_or_create(student=student)

    # Gather line-items
    idx = 0
    items = []
    total_amount = Decimal('0.00')
    total_items  = 0
    while True:
        pid = request.POST.get(f'products[{idx}][product_id]')
        qty = request.POST.get(f'products[{idx}][quantity]')
        if not pid or not qty:
            break
        product    = get_object_or_404(ProductModel, pk=pid)
        quantity   = int(qty)
        unit_price = product.price
        line_total = unit_price * quantity

        items.append((product, quantity, unit_price))
        total_amount += line_total
        total_items  += quantity
        idx += 1

    # Validate funds
    max_debt  = SchoolSettingModel.objects.first().max_student_debt
    available = wallet.balance + (max_debt - wallet.debt)
    if total_amount > available:
        return HttpResponseBadRequest('Insufficient funds or max debt exceeded')

    # Create Sale header
    sale = SaleModel.objects.create(
        student=student,
        total_amount=total_amount,
        total_items=total_items
    )
    try:
        created_by = UserProfileModel.objects.get(user=request.user).staff
        sale.created_by = created_by
        sale.save()
    except Exception:
        pass

    # Process each line with FIFO batch consumption
    for product, qty, unit_price in items:
        # Create a placeholder SaleItem
        sale_item = SaleItemModel.objects.create(
            sale=sale,
            product=product,
            quantity=qty,
            unit_price=unit_price,
            cost_price=Decimal('0.00'),
            profit=Decimal('0.00'),
            subtotal=unit_price * qty
        )

        # FIFO consume StockInModel.quantity_left, update quantity_sold
        remaining  = qty
        total_cost = Decimal('0.00')
        batches = StockInModel.objects.filter(
            product=product,
            quantity_left__gt=0
        ).order_by('date_added', 'created_at')

        for batch in batches:
            take = min(remaining, batch.quantity_left)
            batch.quantity_left -= take
            batch.quantity_sold  = (batch.quantity_sold or Decimal('0.00')) + take
            batch.status         = 'finished' if batch.quantity_left <= 0 else 'active'
            batch.save()

            total_cost += take * batch.unit_cost_price
            remaining  -= take
            if remaining == 0:
                break

        if remaining > 0:
            # Not enough stock to fulfill this line — rollback
            raise ValueError(f"Not enough stock to fulfill {product.name}")

        # Compute average cost and profit
        avg_cost     = (total_cost / qty).quantize(Decimal('0.01'))
        profit_each  = (unit_price - avg_cost).quantize(Decimal('0.01'))
        total_profit = profit_each * qty

        # Update the SaleItem with actual cost & profit
        sale_item.cost_price = avg_cost
        sale_item.profit     = total_profit
        sale_item.save()

        # Update ProductModel.quantity (subtract sold quantity)
        product.quantity -= qty
        product.save()

    # Deduct from student wallet / debt
    if Decimal(wallet.balance) >= total_amount:
        wallet.balance = Decimal(wallet.balance) - total_amount
    else:
        remainder = total_amount - Decimal(wallet.balance)
        wallet.balance = Decimal('0.00')
        wallet.debt = Decimal(wallet.debt) + remainder
    wallet.save()

    target_timezone = pytz_timezone('Africa/Lagos')

    localized_created_at = timezone.localtime(sale.created_at, timezone=target_timezone)

    formatted_time = localized_created_at.strftime(
        f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
    )

    log = f"""
                           <div class='text-white bg-secondary' style='padding:5px;'>
                           <p class=''>Order Placement: <a href={reverse('order_detail', kwargs={'pk': sale.id})}><b>New order of ₦{sale.total_amount}</b></a> placed for
                           <a href={reverse('student_detail', kwargs={'pk': sale.student.id})}><b>{sale.student.__str__().title()}</b></a>
                            by <a href={reverse('staff_detail', kwargs={'pk': sale.created_by.id})}><b>{sale.created_by.__str__().title()}</b></a>
                           <br><span style='float:right'>{formatted_time}</span>
                           </p>

                           </div>
                           """

    activity = ActivityLogModel.objects.create(log=log)
    activity.save()

    messages.success(request, 'Order saved successfully.')
    return redirect(reverse('place_order'))



@login_required
@permission_required("inventory.add_salemodel", raise_exception=True)
@transaction.atomic
def cafeteria_order_view(request):
    if request.method == 'GET':
        settings_obj = SchoolSettingModel.objects.last()
        context = {
            'settings': settings_obj,
            'products': ProductModel.objects.all(),
        }
        return render(request, 'inventory/sales/place_cafeteria_order.html', context)

    # --- POST: Process the sale ---
    pk = request.POST.get('student_id')
    if not pk:
        messages.error(request, 'Please Select a Student')
        return redirect(reverse('place_order'))
    student = get_object_or_404(StudentModel, pk=pk)
    wallet, _ = StudentWalletModel.objects.get_or_create(student=student)

    # Gather line-items
    idx = 0
    items = []
    total_amount = Decimal('0.00')
    total_items  = 0
    while True:
        pid = request.POST.get(f'products[{idx}][product_id]')
        qty = request.POST.get(f'products[{idx}][quantity]')
        if not pid or not qty:
            break
        product    = get_object_or_404(ProductModel, pk=pid)
        quantity   = int(qty)
        unit_price = product.price
        line_total = unit_price * quantity

        items.append((product, quantity, unit_price))
        total_amount += line_total
        total_items  += quantity
        idx += 1

    # Validate funds
    max_debt  = SchoolSettingModel.objects.first().max_student_debt
    available = wallet.balance + (max_debt - wallet.debt)
    if total_amount > available:
        return HttpResponseBadRequest('Insufficient funds or max debt exceeded')

    # Create Sale header
    sale = SaleModel.objects.create(
        student=student,
        total_amount=total_amount,
        total_items=total_items
    )
    try:
        created_by = UserProfileModel.objects.get(user=request.user).staff
        sale.created_by = created_by
        sale.save()
    except Exception:
        pass

    # Process each line with FIFO batch consumption
    for product, qty, unit_price in items:
        # Create a placeholder SaleItem
        sale_item = SaleItemModel.objects.create(
            sale=sale,
            product=product,
            quantity=qty,
            unit_price=unit_price,
            cost_price=Decimal('0.00'),
            profit=Decimal('0.00'),
            subtotal=unit_price * qty
        )

        # FIFO consume StockInModel.quantity_left, update quantity_sold
        remaining  = qty
        total_cost = Decimal('0.00')
        batches = StockInModel.objects.filter(
            product=product,
            quantity_left__gt=0
        ).order_by('date_added', 'created_at')

        for batch in batches:
            take = min(remaining, batch.quantity_left)
            batch.quantity_left -= take
            batch.quantity_sold  = (batch.quantity_sold or Decimal('0.00')) + take
            batch.status         = 'finished' if batch.quantity_left <= 0 else 'active'
            batch.save()

            total_cost += take * batch.unit_cost_price
            remaining  -= take
            if remaining == 0:
                break

        if remaining > 0:
            # Not enough stock to fulfill this line — rollback
            raise ValueError(f"Not enough stock to fulfill {product.name}")

        # Compute average cost and profit
        avg_cost     = (total_cost / qty).quantize(Decimal('0.01'))
        profit_each  = (unit_price - avg_cost).quantize(Decimal('0.01'))
        total_profit = profit_each * qty

        # Update the SaleItem with actual cost & profit
        sale_item.cost_price = avg_cost
        sale_item.profit     = total_profit
        sale_item.save()

        # Update ProductModel.quantity (subtract sold quantity)
        product.quantity -= qty
        product.save()

    # Deduct from student wallet / debt
    if Decimal(wallet.balance) >= total_amount:
        wallet.balance = Decimal(wallet.balance) - total_amount
    else:
        remainder = total_amount - Decimal(wallet.balance)
        wallet.balance = Decimal('0.00')
        wallet.debt = Decimal(wallet.debt) + remainder
    wallet.save()

    target_timezone = pytz_timezone('Africa/Lagos')

    localized_created_at = timezone.localtime(sale.created_at, timezone=target_timezone)

    formatted_time = localized_created_at.strftime(
        f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
    )

    log = f"""
                           <div class='text-white bg-secondary' style='padding:5px;'>
                           <p class=''>Order Placement: <a href={reverse('order_detail', kwargs={'pk': sale.id})}><b>New order of ₦{sale.total_amount}</b></a> placed for
                           <a href={reverse('student_detail', kwargs={'pk': sale.student.id})}><b>{sale.student.__str__().title()}</b></a>
                            by <a href={reverse('staff_detail', kwargs={'pk': sale.created_by.id})}><b>{sale.created_by.__str__().title()}</b></a>
                           <br><span style='float:right'>{formatted_time}</span>
                           </p>

                           </div>
                           """

    activity = ActivityLogModel.objects.create(log=log)
    activity.save()

    messages.success(request, 'Order saved successfully.')
    return redirect(reverse('place_order'))


@transaction.atomic
@login_required
@permission_required("inventory.add_salemodel", raise_exception=True)
def confirm_order_view(request, sale_id):
    sale = get_object_or_404(SaleModel, pk=sale_id)
    student = sale.student

    if request.method == 'POST':
        if sale.status != 'pending':
            messages.warning(request, f"Order is already {sale.status.capitalize()}. Cannot confirm.")
            return redirect(reverse('view_pending_orders'))

        wallet, _ = StudentWalletModel.objects.get_or_create(student=student)
        settings_obj = SchoolSettingModel.objects.first()

        # Convert wallet.balance and wallet.debt to Decimal for consistent calculations
        # This is where the conversion happens to prevent 'float' and 'Decimal' type errors.
        current_wallet_balance = Decimal(str(wallet.balance))
        current_wallet_debt = Decimal(str(wallet.debt))

        # Ensure max_debt is also a Decimal for consistent arithmetic
        max_debt = Decimal(str(settings_obj.max_student_debt)) if settings_obj and settings_obj.max_student_debt is not None else Decimal('0.00')

        # Validate funds (re-validation at confirmation)
        # All operands are now Decimal
        available_funds_including_debt_limit = current_wallet_balance + (max_debt - current_wallet_debt)

        if sale.total_amount > available_funds_including_debt_limit:
            messages.error(request, 'Insufficient funds or maximum debt limit exceeded to confirm this order.')
            return redirect(reverse('view_orders'))

        try:
            # Process each line with FIFO batch consumption
            # Using SaleItemModel.objects.filter(sale=sale) to get related items
            for sale_item in SaleItemModel.objects.filter(sale=sale):
                product = sale_item.product
                quantity_to_deduct = sale_item.quantity

                # Check if product is in stock (basic check first)
                if product.quantity < quantity_to_deduct:
                    raise ValueError(f"Insufficient stock for {product.name}. Only {product.quantity} available.")

                remaining_qty_for_item = quantity_to_deduct
                total_cost_for_item = Decimal('0.00')

                # FIFO consume StockInModel.quantity_left, update quantity_sold
                # Order by date_added and created_at to ensure true FIFO
                batches = StockInModel.objects.filter(
                    product=product,
                    quantity_left__gt=0
                ).order_by('date_added', 'created_at')

                for batch in batches:
                    take = min(remaining_qty_for_item, batch.quantity_left)
                    if take == 0:
                        continue # Skip if nothing to take from this batch

                    batch.quantity_left -= take
                    batch.quantity_sold = (batch.quantity_sold or Decimal('0.00')) + take
                    batch.status = 'finished' if batch.quantity_left <= 0 else 'active'
                    batch.save()

                    total_cost_for_item += take * batch.unit_cost_price
                    remaining_qty_for_item -= take

                    if remaining_qty_for_item <= 0:
                        break # Fulfilled current sale item

                if remaining_qty_for_item > 0:
                    # This should ideally be caught by product.quantity check above,
                    # but serves as a safeguard for edge cases with batch inconsistencies.
                    raise ValueError(f"Not enough stock batches to fulfill {product.name} quantity.")

                # Compute average cost and profit for the SaleItem
                # Ensure division by zero is handled if quantity_to_deduct is 0 (though validator should prevent)
                avg_cost_price_item = (total_cost_for_item / Decimal(str(quantity_to_deduct))).quantize(Decimal('0.01')) if quantity_to_deduct > 0 else Decimal('0.00')
                profit_each_item = (sale_item.unit_price - avg_cost_price_item).quantize(Decimal('0.01'))
                total_profit_item = profit_each_item * Decimal(str(quantity_to_deduct))

                # Update the SaleItem with actual cost & profit
                sale_item.cost_price = avg_cost_price_item
                sale_item.profit = total_profit_item
                sale_item.save()

                # Update ProductModel.quantity (subtract sold quantity)
                product.quantity -= quantity_to_deduct
                product.save()

            # Deduct from student wallet / update debt
            # Use the converted Decimal values for calculations
            if current_wallet_balance >= sale.total_amount:
                wallet.balance = float(current_wallet_balance - sale.total_amount) # Convert back to float for saving if model field is FloatField
            else:
                remainder = sale.total_amount - current_wallet_balance
                wallet.balance = 0.0 # Assign float zero
                wallet.debt = float(current_wallet_debt + remainder) # Convert back to float for saving if model field is FloatField
            wallet.save()

            # Update Sale Status to 'completed'
            sale.status = 'completed'
            sale.save()

            # Log confirmation activity
            localized_created_at = timezone.localtime(now(), timezone=pytz_timezone('Africa/Lagos'))
            formatted_time = localized_created_at.strftime(
                f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
            )
            staff = UserProfileModel.objects.get(user=request.user).staff
            sale_url = reverse('order_detail', kwargs={'pk': sale.pk})
            student_url = reverse('student_detail', kwargs={'pk': sale.student.pk})
            staff_url = reverse('staff_detail', kwargs={'pk': staff.pk}) if staff else '#'

            log = f"""
            <div class='text-white bg-success p-2' style='border-radius: 5px;'>
              <p>
                Order <a href="{sale_url}"><b>#{sale.pk}</b></a> for
                <a href="{student_url}"><b>{sale.student.__str__().title()}</b></a>
                was <b>confirmed</b> by
                <a href="{staff_url}"><b>{staff.__str__().title()}</b></a>.
                <br>
                <b>Total:</b> ₦{sale.total_amount:.2f}
                &nbsp; | &nbsp;
                <b>Time:</b> <span class="text-light">{formatted_time}</span>
                <span class='float-end'>{now().strftime('%Y-%m-%d %H:%M:%S')}</span>
              </p>
            </div>
            """

            ActivityLogModel.objects.create(
                log=log,
            )

            messages.success(request, f"Order #{sale.pk} confirmed successfully.")
            return redirect(reverse('view_orders')) # Redirect to student's order list

        except ValueError as e:
            # Catch specific errors during stock processing
            messages.error(request, f"Order confirmation failed: {e}")
            return redirect(reverse('view_orders'))
        except Exception as e:
            # Catch any other unexpected errors
            messages.error(request, f"An unexpected error occurred during order confirmation: {e}")
            return redirect(reverse('view_orders'))
    else:
        # For GET requests, you might want to display a confirmation page
        # or just redirect with a message indicating invalid method.
        messages.warning(request, "Invalid request method for confirming order.")
        return redirect(reverse('view_orders'))


# --- Cancel Order View ---

@login_required
@permission_required("inventory.add_salemodel", raise_exception=True)
@transaction.atomic
def cancel_order_view(request, sale_id):
    sale = get_object_or_404(SaleModel, pk=sale_id)
    if request.method == 'POST':
        if sale.status == 'pending':
            sale.status = 'cancelled'
            sale.save()

            # Log order cancellation
            localized_created_at = timezone.localtime(now(), timezone=pytz_timezone('Africa/Lagos'))
            formatted_time = localized_created_at.strftime(
                f"%B {localized_created_at.day}{get_day_ordinal_suffix(localized_created_at.day)} %Y %I:%M%p"
            )
            staff = UserProfileModel.objects.get(user=request.user).staff
            sale_url = reverse('order_detail', kwargs={'pk': sale.pk})
            student_url = reverse('student_detail', kwargs={'pk': sale.student.pk})
            staff_url = reverse('staff_detail', kwargs={'pk': staff.pk}) if staff else '#'

            log = f"""
            <div class='text-white bg-danger p-2' style='border-radius: 5px;'>
              <p>
                <b>Order Cancellation:</b> Order
                <a href="{sale_url}"><b>#{sale.pk}</b></a> for
                <a href="{student_url}"><b>{sale.student.__str__().title()}</b></a>
                was <b>cancelled</b> by
                <a href="{staff_url}"><b>{staff.__str__().title()}</b></a>.
                <br>
                <b>Time:</b> {formatted_time}
                <span class='float-end'>{now().strftime('%Y-%m-%d %H:%M:%S')}</span>
              </p>
            </div>
            """

            ActivityLogModel.objects.create(
                log=log,
            )

            messages.success(request, f"Order #{sale.pk} has been cancelled.")
            return redirect(reverse('view_pending_orders'))
        else:
            messages.warning(request, f"Order is already {sale.status.capitalize()}. Cannot cancel.")
            return redirect(reverse('view_pending_orders'))
    else:
        messages.warning(request, "Invalid request method for cancelling order.")
        return redirect(reverse('view_pending_orders'))


@login_required
@permission_required("inventory.view_salemodel", raise_exception=True)
def view_orders(request):
    # (You can add filtering, pagination, etc.)
    orders = SaleModel.objects.select_related('student').exclude(status='pending')
    return render(request, 'inventory/sales/index.html', {
        'orders': orders,
    })

@login_required
@permission_required("inventory.view_salemodel", raise_exception=True)
def view_pending_orders(request):
    # (You can add filtering, pagination, etc.)
    orders = SaleModel.objects.select_related('student').filter(status='pending')
    return render(request, 'inventory/sales/pending.html', {
        'orders': orders,
    })


@login_required
@permission_required("inventory.view_salemodel", raise_exception=True)
def order_detail(request, pk):
    sale = get_object_or_404(SaleModel, pk=pk)
    items = sale.saleitemmodel_set.select_related('product')
    # Compute total profit here
    total_profit = sum(item.profit for item in items)
    return render(request, 'inventory/sales/detail.html', {
        'sale': sale,
        'items': items,
        'total_profit': total_profit,
    })
