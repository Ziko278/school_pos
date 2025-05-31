from decimal import Decimal

from django.db import models
from django.db.models import Sum
from django.utils import timezone
from django.core.validators import MinValueValidator

from admin_site.models import SessionModel, SchoolSettingModel
from human_resource.models import StaffModel
from student.models import StudentModel


class CategoryModel(models.Model):
    """
    Represents a category for products (e.g., 'Electronics', 'Apparel', 'Beverages').
    """
    name = models.CharField(max_length=100, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']

    def __str__(self):
        return self.name


class ProductModel(models.Model):
    category = models.ForeignKey(CategoryModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    barcode = models.CharField(max_length=100, unique=True, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantity = models.IntegerField(default=0, validators=[MinValueValidator(0)], blank=True)
    reorder_level = models.IntegerField(default=10, validators=[MinValueValidator(0)])
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return f"{self.name} ({self.category.name})"


class SupplierModel(models.Model):
    """
    Represents a supplier of products.
    """
    name = models.CharField(max_length=200, unique=True)
    products = models.ManyToManyField(ProductModel, blank=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    address = models.CharField(max_length=250, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class PriceHistoryModel(models.Model):
    """
    Keeps a historical record of product price changes.
    Useful for reporting and understanding pricing strategies.
    """
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='price_history')
    old_price = models.DecimalField(max_digits=10, decimal_places=2)
    new_price = models.DecimalField(max_digits=10, decimal_places=2)
    change_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-change_date']
        verbose_name_plural = "Price History"

    def __str__(self):
        return f"{self.product.name}: {self.old_price} -> {self.new_price} on {self.change_date.date()}"


class StockInModel(models.Model):
    """
    Records a single instance of stock being added for a product.
    """
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE, related_name='stock_ins')

    # Use DecimalField for quantities and monetary values
    quantity_added = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    quantity_left = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    quantity_sold = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    quantity_stocked_out = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True, default=0)
    unit_cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])

    date_added = models.DateField(default=timezone.now)  # Date when stock was added
    status = models.CharField(max_length=10, default='active', blank=True)
    created_at = models.DateTimeField(auto_now_add=True)  # When this record was created
    created_by = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, null=True, blank=True)  # Who added it

    class Meta:
        verbose_name = "Stock In Record"
        verbose_name_plural = "Stock In Records"
        ordering = ['-date_added', '-created_at']

    def __str__(self):
        return f"Added {self.quantity_added} of {self.product.name} @ {self.unit_cost_price}"

    @property
    def total_cost_price(self):
        """Calculates the total cost for this specific stock-in entry."""
        return self.quantity_added * self.unit_cost_price

    def save(self, *args, **kwargs):
        if not self.pk:
            self.quantity_left = self.quantity_added

            # Check if quantity_left is zero to update status
            # IMPORTANT: Use assignment operator '=' instead of comparison '=='
        if self.quantity_left <= Decimal('0.00'):
            self.status = 'finished'
        else:
            self.status = 'active'

        super(StockInModel, self).save(*args, **kwargs)


class StockInSummaryModel(models.Model):
    """
    Represents a summary or header for a collection of StockInModel records.
    This allows tracking different products stocked together in one receiving event.
    """
    # The ManyToManyField here correctly links to individual StockInModel records.
    products = models.ManyToManyField(StockInModel, blank=True,
                                      help_text="Individual stock-in records included in this summary.")

    date = models.DateField(default=timezone.now, help_text="The overall date of this stock-in summary.")
    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this summary record was created.")
    created_by = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, null=True, blank=True,
                                   help_text="Staff member who created this summary.")

    class Meta:
        verbose_name = "Stock In Summary"
        verbose_name_plural = "Stock In Summaries"
        ordering = ['-date', '-created_at']

    def __str__(self):
        # Ensure total_summary_cost is used, and handle potential None if no products
        return f"{self.products.count()} products worth ₦{self.total_summary_cost or Decimal('0.00')}"

    @property
    def total_summary_cost(self):
        """Calculates the total cost for all products linked to this summary."""
        # Sums the total_cost_price from all related StockInModel instances
        return sum(product_in.total_cost_price for product_in in self.products.all())


class StockOutModel(models.Model):
    """
    Records stock removal for reasons other than sales (e.g., damage, internal use, write-off).
    The cost of removed stock will be calculated based on available StockInModel records.
    """
    stock = models.ForeignKey(StockInModel, on_delete=models.CASCADE, related_name='stock_outs')

    # Use DecimalField for quantities
    quantity_removed = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(Decimal('0.01'))], help_text="Quantity of product removed.")

    # This field will store the calculated cost of the removed stock.
    # It should be populated in the view/signal logic, not directly by user input.
    cost_of_removed_stock = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Calculated cost of the stock removed based on costing method.")

    reason = models.TextField(help_text="Why was this stock removed (e.g., 'Damaged', 'Internal Use', 'Lost').")  # Made reason required

    date_removed = models.DateField(default=timezone.now, blank=True, help_text="The date this stock was physically removed.")  # Date when stock was removed

    created_at = models.DateTimeField(auto_now_add=True, help_text="Timestamp when this record was created.")  # When this record was created
    created_by = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, null=True, blank=True, help_text="Staff member who recorded this stock out.")  # Who removed it

    class Meta:
        verbose_name = "Stock Out Record"
        verbose_name_plural = "Stock Out Records"
        ordering = ['-date_removed', '-created_at']

    def __str__(self):
        return f"Removed {self.quantity_removed} of {self.product.name} - Reason: {self.reason[:50]}"

    def save(self, *args, **kwargs):
        """
        Automatically calculates the 'cost_of_removed_stock' before saving.
        It multiplies 'quantity_removed' by the 'cost_price' of the associated 'StockInModel'.
        """
        # Ensure both 'stock' object is loaded and 'quantity_removed' is set
        if self.stock and self.quantity_removed is not None:
            # Access the cost_price from the related StockInModel instance
            # We assume StockInModel has a DecimalField named 'cost_price'
            if hasattr(self.stock, 'unit_cost_price') and self.stock.unit_cost_price is not None:
                self.cost_of_removed_stock = self.quantity_removed * self.stock.unit_cost_price
            else:
                # Handle cases where the cost_price might be missing or not set on StockInModel
                self.cost_of_removed_stock = Decimal('0.00')  # Default to 0 or raise an error
        else:
            # If 'stock' or 'quantity_removed' isn't available, default cost to 0
            self.cost_of_removed_stock = Decimal('0.00')

        super().save(*args, **kwargs)


class SaleModel(models.Model):
    """
    Represents a single completed transaction (e.g., a customer's purchase).
    """
    SALE_STATUS_CHOICES = [
        ('completed', 'Completed'),
        ('pending', 'Pending'),
        ('refunded', 'Refunded'),
        ('cancelled', 'Cancelled'),
    ]
    transaction_id = models.CharField(max_length=50, unique=True, blank=True) # Auto-generated or unique identifier
    sale_date = models.DateTimeField(default=timezone.now)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    total_items = models.IntegerField(default=0, validators=[MinValueValidator(0)])
    student = models.ForeignKey(StudentModel, on_delete=models.SET_NULL, null=True, blank=True) # Optional customer
    status = models.CharField(max_length=20, choices=SALE_STATUS_CHOICES, default='completed')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    session = models.ForeignKey(SessionModel, on_delete=models.SET_NULL, null=True, blank=True)
    created_by = models.ForeignKey(StaffModel, on_delete=models.SET_NULL, null=True, blank=True)  # Who added it
    TERM = (
        ('1st term', '1st TERM'), ('2nd term', '2nd TERM'), ('3rd term', '3rd TERM')
    )
    term = models.CharField(max_length=10, choices=TERM, null=True, blank=True)

    class Meta:
        ordering = ['-sale_date']
        verbose_name_plural = "Sales"

    def __str__(self):
        return f"Sale #{self.transaction_id or self.pk} - {self.sale_date.strftime('%Y-%m-%d %H:%M')}"

    def save(self, *args, **kwargs):
        if not self.transaction_id:
            # Generate a simple transaction ID. More robust methods might use UUIDs or sequential numbers with prefixes.
            self.transaction_id = f"SALE-{timezone.now().strftime('%Y%m%d%H%M%S')}-{self.pk or 'NEW'}"
        if not self.session or not self.term:
            setting = SchoolSettingModel.objects.first()
            self.session = setting.session
            self.term = setting.term

        super().save(*args, **kwargs)
        # Update related inventory quantities after sale
        # This part is usually handled in a transaction, perhaps in a service layer or view
        # For simplicity, if items are added directly, you might trigger it here.
        # However, for robustness, it's often better to handle inventory updates explicitly
        # in the view logic that creates the Sale and SaleItem instances.


class SaleItemModel(models.Model):
    """
    Represents a single product line item within a Sale.
    """
    sale = models.ForeignKey(SaleModel, on_delete=models.CASCADE)
    product = models.ForeignKey(ProductModel, on_delete=models.CASCADE) # Assuming 'products' is the app name
    quantity = models.IntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)]) # Price at time of sale
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)]) # quantity * unit_price
    cost_price = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    profit = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])

    class Meta:
        unique_together = ('sale', 'product') # A product appears only once per sale item
        verbose_name = "Sale Item"
        verbose_name_plural = "Sale Items"

    def __str__(self):
        return f"{self.quantity} x {self.product.name} in Sale #{self.sale.transaction_id or self.sale.pk}"

    def save(self, *args, **kwargs):
        self.subtotal = self.quantity * self.unit_price
        self.profit = (self.unit_price - self.cost_price) * self.quantity
        super().save(*args, **kwargs)


class ReturnModel(models.Model):
    """
    Records product returns.
    """
    RETURN_REASON_CHOICES = [
        ('damaged', 'Damaged Product'),
        ('wrong_item', 'Wrong Item Shipped/Purchased'),
        ('customer_changed_mind', 'Customer Changed Mind'),
        ('defective', 'Defective Product'),
        ('other', 'Other'),
    ]

    sale = models.ForeignKey(SaleModel, on_delete=models.CASCADE, related_name='returns')
    product = models.ForeignKey('ProductModel', on_delete=models.CASCADE)
    quantity_returned = models.IntegerField(validators=[MinValueValidator(1)])
    return_date = models.DateTimeField(default=timezone.now)
    reason = models.CharField(max_length=50, choices=RETURN_REASON_CHOICES, default='customer_changed_mind')
    refund_amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.00)])
    notes = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Returns"
        ordering = ['-return_date']

    def __str__(self):
        return f"Return for Sale #{self.sale.transaction_id or self.sale.pk} - {self.product.name} ({self.quantity_returned})"

    def save(self, *args, **kwargs):
        # Ensure refund_amount is calculated or provided
        if not self.refund_amount:
            # Simple calculation, could be more complex with taxes/discounts
            self.refund_amount = self.product.price * self.quantity_returned
        super().save(*args, **kwargs)
