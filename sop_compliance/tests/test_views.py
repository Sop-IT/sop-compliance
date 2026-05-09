"""
Test cases for NetBox SopCompliance Plugin views.
"""

from django.urls import reverse

from ..models import Sopcompliance
from ..testing import PluginViewTestCase
from ..testing.utils import disable_warnings, get_random_string


class SopcomplianceViewTestCase(PluginViewTestCase):
    """Test Sopcompliance views."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        Sopcompliance.objects.create(name='View Test 1')
        Sopcompliance.objects.create(name='View Test 2')
        Sopcompliance.objects.create(name='View Test 3')

    def setUp(self):
        """Set up each test."""
        super().setUp()
        self.base_url = 'plugins:sop_compliance:sopcompliance'

    def test_list_sopcompliances(self):
        """Test Sopcompliance list view."""
        self.add_permissions('sop_compliance.view_sopcompliance')

        url = reverse('plugins:sop_compliance:sopcompliance_list')
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)

    def test_list_sopcompliances_without_permission(self):
        """Test Sopcompliance list view without permission."""
        url = reverse('plugins:sop_compliance:sopcompliance_list')

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)

    def test_view_sopcompliance(self):
        """Test Sopcompliance detail view."""
        self.add_permissions('sop_compliance.view_sopcompliance')

        instance = Sopcompliance.objects.first()
        url = reverse('plugins:sop_compliance:sopcompliance', kwargs={'pk': instance.pk})
        response = self.client.get(url)

        self.assertHttpStatus(response, 200)
        self.assertEqual(response.context['object'], instance)

    def test_create_sopcompliance(self):
        """Test creating a Sopcompliance via form."""
        self.add_permissions(
            'sop_compliance.add_sopcompliance',
            'sop_compliance.view_sopcompliance'
        )

        url = reverse('plugins:sop_compliance:sopcompliance_add')
        name = f'Created {get_random_string(10)}'

        form_data = self.post_data({
            'name': name,
        })

        response = self.client.post(url, form_data, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was created
        instance = Sopcompliance.objects.get(name=name)
        self.assertEqual(instance.name, name)

    def test_create_sopcompliance_without_permission(self):
        """Test creating a Sopcompliance without permission."""
        url = reverse('plugins:sop_compliance:sopcompliance_add')

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)

    def test_edit_sopcompliance(self):
        """Test editing a Sopcompliance via form."""
        self.add_permissions(
            'sop_compliance.change_sopcompliance',
            'sop_compliance.view_sopcompliance'
        )

        instance = Sopcompliance.objects.first()
        url = reverse('plugins:sop_compliance:sopcompliance_edit', kwargs={'pk': instance.pk})

        new_name = f'Edited {get_random_string(10)}'
        form_data = self.post_data({
            'name': new_name,
        })

        response = self.client.post(url, form_data, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was updated
        instance.refresh_from_db()
        self.assertEqual(instance.name, new_name)

    def test_delete_sopcompliance(self):
        """Test deleting a Sopcompliance."""
        self.add_permissions(
            'sop_compliance.delete_sopcompliance',
            'sop_compliance.view_sopcompliance'
        )

        instance = Sopcompliance.objects.first()
        url = reverse('plugins:sop_compliance:sopcompliance_delete', kwargs={'pk': instance.pk})

        # Confirm deletion
        response = self.client.post(url, {'confirm': True}, follow=True)
        self.assertHttpStatus(response, 200)

        # Verify object was deleted
        self.assertFalse(
            Sopcompliance.objects.filter(pk=instance.pk).exists()
        )

    def test_delete_sopcompliance_without_permission(self):
        """Test deleting a Sopcompliance without permission."""
        instance = Sopcompliance.objects.first()
        url = reverse('plugins:sop_compliance:sopcompliance_delete', kwargs={'pk': instance.pk})

        with disable_warnings('django.request'):
            response = self.client.get(url)
            self.assertHttpStatus(response, 403)


class SopcomplianceFormTestCase(PluginViewTestCase):
    """Test Sopcompliance form validation."""

    def setUp(self):
        """Set up each test."""
        super().setUp()
        self.add_permissions(
            'sop_compliance.add_sopcompliance',
            'sop_compliance.view_sopcompliance'
        )

    def test_form_validation_empty_name(self):
        """Test form validation with empty name."""
        url = reverse('plugins:sop_compliance:sopcompliance_add')
        form_data = self.post_data({'name': ''})

        response = self.client.post(url, form_data)
        self.assertHttpStatus(response, 200)  # Form redisplay

        # Should not create object
        self.assertEqual(Sopcompliance.objects.filter(name='').count(), 0)

    def test_form_validation_duplicate_name(self):
        """Test form validation with duplicate name."""
        Sopcompliance.objects.create(name='Duplicate')

        url = reverse('plugins:sop_compliance:sopcompliance_add')
        form_data = self.post_data({'name': 'Duplicate'})

        response = self.client.post(url, form_data)
        self.assertHttpStatus(response, 200)  # Form redisplay

        # Should only have one instance with this name
        self.assertEqual(Sopcompliance.objects.filter(name='Duplicate').count(), 1)
