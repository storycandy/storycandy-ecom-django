from decimal import Decimal
from django.template import loader
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponseBadRequest, JsonResponse
from .models import Book, Category, Collection, Order, OrderItem
from .cart import Cart
from django.contrib import messages
from .models import Order, OrderItem, Book
from .utils.magiclink import send_order_magic_link, verify_magic_token
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))

def home_view(request):
    # Retrieve collections using iexact on name or slug for safety
    bestseller_books = Book.objects.filter(
        is_available=True, 
        collections__name__iexact='Bestseller'
    ).distinct()[:8]

    popular_books = Book.objects.filter(
        is_available=True, 
        collections__name__iexact='Popular Series'
    ).distinct()[:8]

    india_publishing_books = Book.objects.filter(
        is_available=True, 
        collections__name__iexact='India Publishing'
    ).distinct()[:8]

    context = {
        'bestseller_books': bestseller_books,
        'popular_books': popular_books,
        'india_publishing_books': india_publishing_books,
        'collections': Collection.objects.all(),
        'categories': Category.objects.all(),
    }
    return render(request, 'home.html', context)

def about_view(request):    
    context = {}
    return render(request, 'about.html', context)

def book_list(request):
    books = Book.objects.filter(is_available=True)
    
    # 1. Initialize active_collection BEFORE any checks
    active_collection = None

    # Search Query
    query = request.GET.get('q')
    if query:
        books = books.filter(
            Q(title__icontains=query) | 
            Q(author__icontains=query) | 
            Q(summary__icontains=query)
        )

    # Collection Filter
    collection_id = request.GET.get('collection')
    if collection_id:
        books = books.filter(collections__id=collection_id)
        active_collection = Collection.objects.filter(id=collection_id).first()

    # Category Filter
    category_id = request.GET.get('category')
    if category_id:
        books = books.filter(category_id=category_id)

    # Language Filter
    language = request.GET.get('language')
    if language:
        books = books.filter(language=language)

    # Age Group Filter
    age_group = request.GET.get('age_group')
    if age_group:
        books = books.filter(age_group=age_group)

    # Pagination
    paginator = Paginator(books.distinct(), 30)  # 30 books per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'books': page_obj,  # Passing page_obj as 'books' keeps your template loop intact
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': Category.objects.all(),
        'collections': Collection.objects.all(),
        'active_collection': active_collection,
        'language_choices': Book.LANGUAGE_CHOICES,
        'age_group_choices': Book.AGE_GROUP_CHOICES,
    }
    return render(request, 'store/book_list.html', context)

def book_detail(request, pk):
    book = get_object_or_404(Book, pk=pk)

    print('book --------------- ', book)
    
    # Fetch related books in the same age group (excluding current book)
    related_books = Book.objects.filter(
        age_group=book.age_group
    ).exclude(pk=book.pk)[:3]

    context = {
        'book': book,
        'related_books': related_books,
    }
    return render(request, 'store/book_detail.html', context)

def cart(request):
    """Renders the shopping cart page with item details and calculated subtotal."""
    session_cart = request.session.get('cart', {})
    cart_items = []
    total_price = Decimal('0.00')

    # Fetch books from database based on IDs stored in session
    for book_id, item_data in session_cart.items():
        try:
            book = Book.objects.get(pk=book_id)
            
            # Extract quantity whether item_data is a dict or a direct int/str
            if isinstance(item_data, dict):
                quantity = int(item_data.get('quantity', 1))
            else:
                quantity = int(item_data)

            subtotal = book.price * quantity
            total_price += subtotal
            
            cart_items.append({
                'book': book,
                'quantity': quantity,
                'subtotal': subtotal,
            })
        except (Book.DoesNotExist, ValueError, TypeError):
            continue

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, book_id):
    if request.method == 'POST':
        print('STARTED --------------- ')
        book = get_object_or_404(Book, pk=book_id)

        print('book --------------- ', book)
        
        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        cart = request.session.get('cart', {})
        book_id_str = str(book_id)
        existing_val = cart.get(book_id_str, 0)

        # Handle existing item whether stored as a dict or an integer
        if isinstance(existing_val, dict):
            current_qty = int(existing_val.get('quantity', 0))
            existing_val['quantity'] = current_qty + quantity
            cart[book_id_str] = existing_val
        else:
            try:
                current_qty = int(existing_val)
            except (ValueError, TypeError):
                current_qty = 0
            cart[book_id_str] = current_qty + quantity

        # Mark session as modified so Django saves changes
        request.session['cart'] = cart
        request.session.modified = True

        # Redirect directly to cart page if 'Buy Now' was clicked
        if request.POST.get('direct_checkout') == '1':
            return redirect('cart')

        # Handle AJAX response if submitted asynchronously
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            total_count = sum(
                item['quantity'] if isinstance(item, dict) else int(item)
                for item in cart.values()
            )
            return JsonResponse({'cart_count': total_count})

        return redirect(request.META.get('HTTP_REFERER', 'book_list'))

    return redirect('book_list')

def update_cart(request, book_id):
    """Increases or decreases item quantity in the cart."""
    if request.method == 'POST':
        action = request.POST.get('action')
        cart = request.session.get('cart', {})
        book_id_str = str(book_id)

        if book_id_str in cart:
            if action == 'increase':
                cart[book_id_str] += 1
            elif action == 'decrease':
                cart[book_id_str] -= 1
                if cart[book_id_str] <= 0:
                    del cart[book_id_str]

            request.session['cart'] = cart
            request.session.modified = True

    return redirect('cart')


def remove_from_cart(request, book_id):
    """Removes an item completely from the session cart."""
    if request.method == 'POST':
        cart = request.session.get('cart', {})
        book_id_str = str(book_id)

        if book_id_str in cart:
            del cart[book_id_str]
            request.session['cart'] = cart
            request.session.modified = True

    return redirect('cart')

def checkout(request):
    cart = Cart(request)
    total_amount = cart.get_total_price()

    if total_amount == 0:
        return redirect('book_list')

    if request.method == 'POST':
        # Collect Guest Details
        email = request.POST.get('email')
        name = request.POST.get('full_name')
        address = request.POST.get('address')

        # Convert INR to paise for Razorpay
        amount_in_paise = int(total_amount * 100)

        # Create Razorpay Order
        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })

        # Create Draft Order in DB
        order = Order.objects.create(
            email=email,
            full_name=name,
            shipping_address=address,
            total_amount=total_amount,
            razorpay_order_id=razorpay_order['id']
        )

        for item in cart:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                price=item['price'],
                quantity=item['quantity']
            )

        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount_in_paise': amount_in_paise,
        }
        return render(request, 'store/payment.html', context)

    return render(request, 'store/checkout.html', {'cart': cart, 'total_amount': total_amount})

def payment_view(request):
    cart = Cart(request)
    
    # Redirect if cart is empty
    if not cart:
        return redirect('book_list')

    if request.method == 'POST':
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        shipping_address = request.POST.get('shipping_address')

        total_amount = cart.get_total_price() # e.g. 299

        # 1. Create local Order record
        order = Order.objects.create(
            full_name=full_name,
            email=email,
            shipping_address=shipping_address,
            total_amount=total_amount,
            paid=False
        )

        # 2. Add Cart items to OrderItem model
        for item in cart:
            OrderItem.objects.create(
                order=order,
                book=item['book'],
                price=item['price'],
                quantity=item['quantity']
            )

        # 3. Initialize Razorpay Client & Create Order
        client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))
        
        # Razorpay expects the amount in paise (1 INR = 100 Paise)
        razorpay_order = client.order.create({
            "amount": int(total_amount * 100),
            "currency": "INR",
            "payment_capture": "1"
        })

        # Save Razorpay Order ID to local Order model
        order.razorpay_order_id = razorpay_order['id']
        order.save()

        # 4. Context for client-side Razorpay modal
        context = {
            'order': order,
            'razorpay_order_id': razorpay_order['id'],
            'razorpay_key_id': settings.RAZORPAY_KEY_ID,
            'amount_in_paise': int(total_amount * 100),
            'currency': 'INR',
            'callback_url': request.build_absolute_uri('/payment-success/')
        }
        return render(request, 'store/payment.html', context)

    return redirect('checkout')

@csrf_exempt
def payment_success(request):
    if request.method == "POST":
        payment_id = request.POST.get('razorpay_payment_id', '')
        razorpay_order_id = request.POST.get('razorpay_order_id', '')
        signature = request.POST.get('razorpay_signature', '')

        params_dict = {
            'razorpay_order_id': razorpay_order_id,
            'razorpay_payment_id': payment_id,
            'razorpay_signature': signature
        }

        try:
            # 1. Verify payment signature
            client.utility.verify_payment_signature(params_dict)
            
            # 2. Mark Order as Paid
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.paid = True
            order.razorpay_payment_id = payment_id
            order.save()

            # 3. Clear Session Cart
            cart = Cart(request)
            cart.clear()

            # 4. Dispatch Magic Link via ZeptoMail
            try:
                send_order_magic_link(order, request=request)
            except Exception as mail_err:
                print(f"Failed to send magic link email: {mail_err}")

            return render(request, 'store/success.html', {'order': order})

        except Exception as e:
            print(f"Payment verification failed: {e}")
            return HttpResponseBadRequest("Payment Verification Failed")

    return HttpResponseBadRequest("Invalid Request")


def order_magic_access(request, token):
    """Validates the permanent magic link token and displays order details."""
    
    # FIX: Remove max_age_seconds parameter here
    tracking_id = verify_magic_token(token)
    
    if not tracking_id:
        return render(request, 'store/magic_link_invalid.html', {
            'error': 'This access link is invalid or corrupted.'
        })

    order = get_object_or_404(Order, tracking_id=tracking_id)
    return render(request, 'store/order_detail.html', {'order': order})

def book_fair_proposal(request):
    if request.method == 'POST':
        school_name = request.POST.get('school_name')
        city = request.POST.get('city')
        board = request.POST.get('board')
        contact_info = request.POST.get('contact_info')

        subject = f"New Book Fair Proposal Request: {school_name}"
        message = (
            f"You have received a new Book Fair proposal request:\n\n"
            f"School Name: {school_name}\n"
            f"City: {city}\n"
            f"Board: {board}\n"
            f"Contact Info (Email/Mobile): {contact_info}\n"
        )
        
        recipient_list = ['Storycandy1111@gmail.com']

        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                recipient_list,
                fail_silently=False,
            )
            messages.success(request, 'Your proposal request has been submitted successfully!')
        except Exception as e:
            messages.error(request, 'Failed to send request. Please try again.')

        return redirect(request.META.get('HTTP_REFERER', '/'))