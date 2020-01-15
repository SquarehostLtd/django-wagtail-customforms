from django.conf import settings
from django import forms
from django.utils.html import mark_safe
import requests


class ReCaptchaWidget(forms.Widget):
    def render(self, name, value, attrs=None, renderer=None):
        from django.utils.html import mark_safe
        return mark_safe('<script src="https://www.google.com/recaptcha/api.js"></script><div class="g-recaptcha" data-sitekey="%s"></div><input type="hidden" name="g_recaptcha" value="%s">' % (self.attrs.get('site-key'), self.attrs.get('site-key')))


class CaptchaField(forms.CharField):
    widget = ReCaptchaWidget

    def __init__(self, *args, **kwargs):
        super(CaptchaField, self).__init__(*args, **kwargs)
        self.label = ''
        self.site_key = settings.GOOGLE_RECAPTCHA_SITE_KEY
        self.widget.attrs['site-key'] = self.site_key

    def validate(self, value):
        super().validate(value)
        resp = requests.post('https://www.google.com/recaptcha/api/siteverify', data={
            'secret': settings.GOOGLE_RECAPTCHA_SECRET_KEY,
            'response': value[2:-2]
        })
        if not resp.json().get('success'):
            raise forms.ValidationError(
                _('Invalid value: %(value)s'),
                code='invalid',
                params={'value': value},
            )
        return value
