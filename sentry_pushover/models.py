#!/usr/bin/python
# -*- coding: utf-8 -*-

'''
Sentry-Pushover
=============

License
-------
Copyright 2012 Janez Troha

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

from sentry.utils import settings
from sentry.plugins.bases.notify import NotifyPlugin, NotifyConfigurationForm
from sentry.conf import server

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

    author = 'Janez Troha'
    author_url = 'http://dz0ny.info'

    title = 'Pushover'
    description = 'Event notification to Pushover.'

    conf_title = 'Pushover'
    conf_key = 'pushover'

    slug = 'pushover'

    resource_links = [
        ('Bug Tracker', 'https://github.com/dz0ny/sentry-pushover/issues'),
        ('Source', 'https://github.com/dz0ny/sentry-pushover'),
    ]

    version = sentry_pushover.VERSION
    project_conf_form = PushoverSettingsForm

    def is_configured(self, project):
        return all(self.get_option(key, project) for key in ('userkey', 'apikey'))

    def notify_users(self, group, event, fail_silently=False):
        project = event.project
        new_only = self.get_option('new_only', project)

        self.send_notification(self, 'title', 'message', 'link', project)

    """
    def on_alert(self, alert, **kwargs):
        project = alert.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return 

    def post_process(self, group, event, is_new, is_sample, **kwargs):
        project = event.project
        new_only = self.get_option('new_only', project)

        if not self.is_configured(project):
            return 

        if new_only and not is_new:
            return

        # https://github.com/getsentry/sentry/blob/master/src/sentry/models.py#L353
        if event.level < int(self.get_option('severity', project)):
            return

        title = '%s: %s' % (event.get_level_display().upper(), event.error().split('\n')[0])

        link = '%s/%s/group/%d/' % (settings.URL_PREFIX, group.project.slug, group.id)

        message = 'Server: %s\n' % event.server_name
        message += 'Group: %s\n' % event.group
        message += 'Logger: %s\n' % event.logger
        message += 'Message: %s\n' % event.message

        self.send_notification(title, message, link, project)
    """

    def send_notification(self, title, message, link, project):

        # see https://pushover.net/api

        params = ({
            'user': self.get_option('userkey', project),
            'token': self.get_option('apikey', project),
            'message': message,
            'title': title,
            'url': link,
            'url_title': 'More info',
            'priority': self.get_option('priority', project),
        })

        requests.post('https://api.pushover.net/1/messages.json', params=params)
