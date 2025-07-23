from django.contrib import admin

from .models import Category, Post, Tag


class PostAdmin(admin.ModelAdmin):
    list_display = ("title", "author", "category", "created_at", "updated_at")
    list_filter = ("author", "category", "tags", "created_at")
    search_fields = ("title", "content")
    filter_horizontal = ("tags",)
    date_hierarchy = "created_at"

    fieldsets = (
        (None, {"fields": ("title", "author", "category")}),
        ("Content", {"fields": ("content", "tags")}),
        (
            "Timestamps",
            {"fields": ("created_at", "updated_at"), "classes": ("collapse",)},
        ),
    )

    readonly_fields = ("created_at", "updated_at")


class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


class TagAdmin(admin.ModelAdmin):
    list_display = ("name",)
    search_fields = ("name",)


admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
