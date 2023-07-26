from django.core.management import BaseCommand
from recipes.models import Tag


class Command(BaseCommand):
    help = 'Loads tags'

    def handle(self, *args, **kwargs):
        data = [
            {'name': 'завтрак', 'color': '#FF000', 'slug': 'breakfast'},
            {'name': 'обед', 'color': '#00FFFF', 'slug': 'lunch'},
            {'name': 'ужин', 'color': '#00FA9', 'slug': 'dinner'},
        ]
        Tag.objects.bulk_create(Tag(**tag) for tag in data)
        self.stdout.write(self.style.SUCCESS('Тэги загружены'))
