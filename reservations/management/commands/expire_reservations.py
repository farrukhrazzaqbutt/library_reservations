from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from reservations.models import Reservation, Book


class Command(BaseCommand):
    help = 'Expire reservations and promote next in queue. This command is idempotent.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made'))

        # Get all expired reservations
        now = timezone.now()
        expired_reservations = Reservation.objects.filter(
            expires_at__lt=now,
            status__in=['queued', 'ready']
        ).select_related('book')

        if not expired_reservations.exists():
            self.stdout.write(self.style.SUCCESS('No expired reservations found.'))
            return

        self.stdout.write(f'Found {expired_reservations.count()} expired reservations.')

        # Group expired reservations by book
        books_with_expired = {}
        for reservation in expired_reservations:
            book_id = reservation.book.id
            if book_id not in books_with_expired:
                books_with_expired[book_id] = []
            books_with_expired[book_id].append(reservation)

        cancelled_count = 0
        promoted_count = 0

        with transaction.atomic():
            for book_id, reservations in books_with_expired.items():
                book = Book.objects.get(id=book_id)

                # Cancel all expired reservations for this book
                for reservation in reservations:
                    if not dry_run:
                        reservation.cancel()
                    cancelled_count += 1
                    self.stdout.write(f'  Cancelled: {reservation}')

                # Promote next queued reservation if no active ready reservation
                if not book.has_active_reservation:
                    next_reservation = book.get_next_queued_reservation()
                    if next_reservation:
                        if not dry_run:
                            next_reservation.mark_ready()
                        promoted_count += 1
                        self.stdout.write(f'  Promoted: {next_reservation}')

        # Summary
        if dry_run:
            self.stdout.write(
                self.style.SUCCESS(
                    f'DRY RUN: Would cancel {cancelled_count} expired reservations '
                    f'and promote {promoted_count} from queue.'
                )
            )
        else:
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cancelled {cancelled_count} expired reservations '
                    f'and promoted {promoted_count} from queue.'
                )
            )

        # Verify idempotency by running again
        if not dry_run:
            self.stdout.write('\nVerifying idempotency...')
            self.handle(*args, **options)
