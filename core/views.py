from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from .forms import *
from .models import *
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden
from django.db.models import Q
from .forms import UserUpdateForm, UserProfileUpdateForm


def home(request):
    query = request.GET.get('q', '')
    category_id = request.GET.get('category', '')
    min_price = request.GET.get('min_price', '')
    max_price = request.GET.get('max_price', '')

    products = Product.objects.all()

    if query:
        products = products.filter(name__icontains=query)

    if category_id:
        products = products.filter(category__id=category_id)

    if min_price:
        products = products.filter(price__gte=min_price)

    if max_price:
        products = products.filter(price__lte=max_price)

    categories = Category.objects.all()

    role = None
    if request.user.is_authenticated:
        role = request.user.userprofile.role

    return render(request, 'core/home.html', {
        'products': products,
        'categories': categories,
        'query': query,
        'selected_category': category_id,
        'min_price': min_price,
        'max_price': max_price,
        'role': role,
    })



def register_view(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            user.set_password(form.cleaned_data['password'])
            user.save()
            role = form.cleaned_data['role']
            profile = user.userprofile
            profile.role = role
            profile.save()
            return redirect('login')
    else:
        form = UserRegistrationForm()
    return render(request, 'core/register.html', {'form': form})

def login_view(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(username=username, password=password)
        if user:
            login(request, user)
            return redirect('home')
    return render(request, 'core/login.html')

def logout_view(request):
    logout(request)
    return redirect('login')

@login_required
def dashboard_view(request):
    role = request.user.userprofile.role
    return render(request, 'core/dashboard.html', {'role': role})


# Vendor Product List
@login_required
def vendor_products(request):
    if request.user.userprofile.role != 'vendor':
        return HttpResponseForbidden()
    products = Product.objects.filter(vendor=request.user)
    return render(request, 'core/vendor_products.html', {'products': products})

# Add Product
@login_required
def add_product(request):
    if request.user.userprofile.role != 'vendor':
        return HttpResponseForbidden()
    
    if request.method == 'POST':
        form = ProductForm(request.POST, request.FILES)
        if form.is_valid():
            product = form.save(commit=False)
            product.vendor = request.user
            product.save()
            return redirect('vendor_products')
    else:
        form = ProductForm()
    
    return render(request, 'core/add_product.html', {'form': form})

# Edit Product
@login_required
def edit_product(request, pk):
    product = Product.objects.get(pk=pk)
    if product.vendor != request.user:
        return HttpResponseForbidden()
    
    form = ProductForm(request.POST or None, request.FILES or None, instance=product)
    if form.is_valid():
        form.save()
        return redirect('vendor_products')
    
    return render(request, 'core/edit_product.html', {'form': form})

# Delete Product
@login_required
def delete_product(request, pk):
    product = Product.objects.get(pk=pk)
    if product.vendor != request.user:
        return HttpResponseForbidden()
    product.delete()
    return redirect('vendor_products')



# Cart 
@login_required
def add_to_cart(request, product_id):
    product = Product.objects.get(id=product_id)
    cart_item, created = Cart.objects.get_or_create(user=request.user, product=product)
    if not created:
        cart_item.quantity += 1
    cart_item.save()
    return redirect('view_cart')

@login_required
def view_cart(request):
    cart_items = Cart.objects.filter(user=request.user)
    total = sum(item.total_price() for item in cart_items)

    discount = 0
    final_total = total
    coupon_code = ''

    if request.method == 'POST':
        coupon_code = request.POST.get('coupon_code', '').strip()
        try:
            coupon = Coupon.objects.get(code__iexact=coupon_code, active=True)
            discount = total * (coupon.discount / 100)
            final_total = total - discount
        except Coupon.DoesNotExist:
            discount = 0
            final_total = total

    return render(request, 'core/cart.html', {
        'cart_items': cart_items,
        'total': total,
        'discount': discount,
        'final_total': final_total,
        'coupon_code': coupon_code
    })

@login_required
def remove_from_cart(request, cart_id):
    cart_item = Cart.objects.get(id=cart_id, user=request.user)
    cart_item.delete()
    return redirect('view_cart')



# Checkout Views
@login_required
def checkout(request):
    cart_items = Cart.objects.filter(user=request.user)
    if not cart_items.exists():
        return redirect('view_cart')

    total = sum(item.total_price() for item in cart_items)

    order = Order.objects.create(user=request.user, total=total, status='Pending')

    for item in cart_items:
        OrderItem.objects.create(
            order=order,
            product=item.product,
            quantity=item.quantity,
            price=item.product.price
        )

        # Reduce product stock
        item.product.stock -= item.quantity
        item.product.save()

    cart_items.delete()  # Clear cart

    return redirect('payment_success')

def payment_success(request):
    return render(request, 'core/payment_success.html')



# Order History
@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    reviewed_products = Review.objects.filter(customer=request.user).values_list('product_id', flat=True)
    return render(request, 'core/order_history.html', {
        'orders': orders,
        'reviewed_products': reviewed_products,
    })


# Vendor Orders
@login_required
def vendor_orders(request):
    if request.user.userprofile.role != 'vendor':
        return redirect('dashboard')

    # Get products created by this vendor
    vendor_products = Product.objects.filter(vendor=request.user)

    # Get OrderItems related to vendor's products
    order_items = OrderItem.objects.filter(
        product__in=vendor_products
    ).select_related('order', 'product')

    return render(request, 'core/vendor_orders.html', {
        'order_items': order_items,
        'ORDER_STATUS': ORDER_STATUS,  # Pass status choices to the template
    })


# Update Order Status
from django.views.decorators.http import require_POST

@require_POST
@login_required
def update_order_status(request, order_id):
    if request.user.userprofile.role != 'vendor':
        return redirect('dashboard')

    new_status = request.POST.get('status')

    if not new_status:  # Prevent saving a blank status
        return redirect('vendor_orders')

    try:
        order = Order.objects.get(id=order_id)

        vendor_products = Product.objects.filter(vendor=request.user)
        if OrderItem.objects.filter(order=order, product__in=vendor_products).exists():
            order.status = new_status
            order.save()
    except Order.DoesNotExist:
        pass

    return redirect('vendor_orders')



@login_required
def edit_profile(request):
    user_form = UserUpdateForm(instance=request.user)
    profile_form = UserProfileUpdateForm(instance=request.user.userprofile)

    if request.method == 'POST':
        user_form = UserUpdateForm(request.POST, instance=request.user)
        profile_form = UserProfileUpdateForm(request.POST, instance=request.user.userprofile)

        if user_form.is_valid() and profile_form.is_valid():
            user_form.save()
            profile_form.save()
            return redirect('dashboard')

    return render(request, 'core/edit_profile.html', {
        'user_form': user_form,
        'profile_form': profile_form,
    })



@login_required
def leave_review(request, product_id):
    product = get_object_or_404(Product, id=product_id)

    # Make sure customer has ordered and it's delivered
    has_ordered = OrderItem.objects.filter(
        order__user=request.user,
        order__status='Delivered',
        product=product
    ).exists()

    if not has_ordered:
        return redirect('order_history')

    # Prevent duplicate review
    if Review.objects.filter(customer=request.user, product=product).exists():
        return redirect('order_history')

    if request.method == 'POST':
        form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.customer = request.user
            review.product = product
            review.save()
            return redirect('order_history')
    else:
        form = ReviewForm()

    return render(request, 'core/leave_review.html', {
        'form': form,
        'product': product
    })


def product_detail(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    reviews = Review.objects.filter(product=product).order_by('-created_at')

    return render(request, 'core/product_detail.html', {
        'product': product,
        'reviews': reviews,
    })