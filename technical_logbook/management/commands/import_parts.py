import pandas as pd
from django.core.management.base import BaseCommand
from technical_logbook.models import SparePart


class Command(BaseCommand):
    help = 'Импорт запчастей из Excel файла'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Путь к Excel файлу')

    def handle(self, *args, **options):
        file_path = options['file_path']

        try:
            df = pd.read_excel(file_path)
        except Exception as e:
            self.stderr.write(f'Ошибка чтения файла: {e}')
            return

        created = 0
        updated = 0

        for _, row in df.iterrows():
            # Пропускаем пустые строки
            if pd.isna(row['name']):
                continue

            # Ищем существующую запчасть или создаём новую
            part, created_flag = SparePart.objects.get_or_create(
                name=row['name'],
                manufacturer=row['manufacturer'],
                defaults={
                    'category': row.get('category', 'other'),
                    'expected_lifespan_km': int(row['expected_lifespan_km']) if pd.notna(
                        row['expected_lifespan_km']) else None,
                    'expected_lifespan_months': int(row['expected_lifespan_months']) if pd.notna(
                        row['expected_lifespan_months']) else None,
                    'unit': row.get('unit', 'pcs'),
                    'current_price': float(row['current_price']) if pd.notna(row['current_price']) else 0,
                }
            )

            if created_flag:
                created += 1
                self.stdout.write(self.style.SUCCESS(f'✓ Создано: {part.name} ({part.manufacturer})'))
            else:
                updated += 1
                # Обновляем цену и другие поля
                part.category = row.get('category', part.category)
                part.expected_lifespan_km = int(row['expected_lifespan_km']) if pd.notna(
                    row['expected_lifespan_km']) else part.expected_lifespan_km
                part.expected_lifespan_months = int(row['expected_lifespan_months']) if pd.notna(
                    row['expected_lifespan_months']) else part.expected_lifespan_months
                part.unit = row.get('unit', part.unit)
                part.current_price = float(row['current_price']) if pd.notna(
                    row['current_price']) else part.current_price
                part.save()
                self.stdout.write(self.style.WARNING(f'↻ Обновлено: {part.name} ({part.manufacturer})'))

        self.stdout.write(self.style.SUCCESS(f'\n✅ Готово! Создано: {created}, Обновлено: {updated}'))