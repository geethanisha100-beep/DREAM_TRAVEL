from django.contrib.auth.models import User
from django.db import models

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    phone = models.CharField(max_length=15, blank=True)
    address = models.TextField(blank=True)
    photo = models.ImageField(upload_to="profiles/", blank=True)
    experience = models.CharField(max_length=100, blank=True)
    about = models.TextField(blank=True)

class Destination(models.Model):
    CATS = [("beaches","Beaches"),("hills","Hills"),("heritage","Heritage"),("wildlife","Wildlife"),("adventure","Adventure"),("pilgrimage","Pilgrimage"),("international","International")]
    name = models.CharField(max_length=100)
    category = models.CharField(max_length=20, choices=CATS)
    tagline = models.CharField(max_length=100, blank=True)
    image = models.ImageField(upload_to="destinations/", blank=True)
    popular = models.BooleanField(default=False)
    def __str__(self): return self.name

class Package(models.Model):
    CATS = [("family","Family"),("honeymoon","Honeymoon"),("adventure","Adventure"),("budget","Budget"),("luxury","Luxury")]
    category = models.CharField(max_length=20, choices=CATS, default="family")
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.5)
    destination = models.CharField(max_length=100)
    title = models.CharField(max_length=150)
    description = models.TextField()
    amount = models.DecimalField("Charge per member", max_digits=10, decimal_places=2)
    duration = models.CharField(max_length=50, help_text="e.g. 4 days / 3 nights")
    start_date = models.DateField()
    seats = models.PositiveIntegerField(default=10)
    available = models.BooleanField(default=True)
    image1 = models.ImageField(upload_to="packages/", blank=True)
    image2 = models.ImageField(upload_to="packages/", blank=True)
    image3 = models.ImageField(upload_to="packages/", blank=True)
    def images(self): return [i for i in (self.image1, self.image2, self.image3) if i]
    def unit_price(self): return self.amount
    def __str__(self): return f"{self.title} - {self.destination}"

class Vehicle(models.Model):
    TYPES = [("CAR","Car (4 seater)"),("SUV","SUV (6 seater)"),("TEMPO","Tempo traveller (12 seater)"),("BUS","Tourist bus (30 seater)"),("BIKE","Bike / scooter (2 seater)")]
    name = models.CharField(max_length=100)
    model_name = models.CharField(max_length=100)
    vehicle_type = models.CharField(max_length=5, choices=TYPES)
    description = models.TextField(blank=True)
    photo = models.ImageField(upload_to="vehicles/", blank=True)
    count = models.PositiveIntegerField("Vehicles available", default=1)
    driver_included = models.BooleanField(default=True)
    available = models.BooleanField(default=True)
    amount = models.DecimalField("Amount per day", max_digits=10, decimal_places=2)
    def unit_price(self): return self.amount
    def __str__(self): return f"{self.name} {self.model_name}"

class Hotel(models.Model):
    name = models.CharField(max_length=100)
    location = models.CharField(max_length=100)
    food_details = models.CharField(max_length=200, blank=True)
    room_type = models.CharField(max_length=50)
    photo = models.ImageField(upload_to="hotels/", blank=True)
    rating = models.DecimalField(max_digits=2, decimal_places=1, default=4.0)
    available = models.BooleanField(default=True)
    amount = models.DecimalField("Room charge per day", max_digits=10, decimal_places=2)
    def unit_price(self): return self.amount
    def __str__(self): return f"{self.name}, {self.location}"

class RoomType(models.Model):
    hotel = models.ForeignKey(Hotel, on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    price = models.DecimalField("Price per night", max_digits=10, decimal_places=2)
    photo = models.ImageField(upload_to="rooms/", blank=True)
    def __str__(self): return f"{self.hotel.name} - {self.name}"

class Feedback(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField(default=5)
    comment = models.TextField()
    photo = models.ImageField(upload_to="feedback/", blank=True)
    created = models.DateTimeField(auto_now_add=True)

class Wishlist(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    package = models.ForeignKey(Package, on_delete=models.CASCADE)
    class Meta: unique_together = ("user", "package")

class Booking(models.Model):
    KINDS = [("trip", "Trip"), ("package", "Tour package"), ("vehicle", "Vehicle"), ("hotel", "Hotel")]
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    kind = models.CharField(max_length=10, choices=KINDS)
    item_id = models.PositiveIntegerField()
    item_name = models.CharField(max_length=200)
    name = models.CharField(max_length=100)
    members = models.PositiveIntegerField(default=1, help_text="Members (packages) or days (vehicles/hotels)")
    address = models.TextField()
    contact = models.CharField(max_length=100)
    message = models.TextField(blank=True)
    total = models.DecimalField(max_digits=12, decimal_places=2)
    status = models.CharField(max_length=10, default="Pending")  # Pending / Confirmed
    created = models.DateTimeField(auto_now_add=True)
    travel_date = models.DateField(null=True, blank=True)
    adults = models.PositiveIntegerField(default=1)
    children = models.PositiveIntegerField(default=0)
    vehicle = models.ForeignKey(Vehicle, null=True, blank=True, on_delete=models.SET_NULL)
    hotel = models.ForeignKey(Hotel, null=True, blank=True, on_delete=models.SET_NULL)
    room = models.ForeignKey(RoomType, null=True, blank=True, on_delete=models.SET_NULL)
    nights = models.PositiveIntegerField(default=1)
    @property
    def ref(self): return f"TRV{self.created:%Y%m%d}{self.pk:04d}"

class Payment(models.Model):
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE)
    method = models.CharField(max_length=20)
    txn_id = models.CharField(max_length=40, unique=True)
    amount = models.DecimalField(max_digits=12, decimal_places=2)
    email = models.EmailField()
    phone = models.CharField(max_length=15)
    paid_at = models.DateTimeField(auto_now_add=True)
