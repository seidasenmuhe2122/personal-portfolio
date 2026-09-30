from django.core.management.base import BaseCommand
from django.utils import timezone
from core.models import Post
class Command(BaseCommand):
    help='Publish due scheduled posts'
    def handle(self,*args,**kwargs):
        n=Post.objects.filter(status='scheduled',publish_at__lte=timezone.now()).update(status='published')
        self.stdout.write(self.style.SUCCESS(f'Published {n} scheduled posts.'))
