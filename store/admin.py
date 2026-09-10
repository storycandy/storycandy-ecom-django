# store/admin.py
from django.contrib import admin

# Customizing the Django Admin headers and titles
admin.site.site_header = "StoryCandy Administration"  # Changes header text (top left banner)
admin.site.site_title = "StoryCandy Admin Portal"     # Changes browser tab title
admin.site.index_title = "Welcome to StoryCandy Management"  # Changes main index page subtitle

from .models import Book, BookImage, Category, Collection, Order, OrderItem
from django.contrib.contenttypes.admin import GenericTabularInline

class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 3  # Gives 3 empty image slots by default
    fields = ['image', 'alt_text', 'is_primary', 'order']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    inlines = [BookImageInline]
    list_display = ['title', 'author', 'price', 'stock', 'is_available']
    search_fields = ['title', 'author', 'isbn']

class OrderItemInline(GenericTabularInline):
    model = OrderItem
    extra = 0
    # Make items read-only in the order view to prevent accidental edits
    readonly_fields = ('item_type_display', 'item_title_display', 'item_id_display', 'price', 'quantity')
    fields = ('item_type_display', 'item_title_display', 'item_id_display', 'price', 'quantity')
    can_delete = False

    @admin.display(description='Type')
    def item_type_display(self, obj):
        if obj.content_type:
            return obj.content_type.model.title()
        return '-'

    @admin.display(description='Item ID')
    def item_id_display(self, obj):
        return obj.object_id

    @admin.display(description='Item Title / Name')
    def item_title_display(self, obj):
        # Fetches the underlying object (Book or Toy) and gets its title/name
        if obj.item:
            return getattr(obj.item, 'title', str(obj.item))
        return '-'


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'full_name', 'email', 'total_amount', 'paid', 'created_at')
    list_filter = ('paid', 'created_at')
    search_fields = ('id', 'full_name', 'email', 'razorpay_order_id')
    inlines = [OrderItemInline]

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')  # Adjust fields based on your Collection model
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')  # Adjust timestamp fields if named differently in TimeStampedModel
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}