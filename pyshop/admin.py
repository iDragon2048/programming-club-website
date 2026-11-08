from django.contrib import admin
from.models import Profile, Product, CartItem, OrderItem, ProductCustomAttribute, ProductOption, OrderItemAttribute, CartItemAttribute

# Register your models here.
# This lets you edit attributes directly inside the Product page
class ProductAttributeInline(admin.TabularInline):
    # Remove ".objects" — go straight from Product to attributes
    model = Product.attributes.through
    extra = 1

class OrderItemAttributeInline(admin.TabularInline):
    model = OrderItemAttribute
    extra = 1  # <-- CHANGE THIS TO 1
    # We will temporarily comment out readonly_fields just so it shows a blank editable row
    readonly_fields = ('name', 'input_type', 'text_value', 'number_value', 'file_value')

# @admin.register(Product)
# class ProductAdmin(admin.ModelAdmin):
#     list_display = ('name', 'price')
#     # This turns the multi-select into the dual-box "Available vs Chosen" widget
#     filter_horizontal = ('attributes',)

@admin.register(ProductCustomAttribute)
class ProductCustomAttributeAdmin(admin.ModelAdmin):
    # This adds a sidebar filter so you can view all "Color" or all "Size" values
    list_display = ('name', 'value')
    list_filter = ('name',)

@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'selected_attributes')
    # Makes the JSON dictionary read-only so you don't accidentally break the format
    readonly_fields = ('selected_attributes',)

@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ('user', 'product', 'quantity', 'timestamp')
    readonly_fields = ('selected_attributes', 'timestamp')
    inlines = [OrderItemAttributeInline]

@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance')

# 1. Register the standalone options model so you can create them
@admin.register(ProductOption)
class ProductOptionAdmin(admin.ModelAdmin):
    list_display = ('name', 'input_type')

# 2. Update your ProductAdmin
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ('name', 'price')
    # Just add 'options' right next to 'attributes'!
    filter_horizontal = ('attributes', 'options')

@admin.register(CartItemAttribute)
class CartItemAttributeAdmin(admin.ModelAdmin):
    list_display = ('cart_item', 'option', 'text_value', 'file_value')

@admin.register(OrderItemAttribute)
class OrderItemAttributeAdmin(admin.ModelAdmin):
    list_display = ('order_item', 'name', 'input_type')