# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.test import TestCase


class HomeViewTest(TestCase):
    def test_home_status(self):
        response = self.client.get('/')
        self.assertEquals(response.status_code, 200)

    def test_home_template(self):
        response = self.client.get('/')
        self.assertEquals(response.template_name, ['home.html'])

    def test_home_has_bootstrap(self):
        response = self.client.get('/')
        html = response.content.decode('utf-8')
        self.assertIn('bootstrap.min.css', html)
        self.assertIn('bootstrap.min.js', html)
