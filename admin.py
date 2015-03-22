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
    amount = forms.FloatField(widget=forms.NumberInput(attrs={'size': '5'}), required=False)
    method = forms.ModelChoiceField(empty_label=None, queryset=PaymentMethod.objects.order_by('seq'), required=False)

class RegistrationAdmin(admin.ModelAdmin):
    list_display = ('name', 'badge_name', 'registration_level', 'shirt_size', 'checked_in', 'paid', 'badge_number')
    list_filter = ('registration_level', 'shirt_size', 'checked_in', 'volunteer')
    search_fields = ['name', 'badge_name', 'email', 'badgeassignment__id']
    actions = ['mark_checked_in', 'apply_payment', 'refund_payment', 'print_badge']
    action_form = RegistrationAdminForm
    ordering = ('id',)

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
                        stripe.api_key = Convention.objects.get().stripe_secret_key
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
            badge = BadgeAssignment(registration=user, printed_by=request.user)
            badge.save()
            user.badge_number = '%05d' % badge.id
        if printable:
            transaction.commit()
            transaction.set_autocommit(ac)
            return render(request, 'register/badge.html', {'badges': queryset})
        else:
            transaction.rollback()
            transaction.set_autocommit(ac)

admin.site.register(Registration, RegistrationAdmin)
admin.site.register(Payment)

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
