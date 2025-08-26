from django.db import models
from django.core.exceptions import ValidationError
from django.utils import timezone
from datetime import timedelta


class Member(models.Model):
    """Library member who can make reservations."""
    name = models.CharField(max_length=200)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.name} ({self.email})"

    class Meta:
        ordering = ['name']


class Book(models.Model):
    """Book that can be reserved."""
    title = models.CharField(max_length=200)
    author = models.CharField(max_length=200)
    isbn = models.CharField(max_length=13, unique=True)
    available = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.title} by {self.author}"

    class Meta:
        ordering = ['title']

    @property
    def has_active_reservation(self):
        """Check if book has an active 'ready' reservation."""
        return self.reservation_set.filter(status='ready').exists()

    def get_next_queued_reservation(self):
        """Get the oldest queued reservation for this book."""
        return self.reservation_set.filter(status='queued').order_by('created_at').first()


class Reservation(models.Model):
    """Book reservation with status tracking."""
    STATUS_CHOICES = [
        ('queued', 'Queued'),
        ('ready', 'Ready for Pickup'),
        ('cancelled', 'Cancelled'),
    ]

    member = models.ForeignKey(Member, on_delete=models.CASCADE)
    book = models.ForeignKey(Book, on_delete=models.CASCADE)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='queued')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.member.name} - {self.book.title} ({self.status})"

    class Meta:
        ordering = ['created_at']
        unique_together = ['book', 'member', 'status']

    def clean(self):
        """Validate reservation rules."""
        if self.status == 'ready':
            # Check if another ready reservation exists for this book
            if Reservation.objects.filter(book=self.book, status='ready').exclude(id=self.id).exists():
                raise ValidationError("Only one active 'ready' reservation per book is allowed.")

        # Set expiration date if not provided
        if not self.expires_at:
            self.expires_at = timezone.now() + timedelta(days=7)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    @property
    def is_expired(self):
        """Check if reservation has expired."""
        return timezone.now() > self.expires_at

    def cancel(self):
        """Cancel the reservation."""
        self.status = 'cancelled'
        self.save()

    def mark_ready(self):
        """Mark reservation as ready for pickup."""
        self.status = 'ready'
        self.save()

    def promote_from_queue(self):
        """Promote this reservation from queued to ready status."""
        if self.status == 'queued':
            self.status = 'ready'
            self.save()
            return True
        return False
