import datetime

from django import forms

from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _

class LoanBookForm(forms.Form):
    return_date = forms.DateField(
            help_text="Date entre aujourd'hui et 4 semamines (défaut 3).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Date antérieure invalide'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(
                    _('Date passée 4 semaines'))

        # Remember to always return the cleaned data.
        return data


class RenewBookForm(forms.Form):
    renewal_date = forms.DateField(
            help_text="Date entre aujourd'hui et 4 semamines (défaut 3).")

    def clean_renewal_date(self):
        data = self.cleaned_data['renewal_date']

        # Check if a date is not in the past.
        if data < datetime.date.today():
            raise ValidationError(_('Date antérieure invalide'))

        # Check if a date is in the allowed range (+4 weeks from today).
        if data > datetime.date.today() + datetime.timedelta(weeks=4):
            raise ValidationError(
                    _('Date passée 4 semaines'))

        # Remember to always return the cleaned data.
        return data

# from .models import Book, Category

# class BookListForm(forms.ModelForm):
#     class Meta:
#         model = Book
#         fields = '__all__'

#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.fields['category'].queryset = Category.objects.none()

#         if 'section' in self.data:
#             try:
#                 country_id = int(self.data.get(''))
#                 self.fields['city'].queryset = City.objects.filter(country_id=country_id).order_by('name')
#             except (ValueError, TypeError):
#                 pass  # invalid input from the client; ignore and fallback to empty City queryset
#         elif self.instance.pk:
#             self.fields['city'].queryset = self.instance.country.city_set.order_by('name')
