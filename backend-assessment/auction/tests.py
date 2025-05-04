from django.test import TestCase
from django.contrib.auth.models import User
from rest_framework.test import APIClient
from .models import Auction, Bid
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
from rest_framework_simplejwt.tokens import RefreshToken

class AuctionTests(TestCase):
    """Tests for auction and bidding functionalities."""
    
    def setUp(self):
        """Sets up test users and API client before each test."""
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='pass')
        self.admin = User.objects.create_superuser(username='admin', password='adminpass')
        
        # Generate JWT token for testuser
        refresh = RefreshToken.for_user(self.user)
        access_token = str(refresh.access_token)
        
        # Authenticate requests with the token
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
    
    def test_user_can_create_and_bid(self):
        """Tests that a regular user can create an auction and place a valid bid."""
        now = timezone.now()
        auction_data = {
            'title': 'Phone',
            'description': 'Smartphone',
            'starting_price': '100.00',
            'start_time': now.isoformat(),
            'end_time': (now + timedelta(days=1)).isoformat(),
            'creator': self.user.id
        }
        
        # Create auction
        response = self.client.post('/api/auction/', auction_data, format='json')
        self.assertEqual(response.status_code, 201)
        auction_id = response.data['id']
        
        # Place a bid
        bid_data = {'auction_id': auction_id, 'amount': '120.00'}
        bid_response = self.client.post('/api/bid/', bid_data, format='json')
        self.assertEqual(bid_response.status_code, 200)
        
        # Check that the bid was placed correctly
        auction = Auction.objects.get(id=auction_id)
        self.assertEqual(auction.bids.count(), 1)
    
    def test_admin_can_delete_non_active_bid(self):
        """Tests that an admin can delete a bid from a completed auction."""
        past_time = timezone.now() - timedelta(days=2)
        future_time = timezone.now() - timedelta(days=1)
        
        # Create an auction with a bid
        auction = Auction.objects.create(
            title='Old Phone',
            description='Old auction',
            starting_price=Decimal('50.00'),
            start_time=past_time,
            end_time=future_time,
            creator=self.user
        )
        bid = Bid.objects.create(auction=auction, bidder=self.user, amount=Decimal('60.00'))
        
        # Authenticate as admin
        refresh = RefreshToken.for_user(self.admin)
        access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION='Bearer ' + access_token)
        
        # Delete bid as admin
        delete_data = {'user_id': self.user.id, 'bid_id': bid.id}
        response = self.client.delete('/api/admin/auction/', data=delete_data, format='json')
        self.assertEqual(response.status_code, 200)
        
        # Verify the bid has been deleted
        with self.assertRaises(Bid.DoesNotExist):
            Bid.objects.get(id=bid.id)
