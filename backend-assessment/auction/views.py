"""Module defining the different api endpoints"""

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
from decimal import Decimal, InvalidOperation
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi

class SignUpView(APIView):
    """API endpoint for user registration."""
    
    @swagger_auto_schema(
        operation_description="Creates a new user account",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        ),
        responses={
            201: "User created successfully",
            400: "Bad Request"
        }
    )
    def post(self, request):
        """Creates a new user from the provided username and password."""
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already taken'}, status=status.HTTP_400_BAD_REQUEST)
        user = User.objects.create_user(username=username, password=password)
        serializer = UserSerializer(user)
        return Response({
            'message': 'User created successfully',
            'user': serializer.data
        }, status=status.HTTP_201_CREATED)

class LoginView(APIView):
    """API endpoint for user login."""
    
    @swagger_auto_schema(
        operation_description="Authenticates user and returns JWT tokens",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['username', 'password'],
            properties={
                'username': openapi.Schema(type=openapi.TYPE_STRING, description='Username'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, description='Password'),
            }
        ),
        responses={
            200: "Login successful",
            400: "Bad Request",
            401: "Invalid credentials"
        }
    )
    def post(self, request):
        """Authenticates user and returns JWT tokens."""
        username = request.data.get('username')
        password = request.data.get('password')
        if not username or not password:
            return Response({'error': 'Username and password are required'}, status=status.HTTP_400_BAD_REQUEST)
        user = authenticate(username=username, password=password)
        if user is None:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)
        refresh = RefreshToken.for_user(user)
        serializer = UserSerializer(user)
        return Response({
            'message': 'Login successful',
            'user': serializer.data,
            'refresh': str(refresh),
            'access': str(refresh.access_token)
        }, status=status.HTTP_200_OK)

class LogoutView(APIView):
    """API endpoint for user logout."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Blacklists the refresh token to log out the user",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['refresh'],
            properties={
                'refresh': openapi.Schema(type=openapi.TYPE_STRING, description='Refresh token to blacklist'),
            }
        ),
        responses={
            200: "Logged out successfully",
            400: "Invalid or expired token",
            401: "Unauthorized"
        }
    )
    def post(self, request):
        """Blacklists the refresh token to log out the user."""
        refresh_token = request.data.get('refresh')
        if not refresh_token:
            return Response({'error': 'Refresh token required'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response({'message': 'Logged out successfully'}, status=status.HTTP_200_OK)
        except TokenError:
            return Response({'error': 'Invalid or expired token'}, status=status.HTTP_400_BAD_REQUEST)

class NewAuctionView(APIView):
    """API endpoint for creating a new auction (authenticated users only)."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Create a new auction",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['title', 'description', 'starting_price', 'start_time', 'end_time'],
            properties={
                'title': openapi.Schema(type=openapi.TYPE_STRING, description='Auction title'),
                'description': openapi.Schema(type=openapi.TYPE_STRING, description='Auction description'),
                'starting_price': openapi.Schema(type=openapi.TYPE_STRING, description='Starting price (decimal)'),
                'start_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='Start time (ISO format)'),
                'end_time': openapi.Schema(type=openapi.TYPE_STRING, format=openapi.FORMAT_DATETIME, description='End time (ISO format)'),
            }
        ),
        responses={
            201: "Auction created successfully",
            400: "Bad Request",
            401: "Unauthorized"
        }
    )
    def post(self, request):
        """Handles the creation of a new auction with the current user as creator."""
        # Create a mutable copy of the data
        data = request.data.copy()
        
        # Remove creator if it's in the request data to avoid validation errors
        if 'creator' in data:
            del data['creator']
            
        serializer = AuctionSerializer(data=data)
        if serializer.is_valid():
            serializer.save(creator=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class EnterBidView(APIView):
    """API endpoint for placing a Bid on an auction (authenticated users only)."""
    permission_classes = [IsAuthenticated]
    
    @swagger_auto_schema(
        operation_description="Place a bid on an active auction",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['auction_id', 'amount'],
            properties={
                'auction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the auction'),
                'amount': openapi.Schema(type=openapi.TYPE_STRING, description='Bid amount (decimal)'),
            }
        ),
        responses={
            200: "Bid placed successfully",
            400: "Bad Request - Auction not active or bid too low",
            401: "Unauthorized",
            404: "Auction not found"
        }
    )
    def post(self, request):
        """Places a Bid if the auction is active and the Bid is higher than the current highest."""
        auction_id = request.data.get('auction_id')
        amount = request.data.get('amount')
        
        # Validate auction_id
        if not auction_id:
            return Response({'error': 'Auction ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Validate amount
        try:
            amount = Decimal(amount)
            if amount <= 0:
                return Response({'error': 'Amount must be positive'}, status=status.HTTP_400_BAD_REQUEST)
        except (InvalidOperation, TypeError):
            return Response({'error': 'Invalid amount'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Get auction
        try:
            auction = Auction.objects.get(id=auction_id)
        except Auction.DoesNotExist:
            return Response({'error': 'Auction not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Check if auction is active
        now = timezone.now()
        if now < auction.start_time or now > auction.end_time:
            return Response({'error': 'Auction not active'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if bid is higher than current highest
        highest_bid = auction.bids.order_by('-amount').first()
        if highest_bid and amount <= highest_bid.amount:
            return Response({'error': 'Bid must be higher than current highest bid'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if bid is higher than starting price if no bids yet
        if not highest_bid and amount < auction.starting_price:
            return Response({'error': 'Bid must be at least the starting price'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create bid
        bid = Bid.objects.create(auction=auction, bidder=request.user, amount=amount)
        serializer = BidSerializer(bid)
        return Response({'message': 'Bid placed successfully', 'bid': serializer.data}, status=status.HTTP_200_OK)

class AdminAuctionView(APIView):
    """API endpoint for admin operations on auctions."""
    permission_classes = [IsAdminUser]
    
    @swagger_auto_schema(
        operation_description="Get all auctions (admin only)",
        responses={
            200: "List of all auctions",
            401: "Unauthorized",
            403: "Forbidden - Not an admin"
        }
    )
    def get(self, request):
        """View all auctions (admin only)."""
        auctions = Auction.objects.all()
        serializer = AuctionSerializer(auctions, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
    
    @swagger_auto_schema(
        operation_description="Delete an auction or bid (admin only)",
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            properties={
                'auction_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the auction to delete'),
                'bid_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the bid to delete'),
                'user_id': openapi.Schema(type=openapi.TYPE_INTEGER, description='ID of the user (for bid deletion)'),
            }
        ),
        responses={
            200: "Successfully deleted",
            400: "Bad Request - Missing required fields",
            401: "Unauthorized",
            403: "Forbidden - Not an admin",
            404: "Auction or bid not found"
        }
    )
    def delete(self, request):
        """Delete an auction or bid (admin only)."""
        auction_id = request.data.get('auction_id')
        bid_id = request.data.get('bid_id')
        user_id = request.data.get('user_id')
        
        # If bid_id is provided, delete the bid
        if bid_id:
            try:
                bid = Bid.objects.get(id=bid_id)
                bid.delete()
                return Response({'message': 'Bid deleted successfully'}, status=status.HTTP_200_OK)
            except Bid.DoesNotExist:
                return Response({'error': 'Bid not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # If auction_id is provided, delete the auction
        elif auction_id:
            try:
                auction = Auction.objects.get(id=auction_id)
                auction.delete()
                return Response({'message': 'Auction deleted successfully'}, status=status.HTTP_200_OK)
            except Auction.DoesNotExist:
                return Response({'error': 'Auction not found'}, status=status.HTTP_404_NOT_FOUND)
        
        else:
            return Response({'error': 'Either auction_id or bid_id is required'}, status=status.HTTP_400_BAD_REQUEST)
