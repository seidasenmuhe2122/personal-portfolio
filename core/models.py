from django.db import models
from django.contrib.auth.models import User, Group
from django.core.validators import MaxValueValidator, MinValueValidator
from django.utils.text import slugify
from django.utils import timezone

class TimeStamped(models.Model):
    created_at=models.DateTimeField(auto_now_add=True); updated_at=models.DateTimeField(auto_now=True)
    class Meta: abstract=True

class SiteSettings(TimeStamped):
    site_name=models.CharField(max_length=120,default='Seid Digital Platform'); tagline=models.CharField(max_length=255,default='Technology • Cybersecurity • AI • Automation • Management')
    logo=models.ImageField(upload_to='branding/',blank=True); favicon=models.ImageField(upload_to='branding/',blank=True)
    contact_orbit_mark=models.CharField(max_length=24,default='S',blank=True,help_text='Displayed in the contact orbit when no image is uploaded.')
    contact_orbit_image=models.ImageField(upload_to='branding/',blank=True,help_text='Optional image that replaces the text mark in the contact orbit.')
    primary_color=models.CharField(max_length=20,default='#7c5cff'); accent_color=models.CharField(max_length=20,default='#00d4ff'); dark_mode_default=models.BooleanField(default=True)
    ai_enabled=models.BooleanField(default=True); blog_enabled=models.BooleanField(default=True); comments_enabled=models.BooleanField(default=False); registration_enabled=models.BooleanField(default=False); maintenance_mode=models.BooleanField(default=False)
    telegram_enabled=models.BooleanField(default=False); github_enabled=models.BooleanField(default=False); analytics_enabled=models.BooleanField(default=True); appointments_enabled=models.BooleanField(default=True); newsletter_enabled=models.BooleanField(default=False)
    meta_title=models.CharField(max_length=180,blank=True); meta_description=models.TextField(blank=True); meta_keywords=models.CharField(max_length=500,blank=True); og_image=models.ImageField(upload_to='seo/',blank=True)
    footer_text=models.TextField(blank=True); email=models.EmailField(blank=True); phone=models.CharField(max_length=60,blank=True); location=models.CharField(max_length=160,blank=True)
    github_url=models.URLField(blank=True); linkedin_url=models.URLField(blank=True); telegram_url=models.URLField(blank=True); facebook_url=models.URLField(blank=True); instagram_url=models.URLField(blank=True); youtube_url=models.URLField(blank=True)
    maintenance_message=models.TextField(default='We are upgrading the platform. Please check back soon.',blank=True)
    def __str__(self): return self.site_name
    class Meta: verbose_name='Website Settings'; verbose_name_plural='Website Settings'

class Profile(TimeStamped):
    name=models.CharField(max_length=120); headline=models.CharField(max_length=255); bio=models.TextField(); photo=models.ImageField(upload_to='profile/',blank=True); cv=models.FileField(upload_to='cv/',blank=True)
    portrait_width=models.PositiveSmallIntegerField(default=220,validators=[MinValueValidator(130),MaxValueValidator(240)],verbose_name='Homepage portrait width (px)')
    portrait_height=models.PositiveSmallIntegerField(default=250,validators=[MinValueValidator(170),MaxValueValidator(250)],verbose_name='Homepage portrait height (px)')
    email=models.EmailField(blank=True); phone=models.CharField(max_length=50,blank=True); location=models.CharField(max_length=120,blank=True); availability=models.CharField(max_length=120,blank=True)
    github=models.URLField(blank=True); linkedin=models.URLField(blank=True); telegram=models.URLField(blank=True); website=models.URLField(blank=True)
    def __str__(self): return self.name

class Skill(TimeStamped):
    name=models.CharField(max_length=100); category=models.CharField(max_length=100,blank=True); level=models.PositiveIntegerField(default=80); icon=models.CharField(max_length=80,blank=True); order=models.PositiveIntegerField(default=0); featured=models.BooleanField(default=True)
    class Meta: ordering=['order','name']
    def __str__(self): return self.name

class Service(TimeStamped):
    title=models.CharField(max_length=180); slug=models.SlugField(unique=True,blank=True); summary=models.CharField(max_length=300); description=models.TextField(); icon=models.CharField(max_length=80,blank=True); image=models.ImageField(upload_to='services/',blank=True); featured=models.BooleanField(default=True); published=models.BooleanField(default=True); order=models.PositiveIntegerField(default=0)
    def save(self,*a,**kw):
        if not self.slug:self.slug=slugify(self.title)
        super().save(*a,**kw)
    def __str__(self): return self.title

class Project(TimeStamped):
    title=models.CharField(max_length=180); slug=models.SlugField(unique=True,blank=True); summary=models.CharField(max_length=300); description=models.TextField(); image=models.ImageField(upload_to='projects/',blank=True)
    technologies=models.CharField(max_length=500,blank=True); demo_url=models.URLField(blank=True); source_url=models.URLField(blank=True); github_repo=models.CharField(max_length=220,blank=True); featured=models.BooleanField(default=False); published=models.BooleanField(default=True); order=models.PositiveIntegerField(default=0)
    def save(self,*a,**kw):
        if not self.slug:self.slug=slugify(self.title)
        super().save(*a,**kw)
    def __str__(self): return self.title

class Certificate(TimeStamped):
    title=models.CharField(max_length=180); issuer=models.CharField(max_length=180); issue_date=models.DateField(null=True,blank=True); credential_id=models.CharField(max_length=180,blank=True); credential_url=models.URLField(blank=True); file=models.FileField(upload_to='certificates/',blank=True); featured=models.BooleanField(default=False); order=models.PositiveIntegerField(default=0)
    def __str__(self): return self.title

class Experience(TimeStamped):
    role=models.CharField(max_length=180); organization=models.CharField(max_length=180); start_date=models.DateField(null=True,blank=True); end_date=models.DateField(null=True,blank=True); current=models.BooleanField(default=False); description=models.TextField(); location=models.CharField(max_length=150,blank=True)
    def __str__(self): return f'{self.role} — {self.organization}'

class Education(TimeStamped):
    institution=models.CharField(max_length=180); degree=models.CharField(max_length=180); field=models.CharField(max_length=180,blank=True); start_date=models.DateField(null=True,blank=True); end_date=models.DateField(null=True,blank=True); current=models.BooleanField(default=False); description=models.TextField(blank=True)
    def __str__(self): return f'{self.degree} — {self.institution}'

class Testimonial(TimeStamped):
    name=models.CharField(max_length=120); role=models.CharField(max_length=180,blank=True); company=models.CharField(max_length=180,blank=True); quote=models.TextField(); photo=models.ImageField(upload_to='testimonials/',blank=True); published=models.BooleanField(default=True); order=models.PositiveIntegerField(default=0)
    def __str__(self): return self.name

class Page(TimeStamped):
    title=models.CharField(max_length=180); slug=models.SlugField(unique=True); content=models.TextField(blank=True); published=models.BooleanField(default=True); menu=models.BooleanField(default=False); order=models.PositiveIntegerField(default=0); seo_title=models.CharField(max_length=180,blank=True); seo_description=models.TextField(blank=True)
    def __str__(self): return self.title

class Section(TimeStamped):
    TYPES=[('hero','Hero'),('about','About'),('skills','Skills'),('projects','Projects'),('services','Services'),('experience','Experience'),('education','Education'),('certificates','Certificates'),('testimonials','Testimonials'),('posts','Posts'),('contact','Contact'),('custom','Custom')]
    name=models.CharField(max_length=120); section_type=models.CharField(max_length=30,choices=TYPES); enabled=models.BooleanField(default=True); order=models.PositiveIntegerField(default=0); title=models.CharField(max_length=180,blank=True); subtitle=models.CharField(max_length=300,blank=True); content=models.TextField(blank=True); settings=models.JSONField(default=dict,blank=True)
    class Meta: ordering=['order','id']
    def __str__(self): return self.name

    @property
    def template_name(self):
        return f'core/sections/{self.section_type}.html'

class Post(TimeStamped):
    TYPES=[('text','Text'),('photo','Photo'),('gallery','Gallery'),('video','Video'),('document','Document'),('link','Link'),('announcement','Announcement')]
    LOCATIONS=[('home','Homepage'),('about','About'),('projects','Projects'),('blog','Blog'),('services','Services'),('footer','Footer'),('sidebar','Sidebar'),('popup','Popup'),('custom','Custom')]
    STATUS=[('draft','Draft'),('review','Review'),('scheduled','Scheduled'),('published','Published'),('archived','Archived')]
    title=models.CharField(max_length=200); slug=models.SlugField(unique=True,blank=True); post_type=models.CharField(max_length=30,choices=TYPES,default='text'); body=models.TextField(blank=True); image=models.ImageField(upload_to='posts/',blank=True); video_url=models.URLField(blank=True); external_url=models.URLField(blank=True); document=models.FileField(upload_to='documents/',blank=True); gallery=models.JSONField(default=list,blank=True); locations=models.JSONField(default=list,blank=True); custom_locations=models.CharField(max_length=500,blank=True); status=models.CharField(max_length=20,choices=STATUS,default='draft'); publish_at=models.DateTimeField(null=True,blank=True); author=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True); seo_title=models.CharField(max_length=180,blank=True); seo_description=models.TextField(blank=True); tags=models.CharField(max_length=500,blank=True)
    def save(self,*a,**kw):
        if not self.slug:self.slug=slugify(self.title)
        super().save(*a,**kw)
    def __str__(self): return self.title
    @property
    def is_live(self): return self.status=='published' or (self.status=='scheduled' and self.publish_at and self.publish_at<=timezone.now())

class LegalPage(TimeStamped):
    title=models.CharField(max_length=180); slug=models.SlugField(unique=True); content=models.TextField(); published=models.BooleanField(default=True); seo_description=models.TextField(blank=True)
    def __str__(self): return self.title

class ContactMessage(TimeStamped):
    name=models.CharField(max_length=120); email=models.EmailField(); subject=models.CharField(max_length=200); message=models.TextField(); read=models.BooleanField(default=False); replied=models.BooleanField(default=False); ip_address=models.GenericIPAddressField(null=True,blank=True)
    def __str__(self): return f'{self.name}: {self.subject}'

class Appointment(TimeStamped):
    name=models.CharField(max_length=120); email=models.EmailField(); phone=models.CharField(max_length=60,blank=True); date=models.DateTimeField(); topic=models.CharField(max_length=200); notes=models.TextField(blank=True); status=models.CharField(max_length=20,choices=[('pending','Pending'),('confirmed','Confirmed'),('cancelled','Cancelled')],default='pending')
    def __str__(self): return f'{self.name} — {self.date}'

class NewsletterSubscriber(TimeStamped):
    email=models.EmailField(unique=True); active=models.BooleanField(default=True); token=models.CharField(max_length=80,blank=True)
    def __str__(self): return self.email

class MediaAsset(TimeStamped):
    title=models.CharField(max_length=180); file=models.FileField(upload_to='library/'); alt_text=models.CharField(max_length=255,blank=True); caption=models.CharField(max_length=500,blank=True); folder=models.CharField(max_length=120,default='general'); uploaded_by=models.ForeignKey(User,on_delete=models.SET_NULL,null=True,blank=True)
    def __str__(self): return self.title

class SocialLink(TimeStamped):
    name=models.CharField(max_length=80); url=models.URLField(); icon=models.CharField(max_length=80,blank=True); enabled=models.BooleanField(default=True); order=models.PositiveIntegerField(default=0)
    class Meta: ordering=['order','id']
    def __str__(self): return self.name

class AutomationRule(TimeStamped):
    name=models.CharField(max_length=150); enabled=models.BooleanField(default=True); event=models.CharField(max_length=80); action=models.CharField(max_length=80); config=models.JSONField(default=dict,blank=True); last_run=models.DateTimeField(null=True,blank=True); last_error=models.TextField(blank=True)
    def __str__(self): return self.name

class Integration(TimeStamped):
    PROVIDERS=[('github','GitHub'),('telegram','Telegram'),('gemini','Gemini AI'),('openai','OpenAI'),('smtp','Email/SMTP'),('analytics','Analytics'),('webhook','Webhook')]
    provider=models.CharField(max_length=30,choices=PROVIDERS,unique=True); enabled=models.BooleanField(default=False); public_identifier=models.CharField(max_length=255,blank=True); settings=models.JSONField(default=dict,blank=True); last_sync=models.DateTimeField(null=True,blank=True); last_error=models.TextField(blank=True)
    def __str__(self): return self.get_provider_display()

class AnalyticsEvent(TimeStamped):
    EVENT_TYPES=[('pageview','Page View'),('download','Download'),('contact','Contact'),('ai','AI Question'),('click','Click')]
    event_type=models.CharField(max_length=30,choices=EVENT_TYPES); path=models.CharField(max_length=500,blank=True); referrer=models.CharField(max_length=500,blank=True); user_agent=models.TextField(blank=True); session_key=models.CharField(max_length=100,blank=True); ip_hash=models.CharField(max_length=128,blank=True); metadata=models.JSONField(default=dict,blank=True)
    def __str__(self): return f'{self.event_type} — {self.path}'

class AIConversation(TimeStamped):
    session_key=models.CharField(max_length=100); question=models.TextField(); answer=models.TextField(); provider=models.CharField(max_length=40,blank=True); success=models.BooleanField(default=True)
    def __str__(self): return self.question[:70]

class ActivityLog(models.Model):
    user=models.ForeignKey(User,on_delete=models.SET_NULL,null=True); action=models.CharField(max_length=255); path=models.CharField(max_length=500,blank=True); ip_address=models.GenericIPAddressField(null=True,blank=True); created_at=models.DateTimeField(auto_now_add=True); metadata=models.JSONField(default=dict,blank=True)
    class Meta: ordering=['-created_at']

class WebhookEndpoint(TimeStamped):
    name=models.CharField(max_length=120); url=models.URLField(); secret=models.CharField(max_length=255,blank=True); enabled=models.BooleanField(default=True); events=models.JSONField(default=list,blank=True); last_sent=models.DateTimeField(null=True,blank=True); last_error=models.TextField(blank=True)
    def __str__(self): return self.name
