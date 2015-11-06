# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='BadgeAssignment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('printed_on', models.DateTimeField(auto_now_add=True)),
                ('printed_by', models.ForeignKey(related_name='printed_by_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Convention',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('agreement', models.TextField()),
                ('dealer_limit', models.IntegerField()),
                ('registration_open', models.BooleanField(default=True)),
                ('active', models.BooleanField(default=False)),
                ('contact_email', models.EmailField(max_length=75)),
                ('stripe_publishable_key', models.CharField(max_length=255)),
                ('stripe_secret_key', models.CharField(max_length=255)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CouponCode',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('code', models.CharField(max_length=255)),
                ('discount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('percent', models.BooleanField(default=False)),
                ('single_use', models.BooleanField(default=False)),
                ('convention', models.ForeignKey(to='register.Convention')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='CouponUse',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('coupon', models.ForeignKey(to='register.CouponCode')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='DealerRegistrationLevel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('number_tables', models.IntegerField()),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('convention', models.ForeignKey(to='register.Convention')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Payment',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('payment_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_received', models.DateTimeField(auto_now_add=True)),
                ('payment_extra', models.CharField(null=True, max_length=255, blank=True)),
                ('created_by', models.ForeignKey(null=True, related_name='created_by_user', to=settings.AUTH_USER_MODEL)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='PaymentMethod',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('seq', models.IntegerField()),
                ('name', models.CharField(max_length=255)),
                ('active', models.BooleanField(default=True)),
                ('is_credit', models.BooleanField(default=False)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Registration',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('first_name', models.CharField(max_length=255)),
                ('last_name', models.CharField(max_length=255)),
                ('badge_name', models.CharField(max_length=32)),
                ('email', models.EmailField(max_length=75)),
                ('address', models.CharField(max_length=255)),
                ('city', models.CharField(max_length=255)),
                ('state', models.CharField(max_length=255)),
                ('postal_code', models.CharField(max_length=255)),
                ('country', models.CharField(max_length=255)),
                ('birthday', models.DateField()),
                ('volunteer', models.BooleanField(default=False, verbose_name='Contact me for volunteering opportunities')),
                ('volunteer_phone', models.CharField(max_length=20, blank=True, verbose_name='Phone Number (only required if volunteering)')),
                ('notes', models.TextField(null=True, blank=True)),
                ('checked_in', models.BooleanField(default=False)),
                ('ip', models.GenericIPAddressField()),
                ('dealer_registration_level', models.ForeignKey(null=True, to='register.DealerRegistrationLevel', blank=True, verbose_name='Dealer Tables')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='RegistrationLevel',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('seq', models.IntegerField()),
                ('limit', models.IntegerField()),
                ('title', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
                ('description', models.TextField()),
                ('background', models.CharField(max_length=255)),
                ('added_text', models.CharField(null=True, max_length=255, blank=True)),
                ('color', models.CharField(max_length=7)),
                ('deadline', models.DateTimeField()),
                ('active', models.BooleanField(default=True)),
                ('convention', models.ForeignKey(to='register.Convention')),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ShirtSize',
            fields=[
                ('id', models.AutoField(serialize=False, verbose_name='ID', primary_key=True, auto_created=True)),
                ('seq', models.IntegerField()),
                ('size', models.CharField(max_length=20)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AddField(
            model_name='registration',
            name='registration_level',
            field=models.ForeignKey(to='register.RegistrationLevel'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='registration',
            name='shirt_size',
            field=models.ForeignKey(to='register.ShirtSize'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='registration',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='payment_method',
            field=models.ForeignKey(to='register.PaymentMethod'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='refunded_by',
            field=models.ForeignKey(null=True, related_name='refunded_by_user', blank=True, to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='payment',
            name='registration',
            field=models.ForeignKey(to='register.Registration'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='couponuse',
            name='registration',
            field=models.ForeignKey(to='register.Registration'),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='couponcode',
            name='force_dealer_registration_level',
            field=models.ForeignKey(null=True, to='register.DealerRegistrationLevel', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='couponcode',
            name='force_registration_level',
            field=models.ForeignKey(null=True, to='register.RegistrationLevel', blank=True),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='badgeassignment',
            name='registration',
            field=models.ForeignKey(to='register.Registration'),
            preserve_default=True,
        ),
    ]
