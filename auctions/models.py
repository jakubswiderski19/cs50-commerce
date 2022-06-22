from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    pass

class Category(models.Model):
    name = models.CharField(max_length=64)
    class Meta:
        verbose_name_plural = "Categories"
    
    def __str__(self):
        return f"{self.name}"

class Listing(models.Model):
    created_by = models.ForeignKey(User,on_delete=models.CASCADE,related_name="user_listings")
    title = models.CharField(max_length=64)
    description = models.CharField(max_length=255)
    starting_bid = models.DecimalField(decimal_places=2,max_digits=10)
    image_url = models.URLField(blank=True,null=True)
    category = models.ForeignKey(Category,on_delete=models.CASCADE,blank=True,null=True,related_name="listings")
    active = models.BooleanField(default=True)
    watched_by_users= models.ManyToManyField(User,related_name="user_watched_listings", blank=True)

    def __str__(self):
        return f"{self.title} ({self.starting_bid})"


class Bid(models.Model):
    bid_user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="user_bid")
    bid_listing = models.ForeignKey(Listing,on_delete=models.CASCADE, related_name="listing_bid")
    bid = models.DecimalField(decimal_places=2,max_digits=10)

    def __str__(self):
        return f"User: {self.bid_user.username} bided listing: {self.bid_listing.title} for {self.bid}"

class Comment(models.Model):
    comment_user = models.ForeignKey(User,on_delete=models.CASCADE,related_name="user_comment")
    comment_listing = models.ForeignKey(Listing,on_delete=models.CASCADE,related_name="listing_comment")
    comment = models.CharField(max_length=255)


    
