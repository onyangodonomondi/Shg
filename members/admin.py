from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Event, Contribution, EventCategory
from django.contrib.admin import SimpleListFilter
from django.db import models


# Inline admin for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    fk_name = 'user'
    fields = ('othernames', 'email', 'phone_number', 'birthdate', 'has_children', 'number_of_children', 'image')

# Custom filter for Contribution categories
class CategoryFilter(SimpleListFilter):
    title = 'Category'  # The title displayed in the filter dropdown
    parameter_name = 'category'  # The URL query parameter used for the filter

    def lookups(self, request, model_admin):
        """Return a list of options for the filter."""
        return [
            ('Fully Contributed', 'Fully Contributed'),
            ('Partially Contributed', 'Partially Contributed'),
            ('No Contribution', 'No Contribution'),
        ]

    def queryset(self, request, queryset):
        """Return the filtered queryset based on the selected filter option."""
        value = self.value()
        if value == 'Fully Contributed':
            return queryset.filter(amount__gte=models.F('event__required_amount'))
        elif value == 'Partially Contributed':
            return queryset.filter(amount__gt=0, amount__lt=models.F('event__required_amount'))
        elif value == 'No Contribution':
            return queryset.filter(amount=0)
        return queryset

# Customized User admin with profile details
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff', 'get_phone_number', 'get_other_names')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    def get_phone_number(self, obj):
        return obj.profile.phone_number
    get_phone_number.short_description = 'Phone Number'

    def get_other_names(self, obj):
        return obj.profile.othernames
    get_other_names.short_description = 'Other Names'

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super(UserAdmin, self).get_inline_instances(request, obj)

# Re-register UserAdmin with custom profile inline
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin customization for Event
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'required_amount', 'is_active')
    search_fields = ('name',)
    list_filter = ('date', 'is_active')
    ordering = ('date',)
    fieldsets = (
        ('Event Details', {
            'fields': ('name', 'date', 'required_amount', 'is_active')
        }),
    )

    # Custom action to mark events as inactive
    actions = ['mark_inactive']

    def mark_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, "Selected events have been marked as inactive.")
    mark_inactive.short_description = 'Mark selected events as inactive'

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('date')

# Admin customization for Contribution
@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('get_profile_name', 'event', 'amount', 'category')
    search_fields = ('profile__user__first_name', 'profile__user__last_name', 'event__name')
    list_filter = ('event', 'profile__user__first_name', 'profile__user__last_name', CategoryFilter)  # Use the custom CategoryFilter class here
    ordering = ('event', 'profile__user__last_name')
    readonly_fields = ('category',)

    def get_profile_name(self, obj):
        return f"{obj.profile.user.first_name} {obj.profile.user.last_name}"
    get_profile_name.short_description = 'Profile Name'



# Customizing the admin site titles
admin.site.site_header = "NYAGWA SHG Administration"
admin.site.site_title = "NYAGWA SHG Admin Portal"
admin.site.index_title = "Welcome to NYAGWA SHG Administration Portal"
