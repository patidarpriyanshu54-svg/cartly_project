from django.shortcuts import render, redirect, get_object_or_404
from django.core.mail import send_mail
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import authenticate, login as auth_login
from .models import Product, Category, Cart, CartItem, Order, OrderItem, Wishlist, Review, RefundDetail
from .forms import ReviewForm


def home(request):
    products = Product.objects.all()
    categories = Category.objects.all()

    query = request.GET.get('q')
    category_slug = request.GET.get('category')

    if query:
        products = products.filter(name__icontains=query)

    if category_slug:
        products = products.filter(category__slug=category_slug)

    wishlist_ids = []
    if request.user.is_authenticated:
        wishlist_ids = list(Wishlist.objects.filter(user=request.user).values_list('product_id', flat=True))

    context = {
        'products': products,
        'categories': categories,
        'query': query or '',
        'selected_category': category_slug or '',
        'wishlist_ids': wishlist_ids,
    }
    return render(request, 'home.html', context)


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug)
    reviews = product.reviews.all().order_by('-created_at')

    user_review = None
    if request.user.is_authenticated:
        user_review = reviews.filter(user=request.user).first()

    if request.method == 'POST' and request.user.is_authenticated:
        if user_review:
            form = ReviewForm(request.POST, instance=user_review)
        else:
            form = ReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.product = product
            review.user = request.user
            review.save()
            return redirect('product_detail', slug=product.slug)
    else:
        form = ReviewForm(instance=user_review)

    avg_rating = 0
    if reviews:
        avg_rating = sum(r.rating for r in reviews) / len(reviews)

    in_wishlist = False
    if request.user.is_authenticated:
        in_wishlist = Wishlist.objects.filter(user=request.user, product=product).exists()

    related_products = Product.objects.filter(category=product.category).exclude(id=product.id)[:4]

    context = {
        'product': product,
        'reviews': reviews,
        'form': form,
        'avg_rating': round(avg_rating, 1),
        'in_wishlist': in_wishlist,
        'related_products': related_products,
    }
    return render(request, 'product_detail.html', context)


@login_required
def add_to_cart(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    cart, created = Cart.objects.get_or_create(user=request.user)
    cart_item, created = CartItem.objects.get_or_create(cart=cart, product=product)
    if not created:
        cart_item.quantity += 1
        cart_item.save()
    return redirect('cart_detail')


@login_required
def cart_detail(request):
    cart, created = Cart.objects.get_or_create(user=request.user)
    return render(request, 'cart_detail.html', {'cart': cart})


@login_required
def remove_from_cart(request, item_id):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    cart_item.delete()
    return redirect('cart_detail')


@login_required
def update_cart_quantity(request, item_id, action):
    cart_item = get_object_or_404(CartItem, id=item_id, cart__user=request.user)
    if action == 'increase':
        cart_item.quantity += 1
        cart_item.save()
    elif action == 'decrease':
        cart_item.quantity -= 1
        if cart_item.quantity <= 0:
            cart_item.delete()
        else:
            cart_item.save()
    return redirect('cart_detail')


@login_required
def checkout(request):
    cart, created = Cart.objects.get_or_create(user=request.user)

    if not cart.items.exists():
        return redirect('cart_detail')

    if request.method == 'POST':
        full_name = request.POST.get('full_name')
        address = request.POST.get('address')
        city = request.POST.get('city')
        pincode = request.POST.get('pincode')
        phone = request.POST.get('phone')
        payment_method = request.POST.get('payment_method')

        all_in_stock = all(item.product.stock >= item.quantity for item in cart.items.all())
        initial_status = 'confirmed' if all_in_stock else 'pending'

        order = Order.objects.create(
            user=request.user,
            full_name=full_name,
            address=address,
            city=city,
            pincode=pincode,
            phone=phone,
            payment_method=payment_method,
            total_amount=cart.total_price(),
            status=initial_status,
        )

        for item in cart.items.all():
            OrderItem.objects.create(
                order=order,
                product=item.product,
                product_name=item.product.name,
                price=item.product.price,
                quantity=item.quantity,
            )
            item.product.stock -= item.quantity
            item.product.save()

        cart.items.all().delete()

        send_mail(
            subject=f'Cartly - Order #{order.id} Confirmed',
            message=(
                f'Hi {order.full_name},\n\n'
                f'Thank you for shopping with Cartly! Your order #{order.id} has been placed successfully.\n\n'
                f'Total Amount: ₹{order.total_amount}\n'
                f'Payment Method: {order.get_payment_method_display()}\n'
                f'Delivery Address: {order.address}, {order.city} - {order.pincode}\n'
                f'Estimated Delivery: {order.estimated_delivery().strftime("%d %b %Y")}\n\n'
                f'We will notify you once your order is shipped.\n\n'
                f'Thanks,\nTeam Cartly'
            ),
            from_email=None,
            recipient_list=[request.user.email] if request.user.email else [],
            fail_silently=True,
        )

        return redirect('order_success', order_id=order.id)

    return render(request, 'checkout.html', {'cart': cart, 'payment_choices': Order.PAYMENT_CHOICES})


@login_required
def order_success(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    return render(request, 'order_success.html', {'order': order})


@login_required
def order_history(request):
    orders = Order.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'order_history.html', {'orders': orders})


@login_required
def toggle_wishlist(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    wishlist_item, created = Wishlist.objects.get_or_create(user=request.user, product=product)
    if not created:
        wishlist_item.delete()
    return redirect(request.META.get('HTTP_REFERER', 'home'))


@login_required
def wishlist_view(request):
    items = Wishlist.objects.filter(user=request.user)
    return render(request, 'wishlist.html', {'items': items})


def about_us(request):
    return render(request, 'about_us.html')


@login_required
def cancel_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)
    if order.status in ['pending', 'confirmed']:
        order.status = 'cancelled'
        order.save()
    return redirect('order_history')


@login_required
def return_order(request, order_id):
    order = get_object_or_404(Order, id=order_id, user=request.user)

    if not order.can_return():
        return redirect('order_history')

    if request.method == 'POST':
        account_holder_name = request.POST.get('account_holder_name')
        account_number = request.POST.get('account_number')
        ifsc_code = request.POST.get('ifsc_code')
        phone = request.POST.get('phone')

        errors = []
        if not account_holder_name.replace(' ', '').isalpha():
            errors.append("Account holder name should only contain letters and spaces.")
        if not (account_number.isdigit() and len(account_number) == 14):
            errors.append("Account number must be exactly 14 digits.")
        if not (len(ifsc_code) == 11 and ifsc_code[:4].isalpha() and ifsc_code[4] == '0' and ifsc_code[5:].isalnum()):
            errors.append("Enter a valid 11-character IFSC code (e.g. SBIN0001234).")
        if not (phone.isdigit() and len(phone) == 10 and phone[0] in '6789'):
            errors.append("Enter a valid 10-digit mobile number.")

        if errors:
            return render(request, 'return_order.html', {'order': order, 'errors': errors})

        RefundDetail.objects.update_or_create(
            order=order,
            defaults={
                'account_holder_name': account_holder_name,
                'account_number': account_number,
                'ifsc_code': ifsc_code.upper(),
                'phone': phone,
            }
        )

        order.status = 'return_requested'
        order.save()
        return redirect('order_history')

    return render(request, 'return_order.html', {'order': order})


def is_staff_user(user):
    return user.is_authenticated and user.is_staff


def staff_login(request):
    if request.user.is_authenticated and request.user.is_staff:
        return redirect('dashboard')

    error = None
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and user.is_staff:
            auth_login(request, user)
            return redirect('dashboard')
        else:
            error = "Invalid credentials or you don't have staff access."

    return render(request, 'staff_login.html', {'error': error})


@user_passes_test(is_staff_user, login_url='staff_login')
def dashboard(request):
    orders = Order.objects.all().order_by('-created_at')
    total_orders = orders.count()
    total_revenue = sum(o.total_amount for o in orders if o.status != 'cancelled')
    return render(request, 'dashboard.html', {
        'orders': orders,
        'total_orders': total_orders,
        'total_revenue': total_revenue,
    })


@user_passes_test(is_staff_user, login_url='staff_login')
def update_order_status(request, order_id, new_status):
    order = get_object_or_404(Order, id=order_id)
    valid_statuses = ['pending', 'confirmed', 'shipped', 'delivered', 'returned']
    if new_status in valid_statuses:
        order.status = new_status
        if new_status == 'delivered' and not order.delivered_at:
            from django.utils import timezone
            order.delivered_at = timezone.now()
        order.save()
    return redirect('dashboard')


@user_passes_test(is_staff_user, login_url='staff_login')
def delete_order(request, order_id):
    order = get_object_or_404(Order, id=order_id)
    order.delete()
    return redirect('dashboard')
@user_passes_test(is_staff_user, login_url='staff_login')
def manage_products(request):
    products = Product.objects.all().order_by('-created_at')
    return render(request, 'manage_products.html', {'products': products})


@user_passes_test(is_staff_user, login_url='staff_login')
def delete_product(request, product_id):
    product = get_object_or_404(Product, id=product_id)
    product.delete()
    return redirect('manage_products')
@user_passes_test(is_staff_user, login_url='staff_login')
def manage_categories(request):
    categories = Category.objects.all().order_by('name')

    if request.method == 'POST':
        name = request.POST.get('name')
        slug = request.POST.get('slug')
        if name and slug:
            Category.objects.create(name=name, slug=slug)
        return redirect('manage_categories')

    return render(request, 'manage_categories.html', {'categories': categories})


@user_passes_test(is_staff_user, login_url='staff_login')
def delete_category(request, category_id):
    category = get_object_or_404(Category, id=category_id)
    category.delete()
    return redirect('manage_categories')
from django.http import JsonResponse
import json

