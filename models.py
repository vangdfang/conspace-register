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

from django.db import models

from django.contrib.auth.models import User

# Create your models here.
class Registration(models.Model):
    user = models.ForeignKey(User)
    name = models.CharField(max_length=255)
    badge_name = models.CharField(max_length=32)
    email = models.EmailField()
    address = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    state = models.CharField(max_length=255)
    postal_code = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    birthday = models.DateField()
    registration_level = models.ForeignKey('RegistrationLevel')
    dealer_registration_level = models.ForeignKey('DealerRegistrationLevel', blank=True, null=True)
    shirt_size = models.ForeignKey('ShirtSize')
    volunteer = models.BooleanField(default=False, verbose_name='Contact me for volunteering opportunities')
    volunteer_phone = models.CharField(max_length=20, blank=True, verbose_name='Phone Number (only required if volunteering)')
    ip = models.GenericIPAddressField()

    def __unicode__(self):
        return self.name + ' [' + self.badge_name + ']'

class ShirtSize(models.Model):
    seq = models.IntegerField()
    size = models.CharField(max_length=20)

    def __unicode__(self):
        return self.size

class Payment(models.Model):
    registration = models.ForeignKey('Registration')
    payment_method = models.ForeignKey('PaymentMethod')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_received = models.DateTimeField(auto_now_add=True)

class RegistrationLevel(models.Model):
    seq = models.IntegerField()
    convention = models.ForeignKey('Convention')
    limit = models.IntegerField()
    title = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    description = models.TextField()
    background = models.CharField(max_length=255)
    color = models.CharField(max_length=7)
    deadline = models.DateTimeField()
    active = models.BooleanField(default=True)

    def __unicode__(self):
        return self.title + ' [' + "%.02f" % (self.price) + ']'

class DealerRegistrationLevel(models.Model):
    convention = models.ForeignKey('Convention')
    number_tables = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __unicode__(self):
        return str(self.number_tables) + ' [' + "%.02f" % (self.price) + ']'

class CouponCode(models.Model):
    convention = models.ForeignKey('Convention')
    code = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    percent = models.BooleanField(default=False)
    single_use = models.BooleanField(default=False)

    def __unicode__(self):
        if self.percent:
            return self.code + ' [' + str(self.discount) + '%]'
        else:
            return self.code + ' [' + "%.02f" % (self.discount) + ']'

class CouponUse(models.Model):
    registration = models.ForeignKey('Registration')
    coupon = models.ForeignKey('CouponCode')

class Convention(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    agreement = models.TextField()
    dealer_limit = models.IntegerField()
    stripe_publishable_key = models.CharField(max_length=255)
    stripe_secret_key = models.CharField(max_length=255)

    def __unicode__(self):
        return self.name

class PaymentMethod(models.Model):
    seq = models.IntegerField()
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    is_credit = models.BooleanField(default=False)

    def __unicode__(self):
        return self.name
