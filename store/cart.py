# store/cart.py
from decimal import Decimal
from .models import Book

class Cart:
    def __init__(self, request):
        self.session = request.session
        cart = self.session.get('cart')
        if not cart:
            cart = self.session['cart'] = {}
        self.cart = cart

    def add(self, book_id, quantity=1, override_quantity=False):
        """Add a book to the cart or update its quantity."""
        book_id = str(book_id)
        if book_id not in self.cart:
            self.cart[book_id] = {'quantity': 0}
        elif isinstance(self.cart[book_id], int):
            self.cart[book_id] = {'quantity': self.cart[book_id]}

        if override_quantity:
            self.cart[book_id]['quantity'] = quantity
        else:
            self.cart[book_id]['quantity'] += quantity

        self.save()

    def remove(self, book_id):
        """Remove a book from the cart."""
        book_id = str(book_id)
        if book_id in self.cart:
            del self.cart[book_id]
            self.save()

    def save(self):
        """Mark session as modified to ensure it saves."""
        self.session.modified = True

    def clear(self):
        """Remove cart from session safely."""
        self.session.pop('cart', None)
        self.save()

    def __iter__(self):
        """Iterate over cart items and attach Book instances from DB."""
        book_ids = list(self.cart.keys())
        books = Book.objects.filter(id__in=book_ids)
        
        # Normalize items so integers become dicts safely
        cart = {}
        for k, v in self.cart.items():
            if isinstance(v, int):
                cart[str(k)] = {'quantity': v}
            elif isinstance(v, dict):
                cart[str(k)] = v.copy()

        for book in books:
            book_id_str = str(book.id)
            if book_id_str in cart:
                cart[book_id_str]['book'] = book
                cart[book_id_str]['price'] = Decimal(str(book.price))
                cart[book_id_str]['total_price'] = (
                    cart[book_id_str]['price'] * cart[book_id_str]['quantity']
                )
                yield cart[book_id_str]

    def __len__(self):
        """Count total items in cart."""
        total = 0
        for item in self.cart.values():
            if isinstance(item, int):
                total += item
            elif isinstance(item, dict):
                total += item.get('quantity', 0)
        return total

    def get_total_price(self):
        """Calculate total cart cost."""
        return sum(
            Decimal(str(item['book'].price)) * item['quantity']
            for item in self
        )