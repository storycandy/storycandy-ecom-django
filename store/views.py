from decimal import Decimal
from django.template import loader
import razorpay
from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.contrib.contenttypes.models import ContentType
from django.http import HttpResponseBadRequest, JsonResponse
from .models import Book, Category, Collection, Order, OrderItem, Toy
from .cart import Cart
from django.contrib import messages
from .utils.magiclink import send_order_magic_link, verify_magic_token
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.mail import send_mail

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))




edu_categories = [
        {"id": 18, "name": "Prime Math"},
        {"id": 19, "name": "Active English"},
        {"id": 20, "name": "Active Grammar"},
        {"id": 21, "name": "Active English K"},
        {"id": 22, "name": "Active Math"},
        {"id": 23, "name": "Alpha Grammar"},
        {"id": 24, "name": "Alpha Math"},
        {"id": 25, "name": "Bookflix"},
        {"id": 26, "name": "I Can"},
        {"id": 27, "name": "Literacy Pro"},
        {"id": 28, "name": "Mathpro"},
        {"id": 29, "name": "World Of English"},
        {"id": 30, "name": "PR1ME K"},
        {"id": 31, "name": "Short Reads"},
        {"id": 32, "name": "Start Smart"},
        {"id": 33, "name": "Atlas"},
        {"id": 34, "name": "Go Grammar"},
        {"id": 35, "name": "The World Around Us"},
        {"id": 36, "name": "Dictionary"},
        {"id": 37, "name": "Spelling Success"},
        {"id": 38, "name": "Short Reads Plus"},
        {"id": 39, "name": "Primary Writing"},
        {"id": 40, "name": "Picture Composition"},
        {"id": 41, "name": "Comprehension Strategies"},
        {"id": 42, "name": "Supplementary Reading Programme"},
    ]

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
        'edu_categories' : edu_categories,
    }
    return render(request, 'home.html', context)

def about_view(request):    
    context = {}
    return render(request, 'about.html', context)

def toy_list(request):
    toys = Toy.objects.filter(is_available=True)

    # 1. Initialize active_collection BEFORE any checks
    active_collection = None

    # Search Query
    query = request.GET.get('q')
    if query:
        toys = toys.filter(
            Q(name__icontains=query) |
            Q(description__icontains=query) |
            Q(brand__icontains=query)
        )

    # Collection Filter
    collection_id = request.GET.get('collection')
    if collection_id:
        toys = toys.filter(collections__id=collection_id)
        active_collection = Collection.objects.filter(id=collection_id).first()

    # Category Filter
    category_id = request.GET.get('category')
    if category_id:
        toys = toys.filter(category_id=category_id)

    # Age Group Filter
    age_group = request.GET.get('age_group')
    if age_group:
        toys = toys.filter(age_group=age_group)

    # Pagination
    paginator = Paginator(toys.distinct(), 30)  # 30 toys per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'toys': page_obj,  # Passing page_obj as 'toys' to keep the template loop intact
        'page_obj': page_obj,
        'is_paginated': page_obj.has_other_pages(),
        'categories': Category.objects.all(),
        'collections': Collection.objects.all(),
        'active_collection': active_collection,
        'age_group_choices': getattr(Toy, 'AGE_GROUP_CHOICES', []),
    }
    return render(request, 'store/toy_list.html', context)


def toy_detail(request, pk):
    toy = get_object_or_404(Toy, pk=pk)

    # Fetch related toys in the same age group or category (excluding current toy)
    related_toys = Toy.objects.filter(
        category=toy.category
    ).exclude(pk=toy.pk)[:3]

    context = {
        'toy': toy,
        'related_toys': related_toys,
    }
    return render(request, 'store/toy_detail.html', context)

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


# ==========================================
# CART HELPER CLASS
# ==========================================

class Cart:
    """
    Session-based cart supporting both Book and Toy instances.
    Session structure:
    request.session['cart'] = {
        'book_1': {'item_type': 'book', 'item_id': 1, 'quantity': 2},
        'toy_5':  {'item_type': 'toy',  'item_id': 5, 'quantity': 1},
    }
    """
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def _get_item_key(self, item_type, item_id):
        return f"{item_type}_{item_id}"

    def add(self, item, item_type, quantity=1, override_quantity=False):
        key = self._get_item_key(item_type, item.id)
        if key not in self.cart:
            self.cart[key] = {
                'item_type': item_type,
                'item_id': item.id,
                'quantity': 0
            }

        if override_quantity:
            self.cart[key]['quantity'] = quantity
        else:
            self.cart[key]['quantity'] += quantity

        self.save()

    def update_quantity(self, item_type, item_id, action):
        key = self._get_item_key(item_type, item_id)
        if key in self.cart:
            if action == 'increase':
                self.cart[key]['quantity'] += 1
            elif action == 'decrease':
                self.cart[key]['quantity'] -= 1
                if self.cart[key]['quantity'] <= 0:
                    self.remove(item_type, item_id)
            self.save()

    def remove(self, item_type, item_id):
        key = self._get_item_key(item_type, item_id)
        if key in self.cart:
            del self.cart[key]
            self.save()

    def save(self):
        self.session['cart'] = self.cart
        self.session.modified = True

    def clear(self):
        del self.session['cart']
        self.session.modified = True

    def __iter__(self):
        """Iterates over cart items, fetching real instances from DB."""
        book_ids = [v['item_id'] for v in self.cart.values() if v['item_type'] == 'book']
        toy_ids = [v['item_id'] for v in self.cart.values() if v['item_type'] == 'toy']

        books_map = {b.id: b for b in Book.objects.filter(id__in=book_ids)}
        toys_map = {t.id: t for t in Toy.objects.filter(id__in=toy_ids)}

        cart_copy = self.cart.copy()

        for key, item_data in cart_copy.items():
            item_type = item_data['item_type']
            item_id = item_data['item_id']

            obj = books_map.get(item_id) if item_type == 'book' else toys_map.get(item_id)
            if not obj:
                continue

            subtotal = obj.price * item_data['quantity']
            yield {
                'key': key,
                'item': obj,
                'item_type': item_type,
                'item_id': item_id,
                'price': obj.price,
                'quantity': item_data['quantity'],
                'subtotal': subtotal,
            }

    def __len__(self):
        return sum(item['quantity'] for item in self.cart.values())

    def get_total_price(self):
        total = Decimal('0.00')
        for item in self:
            total += item['subtotal']
        return total


# ==========================================
# VIEWS
# ==========================================

def cart(request):
    """Renders the shopping cart page with item details and calculated total."""
    cart_obj = Cart(request)
    cart_items = list(cart_obj)
    total_price = cart_obj.get_total_price()

    context = {
        'cart_items': cart_items,
        'total_price': total_price,
    }
    return render(request, 'store/cart.html', context)


def add_to_cart(request, item_type, item_id):
    """
    Adds a Book or Toy to the cart.
    URL expects item_type ('book' or 'toy') and item_id.
    """
    if request.method == 'POST':
        if item_type == 'book':
            item_obj = get_object_or_404(Book, pk=item_id)
        elif item_type == 'toy':
            item_obj = get_object_or_404(Toy, pk=item_id)
        else:
            return HttpResponseBadRequest("Invalid item type")

        try:
            quantity = int(request.POST.get('quantity', 1))
        except (ValueError, TypeError):
            quantity = 1

        cart_obj = Cart(request)
        cart_obj.add(item=item_obj, item_type=item_type, quantity=quantity)

        if request.POST.get('direct_checkout') == '1':
            return redirect('cart')

        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            return JsonResponse({'cart_count': len(cart_obj)})

        return redirect(request.META.get('HTTP_REFERER', 'book_list'))

    return redirect('book_list')


def update_cart(request, item_type, item_id):
    """Increases or decreases item quantity in the cart."""
    if request.method == 'POST':
        action = request.POST.get('action')
        cart_obj = Cart(request)
        cart_obj.update_quantity(item_type=item_type, item_id=item_id, action=action)

    return redirect('cart')


def remove_from_cart(request, item_type, item_id):
    """Removes an item completely from the session cart."""
    if request.method == 'POST':
        cart_obj = Cart(request)
        cart_obj.remove(item_type=item_type, item_id=item_id)

    return redirect('cart')


def checkout(request):
    cart_obj = Cart(request)
    total_amount = cart_obj.get_total_price()

    if total_amount == 0:
        return redirect('book_list')

    if request.method == 'POST':
        email = request.POST.get('email')
        name = request.POST.get('full_name')
        address = request.POST.get('address')

        amount_in_paise = int(total_amount * 100)

        razorpay_order = client.order.create({
            'amount': amount_in_paise,
            'currency': 'INR',
            'payment_capture': '1'
        })

        order = Order.objects.create(
            email=email,
            full_name=name,
            shipping_address=address,
            total_amount=total_amount,
            razorpay_order_id=razorpay_order['id']
        )

        for item in cart_obj:
            OrderItem.objects.create(
                order=order,
                content_type=ContentType.objects.get_for_model(item['item']),
                object_id=item['item'].id,
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

    return render(request, 'store/checkout.html', {'cart': cart_obj, 'total_amount': total_amount})


def payment_view(request):
    cart_obj = Cart(request)
    total_amount = cart_obj.get_total_price()

    if total_amount == 0:
        return redirect('book_list')

    if request.method == 'POST':
        email = request.POST.get('email')
        full_name = request.POST.get('full_name')
        shipping_address = request.POST.get('shipping_address')

        order = Order.objects.create(
            full_name=full_name,
            email=email,
            shipping_address=shipping_address,
            total_amount=total_amount,
            paid=False
        )

        for item in cart_obj:
            OrderItem.objects.create(
                order=order,
                content_type=ContentType.objects.get_for_model(item['item']),
                object_id=item['item'].id,
                price=item['price'],
                quantity=item['quantity']
            )

        razorpay_order = client.order.create({
            "amount": int(total_amount * 100),
            "currency": "INR",
            "payment_capture": "1"
        })

        order.razorpay_order_id = razorpay_order['id']
        order.save()

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
            # 1. Verify Payment
            client.utility.verify_payment_signature(params_dict)

            # 2. Update Order status
            order = Order.objects.get(razorpay_order_id=razorpay_order_id)
            order.paid = True
            order.razorpay_payment_id = payment_id
            order.save()

            # 3. CLEAR CART IMMEDIATELY BEFORE ANYTHING ELSE
            cart_obj = Cart(request)
            cart_obj.clear()
            
            # Force session flush
            if 'cart' in request.session:
                del request.session['cart']
            request.session.modified = True

            # 4. Attempt Email (Failure won't break cart or order completion)
            try:
                send_order_magic_link(order, request=request)
            except Exception as mail_err:
                print(f"[WARNING] Mail failed (Zoho expired or network error): {mail_err}")

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