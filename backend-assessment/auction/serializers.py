"""Module defining serializers for transformation of models <-> JSON"""

from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Auction, Bid

class UserSerializer(serializers.ModelSerializer):
    """Serializer for the user model"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email']

class AuctionSerializer(serializers.ModelSerializer):
    """Serializer for the Auction model"""
    class Meta:
        model = Auction
        fields = '__all__'


class BidSerializer(serializers.ModelSerializer):
    """Serializer for the Bid model"""
    class Meta:
        model = Bid
        fields = '__all__'
