# store/admin.py
from django.contrib import admin

# Customizing the Django Admin headers and titles
admin.site.site_header = "StoryCandy Administration"  # Changes header text (top left banner)
admin.site.site_title = "StoryCandy Admin Portal"     # Changes browser tab title
admin.site.index_title = "Welcome to StoryCandy Management"  # Changes main index page subtitle

from .models import Book, BookImage, Category, Collection, Order, OrderItem

class BookImageInline(admin.TabularInline):
    model = BookImage
    extra = 3  # Gives 3 empty image slots by default
    fields = ['image', 'alt_text', 'is_primary', 'order']

@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    inlines = [BookImageInline]
    list_display = ['title', 'author', 'price', 'stock', 'is_available']
    search_fields = ['title', 'author', 'isbn']

@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('id', 'email', 'total_amount', 'paid', 'created_at')

@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')  # Adjust fields based on your Collection model
    search_fields = ('name',)

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'created_at')  # Adjust timestamp fields if named differently in TimeStampedModel
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}