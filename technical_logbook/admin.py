from django.contrib import admin
from .models import (
    CarModel, CarSystem, MaintenanceTask, MaintenancePackage, PackageTask, MaintenanceCycle,
    SparePart, TaskRequiredPart, Car, MaintenanceRecord, MaintenanceRecordTask, UsedPart
)

# --- 1. Админка для Моделей автомобилей (НОВАЯ) ---

@admin.register(CarModel)
class CarModelAdmin(admin.ModelAdmin):
    list_display = ('make', 'model', 'engine', 'year_from', 'year_to')
    list_filter = ('make',)
    search_fields = ('make', 'model', 'engine')


# --- 2. Админка для Запчастей ---

@admin.register(SparePart)
class SparePartAdmin(admin.ModelAdmin):
    list_display = ('name', 'manufacturer', 'category', 'unit', 'current_price', 'expected_lifespan_km')
    list_filter = ('category', 'unit', 'manufacturer')
    search_fields = ('name', 'manufacturer')
    list_editable = ('current_price',)
    change_list_template = 'admin/sparepart_change_list.html'  # ← Добавляем

    fieldsets = (
        ('Основная информация', {'fields': ('name', 'manufacturer', 'category', 'unit')}),
        ('Ресурс и цена', {'fields': ('expected_lifespan_km', 'expected_lifespan_months', 'current_price')}),
    )


@admin.register(MaintenanceTask)
class MaintenanceTaskAdmin(admin.ModelAdmin):
    list_display = ('name', 'system', 'car_model', 'interval_km', 'interval_months', 'labor_cost')
    list_filter = ('system', 'car_model')
    search_fields = ('name', 'system__name')
    list_editable = ('labor_cost',)
    change_list_template = 'admin/maintenancetask_change_list.html'  # ← Обязательно!

    fieldsets = (
        ('Основная информация', {'fields': ('name', 'system', 'car_model')}),
        ('Регламент', {'fields': ('interval_km', 'interval_months')}),
        ('Стоимость', {'fields': ('labor_cost',)}),
    )

# --- 4. Инлайны для Записи о ТО ---

class MaintenanceRecordTaskInline(admin.TabularInline):
    model = MaintenanceRecordTask
    extra = 1
    autocomplete_fields = ['task']


class UsedPartInline(admin.TabularInline):
    model = UsedPart
    extra = 1
    autocomplete_fields = ['part']
    verbose_name = 'Установленная запчасть'
    verbose_name_plural = 'Установленные запчасти'

    # Показываем только нужные столбцы
    fields = ('part', 'quantity', 'unit_price', 'total_price_display')

    # total_price_display — это вычисляемое поле, только для чтения
    readonly_fields = ('total_price_display',)

    def total_price_display(self, obj):
        """Отображаем общую цену (считается автоматически)"""
        if obj.pk:  # Если запись уже сохранена
            return f"{obj.total_price:.2f} ₽"
        # Если запись ещё не сохранена, показываем подсказку
        if obj.unit_price and obj.quantity:
            return f"{float(obj.unit_price) * obj.quantity:.2f} ₽"
        return "—"

    total_price_display.short_description = 'Итого (₽)'
# --- 5. Админка для Записей о ТО ---

@admin.register(MaintenanceRecord)
class MaintenanceRecordAdmin(admin.ModelAdmin):
    list_display = ('car', 'date_performed', 'mileage_at_service', 'cost', 'package')
    list_filter = ('car', 'date_performed', 'package')
    search_fields = ('car__vin', 'car__car_model__make', 'car__car_model__model')
    date_hierarchy = 'date_performed'

    fieldsets = (
        ('Информация о ТО', {'fields': ('car', 'package', 'date_performed', 'mileage_at_service')}),
        ('Финансы', {'fields': ('labor_cost','cost',)}),
        ('Примечания', {'fields': ('notes',), 'classes': ('collapse',)}),
    )
    inlines = [MaintenanceRecordTaskInline, UsedPartInline]

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)

        record = form.instance
        total_parts_cost = sum(
            part.unit_price * part.quantity
            for part in record.used_parts.all()
        )
        # Общая стоимость = запчасти + работы
        record.cost = total_parts_cost + record.labor_cost
        record.save(update_fields=['cost'])


# --- 6. Админка для Автомобилей (ИСПРАВЛЕНА) ---

@admin.register(Car)
class CarAdmin(admin.ModelAdmin):
    # Убрали make и model, добавили car_model
    list_display = ('car_model', 'vin', 'license_plate', 'current_mileage', 'first_registration_date')
    search_fields = ('vin', 'car_model__make', 'car_model__model')
    list_filter = ('car_model',)

    fieldsets = (
        ('Основная информация', {'fields': ('car_model', 'vin', 'license_plate')}),
        ('Эксплуатация', {'fields': ('current_mileage', 'first_registration_date')}),
    )


# --- 7. Остальные справочники ---

@admin.register(CarSystem)
class CarSystemAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class PackageTaskInline(admin.TabularInline):
    model = PackageTask
    extra = 3
    autocomplete_fields = ['task']
    verbose_name = 'Задача'
    verbose_name_plural = 'Список задач в пакете'

@admin.register(MaintenancePackage)
class MaintenancePackageAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)
    inlines = [PackageTaskInline]


@admin.register(MaintenanceCycle)
class MaintenanceCycleAdmin(admin.ModelAdmin):
    list_display = ('name', 'car_model', 'total_mileage', 'step_mileage', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active', 'car_model')


admin.site.register(PackageTask)


@admin.register(TaskRequiredPart)
class TaskRequiredPartAdmin(admin.ModelAdmin):
    list_display = ('task', 'car_model', 'part', 'quantity')
    list_filter = ('car_model', 'task__system')
    autocomplete_fields = ['task', 'part', 'car_model']
    change_list_template = 'admin/taskrequiredpart_change_list.html'

    fieldsets = (
        ('Для какой машины', {'fields': ('car_model',)}),
        ('Норматив', {'fields': ('task', 'part', 'quantity')}),
    )

    def has_add_permission(self, request):
        """Перенаправляем на массовое добавление"""
        return super().has_add_permission(request)

@admin.register(UsedPart)
class UsedPartAdmin(admin.ModelAdmin):
    list_display = ('record', 'part', 'quantity', 'unit_price')
    list_filter = ('record__car', 'part')
    search_fields = ('part__name',)