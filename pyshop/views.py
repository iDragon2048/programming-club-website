from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from .models import Profile, Product, CartItem, OrderItem, CartItemAttribute, OrderItemAttribute, ProductOption
from django.core.mail import send_mail
from django.conf import settings # To grab your default email

# Create your views here.
@login_required
def home(request):
    products = Product.objects.all()
    return render(request, 'pyshop/home.html', {'products': products})

@login_required
def product_detail(request, pk):
    product = get_object_or_404(Product.objects.prefetch_related('attributes'), id=pk)
    return render(request, 'pyshop/product_detail.html', {'product': product})

@login_required
def add_to_cart(request, pk):
    product = get_object_or_404(Product, pk=pk)

    # Get quantity from the <input name="quantity">
    # Use .get() to avoid errors if the field is somehow missing
    qty_to_add = int(request.POST.get('quantity', 1))

    # get attributes in a dict
    attr_dict = {}
    for key, value in request.POST.items():
        if key.startswith("attribute_"):
            key = key[10:]
            attr_dict[key] = value

    # We use get_or_create to find the item or make a new one
    cart_item, created = CartItem.objects.get_or_create(
        product=product,
        user=request.user,
        selected_attributes = attr_dict,
        defaults={'quantity': qty_to_add}  # If NEW, use the form value
    )

    if not created:
        # If ALREADY EXISTS, add the new quantity to the old one
        cart_item.quantity += qty_to_add
        cart_item.save()

    for option in product.options.all():
        input_name = f'custom_attr_{option.id}'

        # Check if the user submitted text/number for this option
        if input_name in request.POST:
            value = request.POST[input_name]

            if option.input_type == 'text':
                CartItemAttribute.objects.create(cart_item=cart_item, option=option, text_value=value)
            elif option.input_type == 'number':
                CartItemAttribute.objects.create(cart_item=cart_item, option=option, number_value=float(value))

        # Check if the user uploaded a file for this option
        elif input_name in request.FILES:
            file_value = request.FILES[input_name]
            CartItemAttribute.objects.create(cart_item=cart_item, option=option, file_value=file_value)

    return redirect('shop')

@login_required
def view_cart(request):
    total = 0
    user_cart = CartItem.objects.filter(user=request.user)
    for cartitem in user_cart:
        total += cartitem.total_price

    return render(request, 'pyshop/cart.html', {"cart_items": user_cart, "total_price": total})

@login_required
def remove_from_cart(request, pk):
    item = get_object_or_404(CartItem, id=pk, user=request.user)
    item.delete()
    messages.success(request, 'Item removed from cart')
    return redirect('cart')

# @login_required
# def checkout(request):
#     total = 0
#     # user_cart = CartItem.objects.filter(user=request.user)
#     user_cart = CartItem.objects.filter(user=request.user).select_related('product')
#     for cartitem in user_cart:
#         total += cartitem.total_price

#     if request.user.profile.balance < total:
#         messages.error(request, 'You do not have enough Pytokens!')
#         return redirect('shop')
#     else:
#         request.user.profile.balance -= total
#         request.user.profile.save()
#         for cartitem in user_cart:
#             order_item = OrderItem(
#                 product=cartitem.product,
#                 user=request.user,
#                 quantity=cartitem.quantity,
#                 selected_attributes=cartitem.selected_attributes
#                 )
#             order_item.save()
#         subject = 'Your PyShop Receipt'
#         message = f'Hi {request.user.username},\n\nThanks for your purchase! Your order has been processed.'
#         recipient_list = [request.user.email] # Assumes the user has an email saved in their profile
#         owner_subject = 'PyShop Order Placed'
#         owner_message = f"{request.user.username} has made an order of {len(user_cart)} items."
#         owner_mail = ["kececioglue@awty.org"]
#         user_cart.delete()

#         # 2. Send it!
#         try:
#             send_mail(
#                 subject,
#                 message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 recipient_list,
#                 fail_silently=False, # Set to False so Django throws an error if it fails (good for debugging)
#             )
#             send_mail(
#                 owner_subject,
#                 owner_message,
#                 settings.DEFAULT_FROM_EMAIL,
#                 owner_mail,
#                 fail_silently=False, # Set to False so Django throws an error if it fails (good for debugging)
#             )
#             messages.success(request, "Checkout complete! A receipt has been emailed to you.")
#         except Exception as e:
#             messages.warning(request, "Checkout complete, but we couldn't send the receipt email.")
#             print(f"Email failed: {e}")
#         return redirect('shop')

@login_required
def checkout(request):
    # Fetch the cart
    user_cart = CartItem.objects.filter(user=request.user).select_related('product')

    # 1. Prevent checking out an empty cart!
    if not user_cart.exists():
        messages.warning(request, "Your cart is empty!")
        return redirect('shop')

    # 2. Calculate total
    total = sum(item.total_price for item in user_cart)

    # 3. Check balance
    if request.user.profile.balance < total and not request.user.is_superuser:
        messages.error(request, 'You do not have enough Pytokens!')
        return redirect('shop')

    # 4. Process the Order
    request.user.profile.balance -= total
    request.user.profile.save()

    # for cartitem in user_cart:
    #     OrderItem.objects.create(
    #         product=cartitem.product,
    #         user=request.user,
    #         quantity=cartitem.quantity,
    #         selected_attributes=cartitem.selected_attributes
    #     )

    # For Emails
    receipt = []

    for cartitem in user_cart:
        text_item = str(cartitem.quantity) + "x " + str(cartitem.product.name)

        # 1. Create the Order Item
        order_item = OrderItem.objects.create(
            product=cartitem.product,
            user=request.user,
            quantity=cartitem.quantity,
            selected_attributes=cartitem.selected_attributes
        )

        # 2. Copy the dynamic attributes (text, numbers, AND files!)
        for attr in cartitem.custom_attributes.all():
            OrderItemAttribute.objects.create(
                order_item=order_item,
                name=attr.option.name,         # Save the name permanently
                input_type=attr.option.input_type, # Save the type permanently
                text_value=attr.text_value,
                number_value=attr.number_value,
                file_value=attr.file_value     # Django automatically handles transferring the file link!
            )
            text_item = f"{text_item} - {attr.option.name}: {attr.text_value if attr.option.input_type == 'text' else str(attr.number_value) if attr.option.input_type == 'number' else str(attr.file_value)}"
        receipt.append(text_item)



    # Save the length before we delete the cart!
    item_count = len(user_cart)
    user_cart.delete()

    # 5. Prepare Emails
    subject = 'Your PyShop Receipt'
    message = f'''Hi {request.user.username},\n\nThanks for your purchase! Your order has been processed.
    '''
    recipient_list = [request.user.email]

    owner_subject = 'PyShop Order Placed'
    owner_message = f'''{request.user.username} has made an order of {item_count} items:
        '''
    for item in receipt:
        message = message + "\n" + item
        owner_message = owner_message + "\n" + item
    owner_mail = ["kececioglue@awty.org"] # <-- Fixed: Now a list!
    owner_labeled_mail = ["kececioglue+pythonclub@awty.org"]

    # 6. Send Emails
    try:
        # Email to User
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            recipient_list,
            fail_silently=False,
        )
        # Email to Owner
        send_mail(
            owner_subject,
            owner_message,
            settings.DEFAULT_FROM_EMAIL,
            owner_labeled_mail,
            fail_silently=False,
        )
        messages.success(request, "Checkout complete! A receipt has been emailed to you.")

    except Exception as e:
        messages.warning(request, "Checkout complete, but we couldn't send the receipt email.")
        print(f"Email failed: {e}")

    return redirect('shop')

@login_required
def update_cart_item(request, pk):
    if request.method == 'POST':
        cart_item = get_object_or_404(CartItem, id=pk, user=request.user)
        new_qty = int(request.POST.get('quantity'))

        if new_qty > 0:
            cart_item.quantity = new_qty  # We OVERWRITE here, no +=
            cart_item.save()
        else:
            cart_item.delete()  # Clean up if they set it to 0

    return redirect('cart')