from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.contrib.auth.models import User
from .models import Profile, Event, Contribution

# Inline admin for Profile
class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False
    verbose_name_plural = 'Profile Details'
    fk_name = 'user'
    fields = ('surname', 'othernames', 'email', 'phone_number', 'birthdate', 'has_children', 'number_of_children', 'image')

# Customized User admin
class UserAdmin(BaseUserAdmin):
    inlines = (ProfileInline,)
    list_display = ('username', 'email', 'first_name', 'last_name', 'is_staff')
    search_fields = ('username', 'first_name', 'last_name', 'email')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'groups')

    def get_inline_instances(self, request, obj=None):
        if not obj:
            return []
        return super(UserAdmin, self).get_inline_instances(request, obj)

    def get_fieldsets(self, request, obj=None):
        fieldsets = super().get_fieldsets(request, obj)
        if obj:
            fieldsets = list(fieldsets)
            fieldsets.append(('NYAGWA SHG Profile', {'fields': ('profile',)}))
        return fieldsets

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)

# Admin customization for Event
@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ('name', 'date', 'required_amount', 'is_active')
    search_fields = ('name',)
    list_filter = ('date', 'is_active')  # Added filter for active status
    ordering = ('date',)
    fieldsets = (
        ('Event Details', {
            'fields': ('name', 'date', 'required_amount', 'is_active')
        }),
    )

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.order_by('date')
# Admin customization for Contribution
@admin.register(Contribution)
class ContributionAdmin(admin.ModelAdmin):
    list_display = ('get_profile_name', 'event', 'amount', 'category')
    search_fields = ('profile__surname', 'profile__othernames', 'event__name')
    list_filter = ('event', 'profile__surname', 'profile__othernames')
    ordering = ('event', 'profile__surname')
    readonly_fields = ('category',)

    def get_profile_name(self, obj):
        return f"{obj.profile.surname} {obj.profile.othernames}"
    get_profile_name.short_description = 'Profile Name'

# Customizing the admin site titles
admin.site.site_header = "NYAGWA SHG Administration"
admin.site.site_title = "NYAGWA SHG Admin Portal"
admin.site.index_title = "Welcome to NYAGWA SHG Administration Portal"
