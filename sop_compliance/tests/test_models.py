"""
Test cases for NetBox SopCompliance Plugin models.
"""

from django.core.exceptions import ValidationError

from ..models import Sopcompliance
from ..testing import PluginModelTestCase
from ..testing.utils import create_tags, get_random_string


class SopcomplianceTestCase(PluginModelTestCase):
    """Test Sopcompliance model."""

    @classmethod
    def setUpTestData(cls):
        """Set up test data for all tests."""
        # Create test instances
        Sopcompliance.objects.create(name='Test 1')
        Sopcompliance.objects.create(name='Test 2')
        Sopcompliance.objects.create(name='Test 3')

    def test_create_sopcompliance(self):
        """Test creating a Sopcompliance instance."""
        name = f'Test {get_random_string(10)}'
        instance = Sopcompliance.objects.create(name=name)

        self.assertEqual(instance.name, name)
        self.assertIsNotNone(instance.pk)

    def test_sopcompliance_str(self):
        """Test Sopcompliance string representation."""
        instance = Sopcompliance.objects.first()
        self.assertEqual(str(instance), instance.name)

    def test_sopcompliance_absolute_url(self):
        """Test Sopcompliance get_absolute_url method."""
        instance = Sopcompliance.objects.first()
        url = instance.get_absolute_url()

        self.assertIsNotNone(url)
        self.assertIn(str(instance.pk), url)

    def test_sopcompliance_unique_name(self):
        """Test that Sopcompliance names must be unique."""
        name = 'Duplicate Name'
        Sopcompliance.objects.create(name=name)

        with self.assertRaises(ValidationError):
            instance = Sopcompliance(name=name)
            instance.full_clean()

    def test_model_to_dict(self):
        """Test model_to_dict helper method."""
        instance = Sopcompliance.objects.first()
        data = self.model_to_dict(instance)

        self.assertIn('name', data)
        self.assertEqual(data['name'], instance.name)
        self.assertIn('id', data)

    def test_instance_equal(self):
        """Test assertInstanceEqual helper method."""
        instance = Sopcompliance.objects.first()

        # Should pass with matching data
        self.assertInstanceEqual(
            instance,
            {'name': instance.name, 'id': instance.pk}
        )

    def test_sopcompliance_with_tags(self):
        """Test Sopcompliance with tags."""
        tags = create_tags(['important', 'test'])
        instance = Sopcompliance.objects.first()

        instance.tags.add(*tags)
        instance.save()

        self.assertEqual(instance.tags.count(), 2)
        self.assertIn(tags[0], instance.tags.all())

    def test_bulk_create(self):
        """Test bulk creation of Sopcompliance instances."""
        initial_count = Sopcompliance.objects.count()

        instances = [
            Sopcompliance(name=f'Bulk {i}')
            for i in range(5)
        ]
        Sopcompliance.objects.bulk_create(instances)

        self.assertEqual(
            Sopcompliance.objects.count(),
            initial_count + 5
        )

    def test_query_filter(self):
        """Test filtering Sopcompliance instances."""
        # Create a specific instance for filtering
        test_name = f'FilterTest {get_random_string(10)}'
        Sopcompliance.objects.create(name=test_name)

        # Test filter
        results = Sopcompliance.objects.filter(name=test_name)
        self.assertEqual(results.count(), 1)
        self.assertEqual(results.first().name, test_name)

    def test_ordering(self):
        """Test Sopcompliance default ordering."""
        instances = list(Sopcompliance.objects.all())

        # Check that instances are ordered by name
        names = [instance.name for instance in instances]
        self.assertEqual(names, sorted(names))


class SopcomplianceValidationTestCase(PluginModelTestCase):
    """Test Sopcompliance validation."""

    def test_empty_name(self):
        """Test that empty name is not allowed."""
        with self.assertRaises(ValidationError):
            instance = Sopcompliance(name='')
            instance.full_clean()

    def test_name_max_length(self):
        """Test name field max length."""
        long_name = 'x' * 101  # Exceeds max_length of 100

        with self.assertRaises(ValidationError):
            instance = Sopcompliance(name=long_name)
            instance.full_clean()
