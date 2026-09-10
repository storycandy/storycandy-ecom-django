from datetime import datetime
import time
import os
import uuid
from django.db import models
from django.conf import settings
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation



class TimeStampedModel(models.Model):
    """
    An abstract base class model that provides self-updating
    'created_at' and 'updated_at' fields.
    """
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

class Category(TimeStampedModel):
    """
    Structural classification (e.g., Fiction, Non-fiction, Activity Books).
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)

    class Meta:
        verbose_name_plural = "Categories"

    def __str__(self):
        return self.name

class Collection(TimeStampedModel):
    """
    Marketing badges/sections like Best-seller, Popular Series, India-Publishing, etc.
    A book can belong to multiple collections.
    """
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name

    @property
    def display_name(self):
        return self.name
    

# def book_cover_upload_path(instance, filename):
#     # Determine the title whether instance is a Book or BookImage inline
#     if hasattr(instance, 'book') and instance.book:
#         title = instance.book.title
#     else:
#         title = getattr(instance, 'title', 'untitled')

#     slug = slugify(title) or 'book'
    
#     # Extract file extension
#     ext = filename.split('.')[-1] if '.' in filename else ''
    
#     # Generate a unique timestamp (e.g., 1735689600)
#     timestamp = int(time.time())
    
#     # Get image index/order if available on BookImage model, fallback to 1
#     order = getattr(instance, 'order', getattr(instance, 'id', 1)) or 1
    
#     # Construct filename: slug-timestamp-order.ext (e.g., harry-potter-1735689600-1.jpg)
#     new_filename = f"{slug}-{timestamp}-{order}.{ext}" if ext else f"{slug}-{timestamp}-{order}"

#     return os.path.join('books/covers/', new_filename)

def item_cover_upload_path(instance, filename, folder_prefix):
    """Dynamic path helper for both books and toys."""
    item = getattr(instance, 'book', getattr(instance, 'toy', None))
    
    if item and hasattr(item, 'title'):
        title = item.title
    else:
        title = getattr(instance, 'title', 'untitled')

    slug = slugify(title) or 'item'
    ext = filename.split('.')[-1] if '.' in filename else ''
    timestamp = int(time.time())
    order = getattr(instance, 'order', getattr(instance, 'id', 1)) or 1

    new_filename = f"{slug}-{timestamp}-{order}.{ext}" if ext else f"{slug}-{timestamp}-{order}"
    return os.path.join(f'{folder_prefix}/covers/', new_filename)

def book_cover_upload_path(instance, filename):
    return item_cover_upload_path(instance, filename, folder_prefix='books')


def toy_cover_upload_path(instance, filename):
    return item_cover_upload_path(instance, filename, folder_prefix='toys')

class Book(TimeStampedModel):
    # ... your existing Book model fields ...
    # Note: You can remove the old `cover_image` single ImageField, or keep it as a 'primary cover' shortcut.
    # Recommended: Remove `cover_image` from Book and use `BookImage` with an `is_primary` flag.

    BINDING_CHOICES = [
        ('paperback', 'Paperback'),
        ('hardcover', 'Hardcover'),
        ('boardbook', 'Board Book'),
        ('boxset', 'Box Set'),
    ]
    LANGUAGE_CHOICES = [
        ('Assamese', 'Assamese'),
        ('Bengali', 'Bengali'),
        ('Bodo', 'Bodo'),
        ('Dogri', 'Dogri'),
        ('English', 'English'),
        ('Gujarati', 'Gujarati'),
        ('Hindi', 'Hindi'),
        ('Kannada', 'Kannada'),
        ('Kashmiri', 'Kashmiri'),
        ('Konkani', 'Konkani'),
        ('Maithili', 'Maithili'),
        ('Malayalam', 'Malayalam'),
        ('Manipuri', 'Manipuri (Meitei)'),
        ('Marathi', 'Marathi'),
        ('Nepali', 'Nepali'),
        ('Odia', 'Odia'),
        ('Punjabi', 'Punjabi'),
        ('Sanskrit', 'Sanskrit'),
        ('Santali', 'Santali'),
        ('Sindhi', 'Sindhi'),
        ('Tamil', 'Tamil'),
        ('Telugu', 'Telugu'),
        ('Urdu', 'Urdu'),
    ]

    AGE_GROUP_CHOICES = [
        ('0-2', '0 to 2 years (Toddlers)'),
        ('3-5', '3 to 5 years (Early Readers)'),
        ('6-8', '6 to 8 years (Early Chapter Books)'),
        ('9-12', '9 to 12 years (Middle Grade)'),
        ('13+', '13+ years (Young Adult)'),
    ]

    THEME_CHOICES = [
        ('life_skills', 'Life Skills'),
        ('mental_health', 'Mental Health'),
        ('adventure', 'Adventure & Fantasy'),
        ('stem', 'STEM & Science'),
        ('friendship', 'Friendship & Family'),
        ('values', 'Moral Values & Ethics'),
    ]

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    author = models.CharField(max_length=255)
    isbn = models.CharField(max_length=13, unique=True, verbose_name="ISBN")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    binding = models.CharField(
        max_length=20, choices=BINDING_CHOICES, default='paperback'
    )
    pages = models.PositiveIntegerField(blank=True, null=True)
    language = models.CharField(
        max_length=50, 
        choices=LANGUAGE_CHOICES, 
        default='English'
    )
    age_group = models.CharField(
        max_length=20, 
        choices=AGE_GROUP_CHOICES, 
        blank=True
    )
    theme = models.CharField(
        max_length=50, 
        choices=THEME_CHOICES, 
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="books"
    )
    collections = models.ManyToManyField(
        Collection,
        blank=True,
        related_name="books"
    )

    summary = models.TextField(blank=True, verbose_name="Product Summary")

    def __str__(self):
        return self.title

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_available

    @property
    def primary_image(self):
        """Returns the primary image or the first image from the array."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        first_img = self.images.first()
        return first_img.image if first_img else None


class BookImage(TimeStampedModel):
    """Stores multiple images per book (Array/Gallery)."""
    book = models.ForeignKey(
        Book, 
        on_delete=models.CASCADE, 
        related_name="images"
    )
    image = models.ImageField(upload_to=book_cover_upload_path)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(
        default=False, 
        help_text="Mark as main cover image"
    )
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Order of display in gallery"
    )

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.book.title} ({'Primary' if self.is_primary else 'Gallery'})"


# ==========================================
# TOY MODELS
# ==========================================

class Toy(TimeStampedModel):
    MATERIAL_CHOICES = [
        ('wooden', 'Wooden'),
        ('plastic', 'Plastic'),
        ('fabric', 'Fabric / Plush'),
        ('silicone', 'Silicone'),
        ('paper_cardboard', 'Paper / Cardboard'),
        ('metal', 'Metal'),
    ]

    title = models.CharField(max_length=255)
    subtitle = models.CharField(max_length=255, blank=True)
    brand = models.CharField(max_length=255, blank=True)
    sku = models.CharField(max_length=50, unique=True, verbose_name="SKU / Item Code")

    price = models.DecimalField(max_digits=10, decimal_places=2)
    discount_price = models.DecimalField(
        max_digits=10, decimal_places=2, blank=True, null=True
    )
    stock = models.PositiveIntegerField(default=1)
    is_available = models.BooleanField(default=True)

    material = models.CharField(
        max_length=30, choices=MATERIAL_CHOICES, blank=True
    )
    age_group = models.CharField(
        max_length=20, 
        choices=Book.AGE_GROUP_CHOICES, 
        blank=True
    )
    theme = models.CharField(
        max_length=50, 
        choices=Book.THEME_CHOICES, 
        blank=True
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="toys"
    )
    collections = models.ManyToManyField(
        Collection,
        blank=True,
        related_name="toys"
    )

    summary = models.TextField(blank=True, verbose_name="Product Summary")

    def __str__(self):
        return self.title

    @property
    def is_in_stock(self):
        return self.stock > 0 and self.is_available

    @property
    def primary_image(self):
        """Returns the primary image or the first image from the gallery."""
        primary = self.images.filter(is_primary=True).first()
        if primary:
            return primary.image
        first_img = self.images.first()
        return first_img.image if first_img else None


class ToyImage(TimeStampedModel):
    """Stores multiple images per toy (Array/Gallery)."""
    toy = models.ForeignKey(
        Toy, 
        on_delete=models.CASCADE, 
        related_name="images"
    )
    image = models.ImageField(upload_to=toy_cover_upload_path)
    alt_text = models.CharField(max_length=255, blank=True)
    is_primary = models.BooleanField(
        default=False, 
        help_text="Mark as main cover image"
    )
    order = models.PositiveIntegerField(
        default=0, 
        help_text="Order of display in gallery"
    )

    class Meta:
        ordering = ['order', 'created_at']

    def __str__(self):
        return f"Image for {self.toy.title} ({'Primary' if self.is_primary else 'Gallery'})"


class Order(TimeStampedModel):
    tracking_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True)
    email = models.EmailField()
    full_name = models.CharField(max_length=255)
    shipping_address = models.TextField()
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Payment Tracking
    paid = models.BooleanField(default=False)
    razorpay_order_id = models.CharField(max_length=100, blank=True, null=True)
    razorpay_payment_id = models.CharField(max_length=100, blank=True, null=True)

    def __str__(self):
        return f"Order #{self.id} - {self.email} ({'Paid' if self.paid else 'Pending'})"

class OrderItem(TimeStampedModel):
    order = models.ForeignKey(Order, related_name='items', on_delete=models.CASCADE)

    # Generic relation to support both Book and Toy models
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('book', 'toy')}
    )
    object_id = models.PositiveIntegerField()
    item = GenericForeignKey('content_type', 'object_id')

    # book = models.ForeignKey(Book, on_delete=models.CASCADE)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)

    def __str__(self):
        item_name = getattr(self.item, 'title', 'Unknown Item')
        return f"{self.quantity}x {item_name}"