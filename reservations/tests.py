from django.test import TestCase
from django.utils import timezone
from django.core.exceptions import ValidationError
from datetime import timedelta
from .models import Member, Book, Reservation


class ReservationModelTest(TestCase):
    def setUp(self):
        """Set up test data."""
        self.member = Member.objects.create(
            name="John Doe",
            email="john@example.com"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            isbn="1234567890123"
        )

    def test_one_ready_per_book_rule(self):
        """Test that only one active 'ready' reservation per book is allowed."""
        # Create first ready reservation
        reservation1 = Reservation.objects.create(
            member=self.member,
            book=self.book,
            status='ready',
            expires_at=timezone.now() + timedelta(days=7)
        )

        # Try to create another ready reservation for the same book
        member2 = Member.objects.create(
            name="Jane Doe",
            email="jane@example.com"
        )

        with self.assertRaises(ValidationError):
            reservation2 = Reservation(
                member=member2,
                book=self.book,
                status='ready',
                expires_at=timezone.now() + timedelta(days=7)
            )
            reservation2.full_clean()
            reservation2.save()

    def test_expired_reservation_auto_cancel(self):
        """Test that expired reservations are properly identified."""
        # Create expired reservation
        expired_reservation = Reservation.objects.create(
            member=self.member,
            book=self.book,
            status='queued',
            expires_at=timezone.now() - timedelta(days=1)
        )

        self.assertTrue(expired_reservation.is_expired)

        # Change status to 'cancelled' to avoid unique constraint violation
        expired_reservation.status = 'cancelled'
        expired_reservation.save()

        # Create valid reservation
        valid_reservation = Reservation.objects.create(
            member=self.member,
            book=self.book,
            status='queued',
            expires_at=timezone.now() + timedelta(days=7)
        )

        self.assertFalse(valid_reservation.is_expired)


class ExpireReservationsCommandTest(TestCase):
    def setUp(self):
        """Set up test data for command testing."""
        self.member = Member.objects.create(
            name="John Doe",
            email="john@example.com"
        )
        self.book = Book.objects.create(
            title="Test Book",
            author="Test Author",
            isbn="1234567890123"
        )

    def test_command_idempotency(self):
        """Test that the expire_reservations command is idempotent."""
        from django.core.management import call_command
        from django.core.management.base import CommandError

        # Create expired reservation
        expired_reservation = Reservation.objects.create(
            member=self.member,
            book=self.book,
            status='queued',
            expires_at=timezone.now() - timedelta(days=1)
        )

        # Run command first time
        call_command('expire_reservations')

        # Verify reservation was cancelled
        expired_reservation.refresh_from_db()
        self.assertEqual(expired_reservation.status, 'cancelled')

        # Run command again - should not change anything
        call_command('expire_reservations')

        # Verify status remains the same
        expired_reservation.refresh_from_db()
        self.assertEqual(expired_reservation.status, 'cancelled')