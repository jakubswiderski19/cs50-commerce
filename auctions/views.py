from unicodedata import category
from django.contrib.auth import authenticate, login, logout
from django.db import IntegrityError
from django.db.models import Max
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse
from django import forms

from .models import Listing, User, Category, Bid, Comment


def index(request):
    return render(request, "auctions/index.html",{
        "listings": Listing.objects.filter(active=True).all(),
        "title": "Active listings"
    })


def login_view(request):
    if request.method == "POST":

        # Attempt to sign user in
        username = request.POST["username"]
        password = request.POST["password"]
        user = authenticate(request, username=username, password=password)

        # Check if authentication successful
        if user is not None:
            login(request, user)
            return HttpResponseRedirect(reverse("index"))
        else:
            return render(request, "auctions/login.html", {
                "message": "Invalid username and/or password."
            })
    else:
        return render(request, "auctions/login.html")


def logout_view(request):
    logout(request)
    return HttpResponseRedirect(reverse("index"))


def register(request):
    if request.method == "POST":
        username = request.POST["username"]
        email = request.POST["email"]

        # Ensure password matches confirmation
        password = request.POST["password"]
        confirmation = request.POST["confirmation"]
        if password != confirmation:
            return render(request, "auctions/register.html", {
                "message": "Passwords must match."
            })

        # Attempt to create new user
        try:
            user = User.objects.create_user(username, email, password)
            user.save()
        except IntegrityError:
            return render(request, "auctions/register.html", {
                "message": "Username already taken."
            })
        login(request, user)
        return HttpResponseRedirect(reverse("index"))
    else:
        return render(request, "auctions/register.html")



def add(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            new_listing = Listing(title=request.POST["title"],
            description=request.POST["description"],
            starting_bid=request.POST["starting_bid"],
            created_by = request.user
            )
            if request.POST["image_url"]:
                new_listing.image_url = request.POST["image_url"]
            
            if request.POST["categories"]:
                new_listing_category = Category.objects.get(pk=request.POST["categories"])
                new_listing.category = new_listing_category
            new_listing.save()
            return HttpResponseRedirect(reverse("index"))
        return HttpResponseRedirect(reverse("login"))
    if request.user.is_authenticated:
        class NewListingForm(forms.Form):
            title = forms.CharField(label='Listing title', max_length=64)
            description = forms.CharField(label='Listing description', max_length=255, widget=forms.Textarea)
            starting_bid = forms.DecimalField(label='Starting bid')
            image_url = forms.URLField(label='Image url', required=False)
            categories= forms.ModelChoiceField(queryset=Category.objects.all(), required=False)

        return render(request, "auctions/add.html", {
            "form": NewListingForm()
        })
    return HttpResponseRedirect(reverse("login"))


def listing(request,pk):
    if 'error_message' in request.session:
        error_message = request.session['error_message']
        request.session['error_message'] = ''
    else:
        error_message = ''
    listing = Listing.objects.filter(pk=pk).first()
    minimum_bid=listing.listing_bid.all().order_by('bid').last()
    if minimum_bid:
        minimum_form_bid = minimum_bid.bid
    else:
        minimum_form_bid = listing.starting_bid
    class NewBid(forms.Form):
            bid = forms.DecimalField(label='Bid',min_value=minimum_form_bid)
    class NewComment(forms.Form):
            comment = forms.CharField(label='Comment', max_length=255, widget=forms.Textarea)
    if listing.active:
        return render(request, "auctions/listing.html", {
                "listing": listing,
                "error_message": error_message,
                "bid_form": NewBid(),
                "comment_form": NewComment(),
                "is_user_author": listing.created_by == request.user
            })
    else:
        return render(request, "auctions/closed_listing.html", {
                "listing": listing,
                "error_message": error_message,
                "bid_form": NewBid(),
                "comment_form": NewComment(),
                "is_user_author": listing.created_by == request.user
            })

def watchlist(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            listing = Listing.objects.filter(pk=request.POST["pk_listing"]).first()
            if not request.user in listing.watched_by_users.all():
                listing.watched_by_users.add(request.user)
            else:
                listing.watched_by_users.remove(request.user)
    return HttpResponseRedirect(reverse("listing",kwargs={'pk':request.POST["pk_listing"]}))

def bid(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            listing = Listing.objects.filter(pk=request.POST["pk_listing"]).first()
            bids = Bid.objects.filter(bid_listing=listing).all()
            if bids:
                max_bid = bids.aggregate(Max('bid'))['bid__max']
            else:
                max_bid = listing.starting_bid
            if float(request.POST["bid"]) > float(max_bid):
                b = Bid(bid_user = request.user,bid_listing = listing, bid = request.POST["bid"])
                b.save()
            else:
                request.session['error_message'] = 'Bid is lower'
                return HttpResponseRedirect(reverse("listing",kwargs={'pk':request.POST["pk_listing"]}))
    return HttpResponseRedirect(reverse("listing",kwargs={'pk':request.POST["pk_listing"]}))

def comment(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            listing = Listing.objects.filter(pk=request.POST["pk_listing"]).first()
            c = Comment(comment_user = request.user,comment_listing = listing, comment = request.POST["comment"])
            c.save()
    return HttpResponseRedirect(reverse("listing",kwargs={'pk':request.POST["pk_listing"]}))

def close_biding(request):
    if request.method == "POST":
        if request.user.is_authenticated:
            listing = Listing.objects.filter(pk=request.POST["pk_listing"]).first()
            if listing.created_by == request.user:
                listing.active=False
                listing.save()
    return HttpResponseRedirect(reverse("listing",kwargs={'pk':request.POST["pk_listing"]}))

def show_watchlist(request):
    if request.user.is_authenticated:
        listings = Listing.objects.all()
        return render(request, "auctions/index.html",{
            "listings": listings.filter(watched_by_users = request.user),
            "title": "Watchlist"
        })
    else:
        return HttpResponseRedirect(reverse("index"))

def categories(request):
    return render(request, "auctions/categories.html",{
            "categories":Category.objects.all()
        })

def category(request,category):
    c = Category.objects.filter(name=category).first()
    listings = Listing.objects.all()
    return render(request, "auctions/index.html",{
            "listings": listings.filter(category = c),
            "title": category
        })