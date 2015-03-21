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
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.forms.extras.widgets import SelectDateWidget
from django.utils import timezone
from register.models import Registration, PaymentMethod, RegistrationLevel, DealerRegistrationLevel, ShirtSize, CouponCode, CouponUse
from datetime import date, datetime
import re
import os

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

def build_countries():
    fp = open(os.path.join(os.path.dirname(__file__), 'countries.dat'), 'r')
    countries = fp.read().split(';')
    fp.close()
    # The Select widget expects a tuple of names and values.
    # For us, these are the same...
    return [(x,x) for x in countries]

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
                  'dealer_registration_level',
                  'birthday',
                  'shirt_size',
                  'volunteer',
                  'volunteer_phone',
                ]
        widgets = {
                   'birthday': SelectDateWidget(years=BIRTH_YEAR_CHOICES),
                   'country': forms.Select(choices=build_countries()),
                   'registration_level': forms.RadioSelect(),
                   'dealer_registration_level': forms.RadioSelect(),
                   'shirt_size': forms.RadioSelect(),
                }

    payment_method = forms.ModelChoiceField(widget=forms.RadioSelect, empty_label=None, queryset=PaymentMethod.objects.filter(active=True).order_by('seq'))
    coupon_code = forms.CharField(required=False)

    def clean_birthday(self):
        data = self.cleaned_data['birthday']
        validate_birthday(data)
        return data

    def clean_badge_name(self):
        data = self.cleaned_data['badge_name']
        # Ugh.  This is some RE magic.  space is \x20, and we want to allow all characters thru \x7e (~)
        # This will include alphanumerics and simple punctuation.
        if re.match('[^\x20-\x7e]', data):
            raise ValidationError("Badge name may only contain letters, numbers and punctuation.")

        return data

    def clean_registration_level(self):
        data = self.cleaned_data['registration_level']
        if (data.deadline <= timezone.now() or
           data.active == False or
           (data.limit and len(Registration.objects.filter(registration_level=data)) >= data.limit)):
            raise ValidationError("That registration level is no longer available.")

        return data

    def clean_dealer_registration_level(self):
        data = self.cleaned_data['dealer_registration_level']
        if data and len(Registration.objects.filter(dealer_registration_level=data)) + data.number_tables > data.convention.dealer_limit:
            raise ValidationError("That dealer registration level is no longer available.")

    def clean_payment_method(self):
        data = self.cleaned_data['payment_method']
        if data.active == False:
            raise ValidationError("That payment method is no longer available.")

        return data

    def clean_volunteer_phone(self):
        data = self.cleaned_data['volunteer_phone']
        if not data and self.cleaned_data['volunteer']:
            raise ValidationError("A contact phone number is required for volunteering.")

        return data

    def clean_coupon_code(self):
        data = self.cleaned_data['coupon_code']
        if data:
            try:
                code = CouponCode.objects.get(code=data)
            except ObjectDoesNotExist:
                code = None

            if not code:
                raise ValidationError("That coupon code is not valid.")

            if code.single_use and CouponUse.objects.filter(coupon=code):
                raise ValidationError("That coupon code has already been used.")

        return data

    def __init__(self, *args, **kwargs):
        super(RegistrationForm, self).__init__(*args, **kwargs)
        self.fields['registration_level'].empty_label = None
        self.fields['registration_level'].queryset=RegistrationLevel.objects.filter(active=True, deadline__gt=datetime.now()).order_by('seq')

        self.fields['dealer_registration_level'].empty_label = 'None'
        self.fields['dealer_registration_level'].queryset=DealerRegistrationLevel.objects.order_by('number_tables')

        self.fields['shirt_size'].empty_label = None
        self.fields['shirt_size'].queryset=ShirtSize.objects.order_by('seq')
