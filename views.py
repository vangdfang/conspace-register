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

# Create your views here.
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.views.generic import View
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
import logging

from register.forms import RegistrationForm
from register.models import Convention, RegistrationLevel, DealerRegistrationLevel, Payment, PaymentMethod, ShirtSize, CouponCode, CouponUse

import stripe

class Register(View):
    def get(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/accounts/login')
        if not Convention.objects.filter(active=True).order_by('-id')[0].registration_open:
            raise PermissionDenied()
        form = RegistrationForm()
        return render(request, 'register/register.html', {'form': form})

    def post(self, request):
        if not request.user.is_authenticated():
            return HttpResponseRedirect('/accounts/login')
        if not Convention.objects.filter(active=True).order_by('-id')[0].registration_open:
            raise PermissionDenied()
        if 'confirm' in request.POST.keys():
            form = request.session['form']
            dealer_price = 0
            dealer_reglevel = None
            if form.cleaned_data['dealer_registration_level']:
                dealer_reglevel = DealerRegistrationLevel.objects.get(id=form['dealer_registration_level'].value)
                dealer_price = dealer_reglevel.price
            discount_amount = 0
            discount_percent = 0
            code = None
            reglevel = RegistrationLevel.objects.get(id=form['registration_level'].value)
            if form.cleaned_data['coupon_code']:
                code = CouponCode.objects.get(code=form.cleaned_data['coupon_code'])
                if code.percent:
                    discount_percent = code.discount
                else:
                    discount_amount = code.discount
                if code.force_registration_level:
                    reglevel = code.force_registration_level
                if code.force_dealer_registration_level:
                    dealer_reglevel = code.force_dealer_registration_level
                    dealer_price = dealer_reglevel.price
            amount = max(((reglevel.price + dealer_price - discount_amount) * (1 - discount_percent)), 0)
            if 'stripeToken' in request.POST.keys():
                # Process Stripe payment
                try:
                    stripe.api_key = Convention.objects.filter(active=True).order_by('-id')[0].stripe_secret_key
                    charge = stripe.Charge.create(
                                                  amount=int(amount) * 100,
                                                  currency="USD",
                                                  card=request.POST['stripeToken'],
                                                  description=reglevel.title)
                    reg = form.save(commit=False)
                    reg.ip = request.META['REMOTE_ADDR']
                    reg.user = request.user
                    reg.registration_level = reglevel
                    reg.dealer_registration_level = dealer_reglevel
                    try:
                        reg.save()
                        method = PaymentMethod.objects.get(id=form['payment_method'].value)
                        payment = Payment(registration=reg,
                                          payment_method=method,
                                          payment_amount=amount,
                                          payment_extra=charge.id)
                        payment.save()
                        if code:
                            couponuse = CouponUse(registration=reg,
                                                  coupon=code)
                            couponuse.save()
                    except Exception as e:
                        charge.refunds.create()
                        raise e
                    request.session.pop('form')
                except stripe.error.CardError as e:
                    # Pass a "Payment Declined" error to the user
                    form.errors['__all__'] = form.error_class([e])
                    request.session.pop('form')
                    return render(request, 'register/register.html', {'form': form})
            else:
                # Confirm normally; don't create payment record
                reg = request.session['form'].save(commit=False)
                reg.ip = request.META['REMOTE_ADDR']
                reg.user = request.user
                reg.registration_level = reglevel
                reg.dealer_registration_level = dealer_reglevel
                try:
                    reg.save()
                    if amount == 0:
                        method = PaymentMethod.objects.get(id=form['payment_method'].value)
                        payment = Payment(registration=reg,
                                          payment_method=method,
                                          payment_amount=0)
                        payment.save()
                        if code:
                            couponuse = CouponUse(registration=reg,
                                                  coupon=code)
                            couponuse.save()
                except Exception as e:
                    raise e
                request.session.pop('form')

            convention = Convention.objects.filter(active=True).order_by('-id')[0]
            try:
                send_mail('Convention Registration',
                          "We have your registration down for %s.\n\n" % ( convention.name ) +
                          'If you have any questions, please let us know!',
                          convention.contact_email,
                          [form.cleaned_data['email']], fail_silently=True)
            except Exception as e:
                logging.exception("Failed sending email")
            return render(request, 'register/success.html')
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                request.session['form'] = form
                convention = Convention.objects.filter(active=True).order_by('-id')[0]
                reglevel = RegistrationLevel.objects.get(id=form['registration_level'].value)
                dealer_price = 0
                dealer_tables = None
                if form.cleaned_data['dealer_registration_level']:
                    dealer_reglevel = DealerRegistrationLevel.objects.get(id=form['dealer_registration_level'].value)
                    dealer_price = dealer_reglevel.price
                    dealer_tables = dealer_reglevel.number_tables
                discount_amount = 0
                discount_percent = 0
                if form.cleaned_data['coupon_code']:
                    code = CouponCode.objects.get(code=form.cleaned_data['coupon_code'])
                    if code.percent:
                        discount_percent = code.discount
                    else:
                        discount_amount = code.discount
                    if code.force_registration_level:
                        reglevel = code.force_registration_level
                    if code.force_dealer_registration_level:
                        dealer_reglevel = code.force_dealer_registration_level
                        dealer_price = dealer_reglevel.price
                        dealer_tables = dealer_reglevel.number_tables

                method = PaymentMethod.objects.get(id=form['payment_method'].value)
                shirt_size = ShirtSize.objects.get(id=form['shirt_size'].value)
                amount = max(((reglevel.price + dealer_price - discount_amount) * (1 - discount_percent)), 0)
                if amount == 0:
                    method.is_credit = False

                return render(request, 'register/confirm.html', {'convention': convention,
                                                                 'form': form,
                                                                 'registration_level': reglevel.title,
                                                                 'registration_price': amount,
                                                                 'registration_amount': int(amount) * 100,
                                                                 'dealer_number_tables': dealer_tables,
                                                                 'is_credit': method.is_credit,
                                                                 'method': method.name,
                                                                 'shirt_size': shirt_size,
                                                                 'birthday': form.cleaned_data['birthday'].strftime("%B %d, %Y")})
            else:
                return render(request, 'register/register.html', {'form': form})
