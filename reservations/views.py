from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db.models import Q
from .models import Book, Reservation
from .serializers import BookSerializer, ReservationSerializer


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Book model."""
    queryset = Book.objects.all()
    serializer_class = BookSerializer
    filterset_fields = ['available', 'author']
    search_fields = ['title', 'author', 'isbn']
    ordering_fields = ['title', 'author', 'created_at']

    @action(detail=False, methods=['get'])
    def available(self, request):
        """List only available books."""
        available_books = Book.objects.filter(available=True).exclude(
            reservation__status='ready'
        )
        serializer = self.get_serializer(available_books, many=True)
        return Response(serializer.data)


class ReservationViewSet(viewsets.ReadOnlyModelViewSet):
    """API viewset for Reservation model."""
    queryset = Reservation.objects.all()
    serializer_class = ReservationSerializer
    filterset_fields = ['status', 'member', 'book']
    search_fields = ['member__name', 'member__email', 'book__title']
    ordering_fields = ['created_at', 'expires_at']
