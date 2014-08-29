# Copyright (c) 2014-2015, Doug Kelly
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from django import forms
from django.core.exceptions import ValidationError
from django.forms.extras.widgets import SelectDateWidget
from register.models import Registration
from register.models import PaymentMethod
from datetime import date

BIRTH_YEAR_CHOICES = list(range(date.today().year, 1900, -1))

def validate_birthday(value):
    years = date.today().year - value.year

    try:
        birthdate = date(year=date.today().year, month=value.month, day=value.day)
    except ValueError as e:
        if value.month == 2 and value.day == 29:
            birthdate = date(year=date.today().year, month=2, day=28)
        else:
            raise e

    if date.today() < birthdate:
        years -= 1

    if years < 18:
        raise ValidationError("You must be 18 or older to register")

class RegistrationForm(forms.ModelForm):
    class Meta:
        model = Registration
        fields = [
                  'name',
                  'badge_name',
                  'email',
                  'address',
                  'city',
                  'state',
                  'postal_code',
                  'country',
                  'registration_level',
                  'birthday',
                ]
        widgets = {
                   'birthday': SelectDateWidget(years=BIRTH_YEAR_CHOICES),
                   'registration_level': forms.RadioSelect(),
                }

    payment_method = forms.ModelChoiceField(widget=forms.RadioSelect, empty_label=None, queryset=PaymentMethod.objects.filter(active=True))

    def clean_birthday(self):
        data = self.cleaned_data['birthday']
        validate_birthday(data)
        return data

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['registration_level'].empty_label = None