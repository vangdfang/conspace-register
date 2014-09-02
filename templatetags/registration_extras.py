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

from django import template
from register.models import Convention, Registration, RegistrationLevel, DealerRegistrationLevel

register = template.Library()

@register.filter
def disabled_reglevel(value):
    level = RegistrationLevel.objects.get(pk=value.choice_value)
    if level.limit and len(Registration.objects.filter(registration_level=level)) >= level.limit:
        return " disabled "
    else:
        return ""

@register.filter
def disabled_dealerreglevel(value):
    # Don't bother specifying a choice for dealers
    if not value.choice_value:
        return ""
    level = DealerRegistrationLevel.objects.get(pk=value.choice_value)
    if len(Registration.objects.filter(dealer_registration_level=level)) + level.number_tables > level.convention.dealer_limit:
        return " disabled "
    else:
        return ""
