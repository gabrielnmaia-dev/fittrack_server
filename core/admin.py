from django.contrib import admin


class BaseModelAdmin(admin.ModelAdmin):
    """Admin that exposes soft deleted rows and offers restore/deactivate actions."""

    actions = ('deactivate_selected', 'restore_selected')
    readonly_fields = ('created_at', 'updated_at')

    def get_queryset(self, request):
        # ``all_objects`` includes soft deleted rows so they can be restored.
        return self.model.all_objects.get_queryset()

    @admin.action(description='Desativar selecionados (soft delete)')
    def deactivate_selected(self, request, queryset):
        updated = queryset.filter(is_active=True).update(is_active=False)
        self.message_user(request, f'{updated} registro(s) desativado(s).')

    @admin.action(description='Restaurar selecionados')
    def restore_selected(self, request, queryset):
        updated = queryset.filter(is_active=False).update(is_active=True)
        self.message_user(request, f'{updated} registro(s) restaurado(s).')


__all__ = ['BaseModelAdmin']
