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

from sentry.utils import settings
from sentry.plugins.bases.notify import NotifyPlugin, NotifyConfigurationForm
from sentry.conf import server
from sentry.utils.http import absolute_uri

import sentry_pushover
import requests


class PushoverSettingsForm(NotifyConfigurationForm):

    choices = ((logging.CRITICAL, 'CRITICAL'), (logging.ERROR, 'ERROR'), (logging.WARNING,
               'WARNING'), (logging.INFO, 'INFO'), (logging.DEBUG, 'DEBUG'))

    userkey = forms.CharField(help_text='Your user key. See https://pushover.net/')
    apikey = forms.CharField(help_text='Application API token. See https://pushover.net/apps/')
    new_only = forms.BooleanField(help_text='Only send new messages.', required=False)
    severity = forms.ChoiceField(choices=choices, help_text="Don't send notifications for events below this level.")
    priority = forms.BooleanField(required=False, help_text='High-priority notifications, also bypasses quiet hours.')


class PushoverNotifications(NotifyPlugin):

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
        return all(self.get_option(key, project) for key in ('userkey', 'apikey'))

    def notify_users(self, group, event, fail_silently=False):
        project = event.project
        new_only = self.get_option('new_only', project)

        title = ('[%s] %s' % (
            project.name.encode('utf-8'),
            unicode(event.get_level_display()).upper().encode('utf-8')
        ))

        link = group.get_absolute_url()

        message = ''
        message += event.error().encode('utf-8').splitlines()[0]
        message += 'Server: %s\n' % event.server_name
        message += 'Group: %s\n' % event.group
        message += 'Logger: %s\n' % event.logger
        message += 'Message: %s\n' % event.message

        self.send_notification(title, message, link, project)

    def on_alert(self, alert, **kwargs):
        project = alert.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return

        title = ('[{0}] ALERT'.format(
            project.name.encode('utf-8')
        ))

        link = alert.get_absolute_url()
        message = alert.message.encode('utf-8')

        self.send_notification(title, message, link, project)

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        project = event.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return 

        if new_only and not is_new:
            return

        if event.level < int(self.get_option('severity', project)):
            return

        if not self.should_notify(group, event):
            return

        self.notify_users(group, event)

    def send_notification(self, title, message, link, project):
        # see https://pushover.net/api

        params = ({
            'user': self.get_option('userkey', project),
            'token': self.get_option('apikey', project),
            'message': message,
            'title': title,
            'url': link,
            'url_title': 'More info',
            #'priority': self.get_option('priority', project),
        })

        requests.post('https://api.pushover.net/1/messages.json', params=params)
