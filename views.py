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

from django.shortcuts import render
from django.views.generic import View

from register.forms import RegistrationForm
from register.models import Convention, RegistrationLevel, Payment, PaymentMethod

import stripe

class Register(View):
    def get(self, request):
        form = RegistrationForm()
        return render(request, 'register/register.html', {'form': form})

    def post(self, request):
        if 'confirm' in request.POST.keys():
            if 'stripeToken' in request.POST.keys():
                # Process Stripe payment
                try:
                    form = request.session['form']
                    stripe.api_key = Convention.objects.get().stripe_secret_key
                    reglevel = RegistrationLevel.objects.get(id=form['registration_level'].value)
                    charge = stripe.Charge.create(
                                                  amount=reglevel.price * 100,
                                                  currency="USD",
                                                  card=request.POST['stripeToken'],
                                                  description=reglevel.title)
                    reg = form.save(commit=False)
                    reg.ip = request.META['REMOTE_ADDR']
                    try:
                        reg.save()
                        method = PaymentMethod.objects.get(id=form['payment_method'].value)
                        payment = Payment(registration_id=reg,
                                          payment_method=method,
                                          payment_amount=reglevel.price)
                        payment.save()
                    except Exception, e:
                        charge.refunds.create()
                        raise e
                    request.session.pop('form')
                except stripe.error.CardError, e:
                    # Pass a "Payment Declined" error to the user
                    form.errors['__all__'] = form.error_class([e])
                    request.session.pop('form')
                    return render(request, 'register/register.html', {'form': form})
                return render(request, 'register/success.html')
            else:
                # Confirm normally; don't create payment record
                reg = request.session['form'].save(commit=False)
                reg.ip = request.META['REMOTE_ADDR']
                reg.save()
                request.session.pop('form')
                return render(request, 'register/success.html')
        else:
            form = RegistrationForm(request.POST)
            if form.is_valid():
                request.session['form'] = form
                convention = Convention.objects.get()
                reglevel = RegistrationLevel.objects.get(id=form['registration_level'].value)
                method = PaymentMethod.objects.get(id=form['payment_method'].value)
                return render(request, 'register/confirm.html', {'convention': convention,
                                                                 'form': form,
                                                                 'registration_level': reglevel.title,
                                                                 'registration_amount': reglevel.price * 100,
                                                                 'is_credit': method.is_credit,
                                                                 'method': method.name,
                                                                 'birthday': form.cleaned_data['birthday'].strftime("%B %d, %Y")})
            else:
                return render(request, 'register/register.html', {'form': form})