from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken, TokenError
from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from .models import Auction, Bid
from .serializers import UserSerializer, AuctionSerializer, BidSerializer
from django.utils import timezone

class SignUpView(APIView):
    """API endpoint for user registration."""

    def post(self, request):
        """Creates a new user from the provided username and password."""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)

        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=400)

        user = User.objects.create_user(username=username, password=password)
        serializer = UserSerializer(user)
        return Response({
            'message': 'User created successfully',
            'user': serializer.data
        }, status=201)
        return Response({'message': 'User created'}, status=201)

class LoginView(APIView):
    """API endpoint for user login."""

    def post(self, request):
        """Authenticates user and returns JWT tokens."""
        username = request.data.get('username')
        password = request.data.get('password')

        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=400)

        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=401)

        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)

        return Response({
            'message': 'Login successful',
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=200)

class LogoutView(APIView):
    """API endpoint for user logout."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklists the refresh token to log out the user."""
        refresh_token = request.data.get('refresh')

        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=400)

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=200)
        except TokenError:
            return Response({'error': 'Invalid or expired token'}, status=400)

class NewAuctionView(APIView):
    """API endpoint for creating a new auction (authenticated users only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Handles the creation of a new auction with the current user as creator."""
        serializer = AuctionSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=201)
        return Response(serializer.errors, status=400)


class EnterBidView(APIView):
    """API endpoint for placing a Bid on an auction (authenticated users only)."""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Places a Bid if the auction is active and the Bid is higher than the current highest."""
        auction_id = request.data.get('auction_id')
        amount = request.data.get('amount')
        auction = Auction.objects.get(id=auction_id)

        if not auction.is_active():
            return Response({'error': 'Auction not active'}, status=400)

        top_bid = auction.Bids.first()
        if top_bid and float(amount) <= float(top_bid.amount):
            return Response({'error': 'Bid must be higher'}, status=400)

        Bid.objects.create(auction=auction, Bidder=request.user, amount=amount)
        return Response({'message': 'Bid placed'})


class AdminAuctionView(APIView):
    permission_classes = [IsAdminUser]

    def get(self, request):
        """View all auctions (admin only)."""
        auctions = Auction.objects.all()
        serializer = AuctionSerializer(auctions, many=True)
        return Response(serializer.data)

    def delete(self, request):
        """Delete an auction by ID (admin only)."""
        auction_id = request.data.get('auction_id')
        try:
            auction = Auction.objects.get(id=auction_id)
            auction.delete()
            return Response({'message': 'Auction deleted'})
        except Auction.DoesNotExist:
            return Response({'error': 'Auction not found'}, status=404)
