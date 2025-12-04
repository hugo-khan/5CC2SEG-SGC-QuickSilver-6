#!/usr/bin/env python
"""
Quick script to fix the Django Site configuration for Google OAuth.
Run this with: python manage.py shell < fix_google_oauth.py
Or run the commands manually in Django shell.
"""

from django.contrib.sites.models import Site

# Update Site to match your development server
site = Site.objects.get(id=1)
site.domain = '127.0.0.1:8001'  # Match your server port
site.name = 'Recipify'
site.save()

print(f"✅ Site updated:")
print(f"   Domain: {site.domain}")
print(f"   Name: {site.name}")
print(f"\n📝 Make sure Google Cloud Console has this redirect URI:")
print(f"   http://{site.domain}/accounts/google/login/callback/")

