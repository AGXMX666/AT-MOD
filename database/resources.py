from import_export import resources
from .models import registrationcode, Book, Supplier, users
from django.core.exceptions import ValidationError


class RegistrationCodeResource(resources.ModelResource):
    class Meta:
        model = registrationcode
        fields = ('codes', 'user', 'Status', 'time')
        import_id_fields = ['codes']
        skip_unchanged = True


class BookResource(resources.ModelResource):
    def before_import(self, dataset, using_transactions, dry_run, **kwargs):
        self.current_user = kwargs.get('user')

    def skip_row(self, instance, original):
        code = original.get('编码') or original.get('code')
        if code:
            if Book.objects.filter(code=code).exists():
                raise ValidationError(f'书籍编码 {code} 已存在')
        return True

    def get_import_id(self, row):
        return row.get('编码') or row.get('code')

    def before_save_instance(self, instance, row, using_transactions, dry_run):
        if hasattr(self, 'current_user') and self.current_user:
            instance.user = self.current_user

        supplier_name = row.get('供应商')
        if supplier_name:
            try:
                supplier = Supplier.objects.get(name=supplier_name)
                instance.supplier = supplier
            except Supplier.DoesNotExist:
                raise ValidationError(f'供应商 {supplier_name} 不存在，请先创建供应商')

        if not instance.image or not instance.image.name:
            instance.image = 'static/img/logo.png'

    class Meta:
        model = Book
        fields = (
            'code',
            'name',
            'cost',
            'supplier',
            'use_count',
            'is_display',
        )
        import_id_fields = ['code']
        skip_unchanged = True
