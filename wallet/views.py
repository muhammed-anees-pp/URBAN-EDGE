from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import Wallet, WalletTransaction

@login_required
def wallet_view(request):
    try:
        wallet = Wallet.objects.get(user=request.user)
    except Wallet.DoesNotExist:
        # If the wallet does not exist, create a new one with zero balance
        wallet = Wallet.objects.create(user=request.user, balance=0.00)
    
    transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')
    return render(request, 'user/wallet.html', {'wallet': wallet, 'transactions': transactions})