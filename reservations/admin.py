from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils import timezone
from .models import Member, Book, Reservation


class ReservationInline(admin.TabularInline):
    """Inline reservations under Member."""
    model = Reservation
    extra = 0
    readonly_fields = ['created_at', 'expires_at', 'is_expired_display']
    fields = ['book', 'status', 'created_at', 'expires_at', 'is_expired_display']

    def is_expired_display(self, obj):
        """Display expiration status with color coding."""
        # Handle new objects that don't have an ID yet
        if not obj.pk or not obj.expires_at:
            return format_html('<span style="color: gray;">N/A</span>')

        if obj.is_expired:
            return format_html('<span style="color: red;">EXPIRED</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Expiration Status'

    def get_queryset(self, request):
        """Only show existing reservations, not empty forms."""
        qs = super().get_queryset(request)
        return qs.filter(pk__isnull=False)


@admin.register(Member)
class MemberAdmin(admin.ModelAdmin):
    """Admin interface for Member model."""
    list_display = ['name', 'email', 'phone', 'created_at', 'reservation_count']
    search_fields = ['name', 'email']
    list_filter = ['created_at']
    inlines = [ReservationInline]

    def reservation_count(self, obj):
        """Count of active reservations."""
        # Handle new objects that don't have an ID yet
        if not obj.pk:
            return 0
        return obj.reservation_set.filter(status__in=['queued', 'ready']).count()
    reservation_count.short_description = 'Active Reservations'


@admin.register(Book)
class BookAdmin(admin.ModelAdmin):
    """Admin interface for Book model."""
    list_display = ['title', 'author', 'isbn', 'available', 'status_display', 'reservation_count']
    search_fields = ['title', 'author', 'isbn']
    list_filter = ['available', 'created_at']
    actions = ['mark_as_returned']

    def status_display(self, obj):
        """Display current reservation status."""
        # Handle new objects that don't have an ID yet
        if not obj.pk:
            return format_html('<span style="color: gray;">N/A</span>')

        if obj.has_active_reservation:
            return format_html('<span style="color: orange;">Reserved</span>')
        elif obj.available:
            return format_html('<span style="color: green;">Available</span>')
        return format_html('<span style="color: red;">Unavailable</span>')
    status_display.short_description = 'Status'

    def reservation_count(self, obj):
        """Count of queued reservations."""
        # Handle new objects that don't have an ID yet
        if not obj.pk:
            return 0
        return obj.reservation_set.filter(status='queued').count()
    reservation_count.short_description = 'Queued'

    def mark_as_returned(self, request, queryset):
        """Mark selected books as returned and promote next reservation."""
        updated = 0
        for book in queryset:
            if book.has_active_reservation:
                # Cancel the current ready reservation
                ready_reservation = book.reservation_set.filter(status='ready').first()
                if ready_reservation:
                    ready_reservation.cancel()

                # Promote next queued reservation
                next_reservation = book.get_next_queued_reservation()
                if next_reservation:
                    next_reservation.mark_ready()
                    updated += 1

        if updated == 1:
            message = '1 book was marked as returned and next reservation promoted.'
        else:
            message = f'{updated} books were marked as returned and next reservations promoted.'

        self.message_user(request, message)
    mark_as_returned.short_description = 'Mark book(s) as returned'


@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    """Admin interface for Reservation model."""
    list_display = ['member', 'book', 'status', 'created_at', 'expires_at', 'is_expired_display']
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = ['member__name', 'member__email', 'book__title', 'book__author']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'

    def is_expired_display(self, obj):
        """Display expiration status with color coding."""
        # Handle new objects that don't have an ID yet
        if not obj.pk or not obj.expires_at:
            return format_html('<span style="color: gray;">N/A</span>')

        if obj.is_expired:
            return format_html('<span style="color: red;">EXPIRED</span>')
        return format_html('<span style="color: green;">Valid</span>')
    is_expired_display.short_description = 'Expired'

    actions = ['cancel_expired', 'promote_from_queue']

    def cancel_expired(self, request, queryset):
        """Cancel expired reservations."""
        expired = queryset.filter(expires_at__lt=timezone.now(), status__in=['queued', 'ready'])
        count = expired.count()
        expired.update(status='cancelled')

        if count == 1:
            message = '1 expired reservation was cancelled.'
        else:
            message = f'{count} expired reservations were cancelled.'

        self.message_user(request, message)
    cancel_expired.short_description = 'Cancel expired reservations'

    def promote_from_queue(self, request, queryset):
        """Promote queued reservations to ready."""
        queued = queryset.filter(status='queued')
        promoted = 0

        for reservation in queued:
            if not reservation.book.has_active_reservation:
                reservation.mark_ready()
                promoted += 1

        if promoted == 1:
            message = '1 reservation was promoted from queue.'
        else:
            message = f'{promoted} reservations were promoted from queue.'

        self.message_user(request, message)
    promote_from_queue.short_description = 'Promote from queue'
