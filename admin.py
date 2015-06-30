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

from django.conf.urls import patterns, url
from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.helpers import ActionForm
from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.shortcuts import render
from django import forms
import stripe
from register.models import *

class RegistrationAdminForm(ActionForm):
    amount = forms.FloatField(widget=forms.NumberInput(attrs={'style': 'width:auto'}), required=False)
    method = forms.ModelChoiceField(widget=forms.Select(attrs={'style': 'width:auto'}), empty_label=None, queryset=PaymentMethod.objects.order_by('seq'), required=False)
    reprint = forms.BooleanField(required=False)

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_name', 'registration_level', 'shirt_size', 'checked_in', 'paid', 'badge_number')
    list_filter = ('registration_level', 'shirt_size', 'checked_in', 'volunteer', 'registration_level__convention')
    search_fields = ['name', 'badge_name', 'email', 'badgeassignment__id']
    actions = ['mark_checked_in', 'apply_payment', 'refund_payment', 'print_badge', 'download_registration_detail']
    action_form = RegistrationAdminForm
    ordering = ('id',)

    def get_urls(self):
        urls = super(RegistrationAdmin, self).get_urls()
        my_urls = patterns('',
            url(r'^print/$', self.print_badge_list, name='print')
        )
        return my_urls + urls

    def mark_checked_in(self, request, queryset):
        queryset.update(checked_in=True)
        for id in queryset:
            self.message_user(request, '%s successfully checked in!' % id)
    mark_checked_in.short_description = 'Check in attendee'

    def apply_payment(self, request, queryset):
        try: 
            amount = request.POST['amount']
            method = PaymentMethod.objects.get(id=request.POST['method'])
        except ObjectDoesNotExist:
            method = None
        if (method and amount):
            for id in queryset:
                payment = Payment(registration=id,
                                  payment_method=method,
                                  payment_amount=float(amount),
                                  created_by=request.user)
                payment.save()
                self.message_user(request, 'Applied %.02f payment by %s to %s' % (float(amount), method, id))
        else:
            self.message_user(request, 'Must specify an amount and payment method!', messages.ERROR)

    def refund_payment(self, request, queryset):
        for id in queryset:
            payments = Payment.objects.filter(registration=id)
            for payment in payments:
                if (payment.payment_method.is_credit and payment.payment_extra):
                    try:
                        stripe.api_key = Convention.objects.filter(id=payment.registration.registration_level.convention).get().stripe_secret_key
                        charge = stripe.Charge.retrieve(payment.payment_extra)
                        refund = charge.refunds.create()
                        payment.refunded_by = request.user
                        payment.save()
                        self.message_user(request, 'Refunded %.02f payment by Stripe to %s' % (refund.amount / 100, id))
                    except stripe.error.StripeError as e:
                        self.message_user(request, 'Failed to refund %.02f payment by Stripe to %s (%s)' % (payment.payment_amount, id, e.json_body['error']['message']), messages.ERROR)
                else:
                    payment.refunded_by = request.user
                    payment.save()
                    self.message_user(request, 'Refunded %.02f payment by %s to %s' % (payment.payment_amount, payment.payment_method, id))
    refund_payment.short_description = 'Refund all payments from attendee'

    def print_badge(self, request, queryset):
        printable = True
        ac = transaction.get_autocommit()
        transaction.set_autocommit(False)
        for user in queryset:
            if not user.paid():
                self.message_user(request, 'Cannot print unpaid badge for %s' % (user), messages.ERROR)
                printable = False
            badge_number = None
            reprint = request.POST.get('reprint')
            if reprint:
                badge_number = user.badge_number()
            if not reprint or not badge_number:
                badge = BadgeAssignment(registration=user, printed_by=request.user)
                badge.save()
                badge_number = badge.id
            user.badge_number = '%05d' % int(badge_number)
        if printable:
            transaction.commit()
            transaction.set_autocommit(ac)
            return render(request, 'register/badge.html', {'badges': queryset})
        else:
            transaction.rollback()
            transaction.set_autocommit(ac)

    def print_badge_list(self, request):
        badges = Registration.objects.filter(checked_in=False).order_by('name')
        split_badges = []
        temp_list = []
        for badge in badges:
            if badge.badge_number():
                temp_list.append({'name': badge.name, 'badge_name': badge.badge_name, 'badge_number': badge.badge_number(), 'registration_level': badge.registration_level.title})
            if len(temp_list) == 25:
                split_badges.append({'list': temp_list, 'last': False})
                temp_list = []
        if len(temp_list) > 0:
            split_badges.append({'list': temp_list, 'last': True})
        return render(request, 'register/badgelist.html', {'lists': split_badges})

    def download_registration_detail(self, request, queryset):
        registration_list = []
        for badge in queryset:
            payments = Payment.objects.filter(registration=badge)
            for payment in payments:
                discount_amount = ''
                try:
                    coupon = CouponUse.objects.get(registration=badge)
                    if coupon.coupon.percent:
                        discount_amount = '%.02f' % ((coupon.coupon.discount / 100) * badge.registration_level.price)
                    else:
                        discount_amount = '%.02f' % (coupon.coupon.discount)
                except ObjectDoesNotExist:
                    pass
                registration_list.append({'name': badge.name,
                                          'badge_name': badge.badge_name.replace('"', '""'),
                                          'badge_number': badge.badge_number(),
                                          'registration_level': badge.registration_level.title.replace('"', '""'),
                                          'payment_amount': '%.02f' % payment.payment_amount,
                                          'payment_created': payment.payment_received,
                                          'received_by': payment.created_by.username.replace('"', '""') if payment.created_by else '',
                                          'refunded_by': payment.refunded_by.username.replace('"', '""') if payment.refunded_by else '',
                                          'discount_amount': discount_amount,
                                          'payment_method': payment.payment_method})
        if not payments:
            discount_amount = ''
            try:
                coupon = CouponUse.objects.get(registration=badge)
                if coupon.coupon.percent:
                    discount_amount = '%.02f' % ((coupon.coupon.discount / 100) * badge.registration_level.price)
                else:
                    discount_amount = '%.02f' % (coupon.coupon.discount)
            except ObjectDoesNotExist:
                pass
            registration_list.append({'name': badge.name,
                                      'badge_name': badge.badge_name.replace('"', '""'),
                                      'badge_number': badge.badge_number(),
                                      'registration_level': badge.registration_level.title.replace('"', '""'),
                                      'payment_amount': '0.00',
                                      'payment_created': '',
                                      'payment_refunded': '',
                                      'received_by': '',
                                      'refunded_by': '',
                                      'discount_amount': discount_amount,
                                      'payment_method': ''})
        return render(request, 'register/regdetail.csv', {'badges': registration_list}, content_type='text/csv')

admin.site.register(Registration, RegistrationAdmin)

class PaymentAdmin(admin.ModelAdmin):
    actions = ['download_payment_detail']
    list_display = ('registration', 'payment_method', 'payment_amount', 'payment_received', 'created_by', 'refunded_by')
    list_filter = ('payment_method',)
    search_fields = ['registration__name', 'registration__badge_name', 'registration__email']

    def download_payment_detail(self, request, queryset):
        registration_list = []
        for payment in queryset:
            badge = payment.registration
            discount_amount = ''
            try:
                coupon = CouponUse.objects.get(registration=badge)
                if coupon.coupon.percent:
                    discount_amount = '%.02f' % ((coupon.coupon.discount / 100) * badge.registration_level.price)
                else:
                    discount_amount = '%.02f' % (coupon.coupon.discount)
            except ObjectDoesNotExist:
                pass
            registration_list.append({'name': badge.name,
                                      'badge_name': badge.badge_name.replace('"', '""'),
                                      'badge_number': badge.badge_number(),
                                      'registration_level': badge.registration_level.title.replace('"', '""'),
                                      'payment_amount': '%.02f' % payment.payment_amount,
                                      'payment_created': payment.payment_received,
                                      'received_by': payment.created_by.username.replace('"', '""') if payment.created_by else '',
                                      'refunded_by': payment.refunded_by.username.replace('"', '""') if payment.refunded_by else '',
                                      'discount_amount': discount_amount,
                                      'payment_method': payment.payment_method})
        return render(request, 'register/regdetail.csv', {'badges': registration_list}, content_type='text/csv')

admin.site.register(Payment, PaymentAdmin)

class BadgeAssignmentAdmin(admin.ModelAdmin):
    search_fields = ['id', 'registration__name', 'registration__badge_name', 'registration__email']

admin.site.register(BadgeAssignment, BadgeAssignmentAdmin)
admin.site.register(RegistrationLevel)
admin.site.register(DealerRegistrationLevel)
admin.site.register(PaymentMethod)
admin.site.register(Convention)
admin.site.register(ShirtSize)
admin.site.register(CouponCode)
admin.site.register(CouponUse)
