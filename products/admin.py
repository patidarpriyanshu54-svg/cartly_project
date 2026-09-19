from django.contrib import admin
from .models import Category, Product, Cart, CartItem, Order, OrderItem, Wishlist, Review, ProductImage, ProductSpecification, ProductSize


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 3


class ProductSpecificationInline(admin.TabularInline):
    model = ProductSpecification
    extra = 4


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 4
class OrderAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'status', 'total_amount', 'created_at']

    def save_model(self, request, obj, form, change):
        from django.utils import timezone
        if obj.status == 'delivered' and not obj.delivered_at:
            obj.delivered_at = timezone.now()
        super().save_model(request, obj, form, change)

class ProductAdmin(admin.ModelAdmin):
    inlines = [ProductImageInline, ProductSpecificationInline, ProductSizeInline]


admin.site.register(Category)
admin.site.register(Product, ProductAdmin)
admin.site.register(Cart)
admin.site.register(Order, OrderAdmin)
admin.site.register(CartItem)
admin.site.register(OrderItem)
admin.site.register(Wishlist)
admin.site.register(Review)