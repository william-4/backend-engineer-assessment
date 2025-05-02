from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Auction, Bid
from django.utils import timezone
from datetime import timedelta

class AuctionTests(TestCase):
    """Test suite for auction and bidding functionalities."""

    def setUp(self):
        """Sets up test users and API client before each test."""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')

    def test_user_can_create_and_bid(self):
        """Tests that a regular user can create an auction and place a valid bid."""
        self.client.login(username='testuser', password='pass')
        now = timezone.now()
        auction_data = {
            'title': 'Phone',
            'description': 'Smartphone',
            'starting_price': '100.00',
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(days=1)).isoformat()
        }
        response = self.client.post('/new_auction/', auction_data, format='json')
        auction_id = response.data['id']
        bid_response = self.client.post('/enter_bid/', {'auction_id': auction_id, 'amount': '120.00'})
        self.assertEqual(bid_response.status_code, 200)

    def test_admin_can_delete_non_active_bid(self):
        """Tests that an admin can delete a bid from a completed auction."""
        self.client.login(username='testuser', password='pass')
        past_time = timezone.now() - timedelta(days=2)
        future_time = timezone.now() - timedelta(days=1)
        auction = Auction.objects.create(
            title='Old Phone',
            description='Old auction',
            starting_price='50.00',
            start_time=past_time,
            end_time=future_time,
            creator=self.user
        )
        bid = Bid.objects.create(auction=auction, bidder=self.user, amount=60.00)

        self.client.logout()
        self.client.login(username='admin', password='adminpass')
        response = self.client.post('/admin/delete_bid/', {'user_id': self.user.id, 'bid_id': bid.id})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Bid.objects.count(), 0)
