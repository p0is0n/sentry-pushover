#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Sentry-Pushover
=============

License
-------
Copyright 2012 Janez Troha
Copyright 2013 p0is0n

This file is part of Sentry-Pushover.

Sentry-Pushover is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

Sentry-Pushover is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with Sentry-Pushover.  If not, see <http://www.gnu.org/licenses/>.
'''

import time
import logging

from django import forms
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.template import Template

from sentry.utils import settings
from sentry.plugins import Plugin
from sentry.conf import server
from sentry.utils.http import absolute_uri
from sentry.web.helpers import render_to_string
from sentry.constants import LOG_LEVELS

import sentry_pushover
import requests


message_template = 'sentry_pushover/error.txt'
message_template_alert = 'sentry_pushover/alert.txt'

choices_levels = ((i, level.upper()) for i, level in LOG_LEVELS.iteritems())
choices_sounds = ((
    ('pushover', 'Pushover (default)'),
    ('bike', 'Bike'),
    ('bugle', 'Bugle'),
    ('cashregister', 'Cash Register'),
    ('classical', 'Classical'),
    ('cosmic', 'Cosmic'),
    ('falling', 'Falling'),
    ('gamelan', 'Gamelan'),
    ('incoming', 'Incoming'),
    ('intermission', 'Intermission'),
    ('magic', 'Magic'),
    ('mechanical', 'Mechanical'),
    ('pianobar', 'Piano Bar'),
    ('siren', 'Siren'),
    ('spacealarm', 'Space Alarm'),
    ('tugboat', 'Tug Boat'),
    ('alien', 'Alien Alarm (long)'),
    ('climb', 'Climb (long)'),
    ('persistent', 'Persistent (long)'),
    ('echo', 'Pushover Echo (long)'),
    ('updown', 'Up Down (long)'),
    ('none', 'None (silent)')
))

choices_priority = ((
    ('0', 'Normal'),
    ('-1', 'Quiet'),
    ('1', 'High'),
))

API_URL_MESSAGE = 'https://api.pushover.net/1/messages.json'
API_CHARSET = 'utf-8'


class PushoverSettingsForm(forms.Form):

    userkey = forms.CharField(help_text='Your user key. See https://pushover.net/', required=True)
    apikey = forms.CharField(help_text='Application API token. See https://pushover.net/apps/', required=True)
    new_only = forms.BooleanField(help_text='Only send new messages.', required=False)
    severity = forms.ChoiceField(choices=choices_levels, help_text="Don't send notifications for events below this level.", required=True)
    sound = forms.ChoiceField(choices=choices_sounds, help_text="When sending notifications through the Pushover API, the sound parameter may be set to one of the following.", required=True)
    priority = forms.ChoiceField(choices=choices_priority, help_text="Priority notifications")


class PushoverNotifications(Plugin):

    BASE_MAXIMUM_MESSAGE_LENGTH = 512

    author = 'Janez Troha & p0is0n'
    author_url = 'http://dz0ny.info'

    title = 'Pushover'
    description = 'Event notification to Pushover.'

    conf_title = 'Pushover'
    conf_key = 'pushover'

    slug = 'pushover'

    resource_links = [
        ('Bug Tracker', 'https://github.com/p0is0n/sentry-pushover/issues'),
        ('Source', 'https://github.com/p0is0n/sentry-pushover'),
    ]

    version = sentry_pushover.VERSION
    project_conf_form = PushoverSettingsForm

    def get_project_url(self, project):
        return absolute_uri(reverse('sentry-stream', args=[
            project.team.slug,
            project.slug,
        ]))

    def is_configured(self, project):
        return bool(all(self.get_option(key, project)
                    for key in ('userkey', 'apikey', 'severity')))

    def notify_users(self, group, event, fail_silently=False):
        project = event.project
        interface_list = []

        for interface in event.interfaces.itervalues():
            body = interface.to_string(event)

            if not body:
                # Skip
                continue

            interface_list.append((interface.get_title(), mark_safe(body)))

        title = ('[%s] %s' % (
            project.name.encode(API_CHARSET),
            unicode(group.get_level_display().upper().encode(API_CHARSET))))

        link = group.get_absolute_url()
        message = render_to_string(message_template, ({
            'group': group,
            'event': event,
            'tags': event.get_tags(),
            'link': link,
            'interfaces': interface_list
        }))

        if len(message) > self.BASE_MAXIMUM_MESSAGE_LENGTH:
            message = message[:self.BASE_MAXIMUM_MESSAGE_LENGTH - 4] + ' ...'
            message = message.encode(API_CHARSET)
        else:
            message = message.encode(API_CHARSET)

        self.send_notification(title, message, link, project)

    def on_alert(self, alert, **kwargs):
        project = alert.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return

        title = ('[{0}] ALERT'.format(
            project.name.encode(API_CHARSET)
        ))

        link = alert.get_absolute_url()
        message = alert.message.encode(API_CHARSET)

        self.send_notification(title, message, link, project)

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        project = event.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return

        if new_only and not is_new:
            return

        if group.level < int(self.get_option('severity', project)):
            return

        self.notify_users(group, event)

    def send_notification(self, title, message, link, project):
        params = ({
            'user': self.get_option('userkey', project),
            'token': self.get_option('apikey', project),
            'message': message,
            'title': title,
            'url': link,
            'url_title': 'More info',
            'sound': (self.get_option('sound', project) or 'pushover'),
            'priority': (self.get_option('priority', project) or 0),
        })

        requests.post(API_URL_MESSAGE, params=params)
