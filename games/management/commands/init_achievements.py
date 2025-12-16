"""
Management command to initialize default achievements
"""
from django.core.management.base import BaseCommand
from accounts.models import Achievement
from games.models import ChessManager


class Command(BaseCommand):
    help = 'Initialize default achievements in the database'

    def handle(self, *args, **options):
        self.stdout.write('🎯 Initializing achievements...')
        
        try:
            created_count = ChessManager.create_default_achievements()
            
            if created_count > 0:
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ Successfully created {created_count} achievements'
                    )
                )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️ All achievements already exist'
                    )
                )
            
            # Display achievement summary
            total_count = Achievement.objects.filter(is_active=True).count()
            self.stdout.write(f'\n📊 Total active achievements: {total_count}')
            
            # Display by category
            categories = Achievement.objects.filter(is_active=True).values_list('category', flat=True).distinct()
            for category in categories:
                count = Achievement.objects.filter(is_active=True, category=category).count()
                self.stdout.write(f'   - {category.title()}: {count} achievements')
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(
                    f'❌ Error creating achievements: {str(e)}'
                )
            )
            raise
