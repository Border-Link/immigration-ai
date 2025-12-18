from django.contrib import admin
from users_access.models.country import Country
from users_access.models.state_province import StateProvince


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    """Admin interface for Country model."""
    list_display = ('code', 'name', 'has_states', 'is_jurisdiction', 'is_active', 'created_at')
    list_filter = ('is_active', 'is_jurisdiction', 'has_states', 'created_at')
    search_fields = ('code', 'name')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('name',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name')
        }),
        ('Immigration Context', {
            'fields': ('has_states', 'is_jurisdiction')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(StateProvince)
class StateProvinceAdmin(admin.ModelAdmin):
    """Admin interface for StateProvince model."""
    list_display = ('name', 'code', 'country', 'has_nomination_program', 'is_active', 'created_at')
    list_filter = ('is_active', 'has_nomination_program', 'country', 'created_at')
    search_fields = ('name', 'code', 'country__name', 'country__code')
    readonly_fields = ('id', 'created_at', 'updated_at')
    ordering = ('country', 'name')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('country', 'code', 'name')
        }),
        ('Immigration Context', {
            'fields': ('has_nomination_program',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('id', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
