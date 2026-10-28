from django.db import models


class SoftDeleteQuerySet(models.QuerySet):
    """QuerySet that performs soft deletes by default."""

    def delete(self):
        count = self.update(is_active=False)
        return count, {self.model._meta.label: count}

    def restore(self):
        return self.update(is_active=True)

    def hard_delete(self):
        return super().delete()


SoftDeleteManager = models.Manager.from_queryset(SoftDeleteQuerySet)


class ActiveManager(SoftDeleteManager):
    """Default manager: only returns active (not soft deleted) rows."""

    def get_queryset(self):
        return super().get_queryset().filter(is_active=True)


class BaseModel(models.Model):
    is_active = models.BooleanField(default=True, db_index=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ``objects`` returns only active rows, ``all_objects`` returns everything.
    objects = ActiveManager()
    all_objects = SoftDeleteManager()

    def delete(self, using=None, keep_parents=False):
        """Soft delete: the row is kept in the database and marked inactive."""
        self.is_active = False
        self.save(using=using)

    def hard_delete(self, using=None, keep_parents=False):
        return super().delete(using=using, keep_parents=keep_parents)

    def restore(self):
        self.is_active = True
        self.save()

    class Meta:
        abstract = True
