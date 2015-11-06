# Conspace Registration

Conspace is a free and open source convention administration application,
written for the Django platform.  The goal is to provide a simple, easy
to use convention system, enabling web-based registration and credit card
payment and an associated administrative backend to allow checking in
attendees, printing registration badges, and managing attendee
information.

## How to use

Conspace currently relies on user accounts to accept each registration.
This means some user management backend (generally Django's built-in
user backend) should be used.  It is outside the scope of this
application to handle user management, since other applications
exist for this purpose, such as Mezzanine.  A sample site for Conspace
also exists to provide base templates that may be modified as desired.

Note: the sample templates distributed with the app require the bootstrap3
Django application.

Additionally, some small customizations are required to settings.py:
```
# JSON Serializer for sessions doesn't work with everything. Use Pickle.
SESSION_SERIALIZER = 'django.contrib.sessions.serializers.PickleSerializer'
```

Adding the appropriate path to urls.py:
```
...

from register.views import Register

urlpatterns = patterns('',
    url(r'^register/', Register.as_view(), name='convention_registration'),
)
```

### App Settings

Once you've got the app running, log into the admin panel to add your first
convention.  You'll want to specify all fields, including a description and
agreement text (these currently aren't used), the total number of dealer
registrations to limit to (can be zero to disable dealer registrations),
if the convention is currently active and registration is open, an email
address used as the "From:" address for system-generated emails, and the
publishable and secret API keys for Stripe (https://www.stripe.com).

Note that only one convention can be active at any one time.

You'll also want to add at least one registration level: the squence field
is used for sorting the registration levels on the page.  Assign the level
to the convention, number of registrations the level is limited to (zero
for unlimited), registration level title displayed to the user, price,
description (currently unused), and the background image, added text on
the registration level, and color displayed while printing the badge, and
a date and time to automatically deactivate the registration level.

Shirt sizes are also displayed on the registration form for additional
information.

Finally, payment methods can be added: note that the "Is credit" flag
is used to determine if the payment method should redirect to Stripe.  If
"Is credit" is not checked, the registration is added to the database,
but the registration is not marked as paid in the database until payment
is added in the administration panel.  Only "Active" payment methods are
shown to users.

Most of the options for modifying registrations are available under the
Registration administration page.  Payment can be added/refunded,
badges can be printed, attendees can be checked in, and summary lists
of registrations and non-checked-in attendees can be fetched.  Note that
all actions require checking the attendees you wish to modify first.

Coupon codes can also be added to provide discounts during registration.
These can be added on a dollar amount or percent amount.

The application is currently tested against Django 1.7.10 on at least
Python 2.7 and 3.3.  If we've done something horribly wrong that
introduces an incompatibility in either dependency, please accept our
sincere apologies and file an issue report so we may investigate.

The application is also built on the Stripe API.  This means the
Stripe Python APIs should be installed (currently tested with
version 1.18.0), and a Stripe key should exist.  You may register
with Stripe for a free developer account, but we are unable to provide
support for their services.

## Contributing

Contributions to Conspace are welcome, however by sumbitting
contributions back to the Conspace project, you agree to assign all
rights to us.  While we have no intentions to change the license
of the project, this greatly simplifies management of the copyrights
in the future.  If you are uncomfortable with this policy, you are
still welcome to use and modify the code under the terms of the BSD
license, but we regret that we will be unable to accept any patches.

Should the project reach a size where it becomes necessary, a company
will be formed to manage the rights and ensure the continued free
availability of the application for all.  Since this project is still
in its infancy, there isn't currently a need.
