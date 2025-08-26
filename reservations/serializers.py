from rest_framework import serializers
from .models import Book, Reservation, Member


class MemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = Member
        fields = ['id', 'name', 'email', 'phone', 'created_at']


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = ['id', 'title', 'author', 'isbn', 'available', 'created_at']


class ReservationSerializer(serializers.ModelSerializer):
    member = MemberSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = Reservation
        fields = ['id', 'member', 'book', 'status', 'created_at', 'expires_at']