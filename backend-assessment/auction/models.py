"""Module defining the different models (database tables) in the application"""

# Inbuilt django user model to be used in the application
from django.contrib.auth.models import User
from django.db import models

class Auction(models.Model):
    """Defines an auction created by a user"""
    title = models.CharField(max_length=100)
    description = models.TextField()
    starting_price = models.DecimalField(max_digits=10, decimal_places=2)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    creator = models.ForeignKey(User, on_delete=models.CASCADE, related_name='auctions')

    def is_active(self):
        """Returns true if current time is within the auction period"""
        from django.utils import timezone
        now = timezone.now()
        return self.start_time <= now <= self.end_time

class Bid(models.Model):
    """Represents a bid placed by a user on an auction"""
    auction = models.ForeignKey(Auction, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-amount']
