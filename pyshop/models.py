from django.contrib.auth.models import User
from django.db import models
from datetime import datetime

# Create your models here.
class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    balance = models.IntegerField(default=0)
    codewars_username = models.CharField(max_length=100, blank=True, null=True)
    is_verified_member = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username + "'s profile"

class ProductCustomAttribute(models.Model):
    name = models.CharField(max_length=50, help_text="e.g., Color, Size, Material")
    value = models.CharField(max_length=50, help_text="e.g., Red, XL, Cotton")

    class Meta:
        # This prevents creating duplicate attributes like two "Color: Red" entries
        unique_together = ('name', 'value')

    def __str__(self):
        # This makes it readable in the Django Admin and forms
        return f"{self.name}: {self.value}"



# models.py
class ProductOption(models.Model):
    name = models.CharField(max_length=50) # e.g., "Engraving Text", "Age", "Custom Logo"

    # The drop-down choices for YOU in the admin panel
    TYPE_CHOICES = [
        ('text', 'Text String'),
        ('number', 'Number'),
        ('file', 'File Upload'),
    ]
    input_type = models.CharField(max_length=10, choices=TYPE_CHOICES)

    def __str__(self):
        return f"{self.name} - {self.name} ({self.input_type})"

class Product(models.Model):
    name = models.CharField(max_length=100)
    price = models.IntegerField()
    description = models.TextField()
    image = models.ImageField(upload_to="images/", null=True, blank=True)
    attributes = models.ManyToManyField(ProductCustomAttribute, blank=True, related_name='products')
    options = models.ManyToManyField(ProductOption, blank=True, related_name='products')

    def __str__(self):
        return self.name

class CartItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    selected_attributes = models.JSONField(default=dict)

    @property
    def total_price(self):
        return self.quantity * self.product.price

class OrderItem(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.IntegerField(default=1)
    timestamp = models.DateTimeField(auto_now_add=True)
    selected_attributes = models.JSONField(default=dict)

    def __str__(self):
        return f"{self.user}-{self.product}-{self.timestamp.strftime("%c")}"

    @property
    def total_price(self):
        return self.quantity * self.product.price

class CartItemAttribute(models.Model):
    cart_item = models.ForeignKey(CartItem, on_delete=models.CASCADE, related_name='custom_attributes')
    option = models.ForeignKey(ProductOption, on_delete=models.CASCADE)

    # We create a column for every data type, but we ONLY fill one!
    text_value = models.CharField(max_length=255, blank=True, null=True)
    number_value = models.FloatField(blank=True, null=True)
    file_value = models.FileField(upload_to='customer_uploads/', blank=True, null=True)

    @property
    def get_value(self):
        """This smart property checks the required type and returns the correct data."""
        if self.option.input_type == 'text':
            return self.text_value
        elif self.option.input_type == 'number':
            return self.number_value
        elif self.option.input_type == 'file':
            return self.file_value
        return None

# models.py
class OrderItemAttribute(models.Model):
    order_item = models.ForeignKey(OrderItem, on_delete=models.CASCADE, related_name='custom_attributes')

    # We save these as plain text so the receipt is permanent
    name = models.CharField(max_length=50)
    input_type = models.CharField(max_length=10)

    # The EAV values
    text_value = models.CharField(max_length=255, blank=True, null=True)
    number_value = models.FloatField(blank=True, null=True)
    file_value = models.FileField(upload_to='customer_uploads/orders/', blank=True, null=True)

    @property
    def get_value(self):
        if self.input_type == 'text':
            return self.text_value
        elif self.input_type == 'number':
            return self.number_value
        elif self.input_type == 'file':
            return self.file_value
        return None


