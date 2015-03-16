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
from django.utils.encoding import python_2_unicode_compatible
from django.core.exceptions import ObjectDoesNotExist

# Create your models here.
@python_2_unicode_compatible
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
    dealer_registration_level = models.ForeignKey('DealerRegistrationLevel', verbose_name='Dealer Tables', blank=True, null=True)
    shirt_size = models.ForeignKey('ShirtSize')
    volunteer = models.BooleanField(default=False, verbose_name='Contact me for volunteering opportunities')
    volunteer_phone = models.CharField(max_length=20, blank=True, verbose_name='Phone Number (only required if volunteering)')
    checked_in = models.BooleanField(default=False)
    ip = models.GenericIPAddressField()

    def paid(self):
        coupon = None
        try:
            coupon_use = CouponUse.objects.get(registration=self)
            coupon = coupon_use.coupon
            if (coupon and ((coupon.percent and coupon.discount == 100) or
                           (coupon.percent == False and coupon.discount == self.registration_level.price))):
                return True
        except ObjectDoesNotExist:
            pass

        try:
            payments = Payment.objects.filter(registration=self, refunded_by=None)
            payment_amount = 0
            for payment in payments:
                payment_amount += payment.payment_amount
            if (payment_amount == self.registration_level.price):
                return True
            if (coupon and ((coupon.percent and ((self.registration_level.price * coupon.discount) + payment_amount) == self.registration_level.price) or
                            (coupon.percent == False and ((payment_amount + coupon.discount) == self.registration_level.price)))):
                return True
        except ObjectDoesNotExist:
            pass

        return False
    paid.boolean = True
    paid.short_description = 'Paid?'

    def __str__(self):
        return self.name + ' [' + self.badge_name + ']'

@python_2_unicode_compatible
class ShirtSize(models.Model):
    seq = models.IntegerField()
    size = models.CharField(max_length=20)

    def __str__(self):
        return self.size

@python_2_unicode_compatible
class Payment(models.Model):
    registration = models.ForeignKey('Registration')
    payment_method = models.ForeignKey('PaymentMethod')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_received = models.DateTimeField(auto_now_add=True)
    payment_extra = models.CharField(max_length=255, null=True)
    created_by = models.ForeignKey(User, null=True, related_name="created_by_user")
    refunded_by = models.ForeignKey(User, null=True, related_name="refunded_by_user")

    def __str__(self):
        return self.registration.name + ' [' + "%.02f" % (self.payment_amount) + ']'

@python_2_unicode_compatible
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

    def __str__(self):
        return self.title + ' [' + "%.02f" % (self.price) + ']'

@python_2_unicode_compatible
class DealerRegistrationLevel(models.Model):
    convention = models.ForeignKey('Convention')
    number_tables = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)

    def __str__(self):
        return str(self.number_tables) + ' [' + "%.02f" % (self.price) + ']'

@python_2_unicode_compatible
class CouponCode(models.Model):
    convention = models.ForeignKey('Convention')
    code = models.CharField(max_length=255)
    discount = models.DecimalField(max_digits=10, decimal_places=2)
    percent = models.BooleanField(default=False)
    single_use = models.BooleanField(default=False)

    def __str__(self):
        if self.percent:
            return self.code + ' [' + "%d%%" % (self.discount) + '%]'
        else:
            return self.code + ' [' + "%.02f" % (self.discount) + ']'

class CouponUse(models.Model):
    registration = models.ForeignKey('Registration')
    coupon = models.ForeignKey('CouponCode')

@python_2_unicode_compatible
class Convention(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    agreement = models.TextField()
    dealer_limit = models.IntegerField()
    registration_open = models.BooleanField(default=True)
    contact_email = models.EmailField()
    stripe_publishable_key = models.CharField(max_length=255)
    stripe_secret_key = models.CharField(max_length=255)

    def __str__(self):
        return self.name

@python_2_unicode_compatible
class PaymentMethod(models.Model):
    seq = models.IntegerField()
    name = models.CharField(max_length=255)
    active = models.BooleanField(default=True)
    is_credit = models.BooleanField(default=False)

    def __str__(self):
        return self.name
