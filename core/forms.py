from django import forms
from django.contrib.auth.models import User
from .models import Booking, Profile

class RegisterForm(forms.Form):
    email = forms.EmailField()
    phone = forms.RegexField(r"^\d{10}$", error_messages={"invalid": "Enter a 10-digit phone number."})
    password = forms.CharField(widget=forms.PasswordInput, min_length=8)
    confirm_password = forms.CharField(widget=forms.PasswordInput)
    def clean(self):
        d = super().clean()
        if d.get("password") != d.get("confirm_password"):
            raise forms.ValidationError("Passwords do not match.")
        if User.objects.filter(email__iexact=d.get("email", "")).exists() or Profile.objects.filter(phone=d.get("phone")).exists():
            raise forms.ValidationError("An account with this email or phone already exists.")
        return d

class LoginForm(forms.Form):
    username = forms.CharField(label="Phone number or email")
    password = forms.CharField(widget=forms.PasswordInput)

class BookingForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["name", "members", "address", "contact", "message"]
        widgets = {"address": forms.Textarea(attrs={"rows": 2}), "message": forms.Textarea(attrs={"rows": 2})}
    def clean_members(self):
        m = self.cleaned_data["members"]
        if m < 1: raise forms.ValidationError("Enter at least 1.")
        return m

class PaymentForm(forms.Form):
    method = forms.ChoiceField(choices=[("Card","Credit / Debit card"),("UPI","UPI (Google Pay / PhonePe)"),("Net Banking","Net banking"),("Wallet","Wallet")])
    email = forms.EmailField()
    phone = forms.RegexField(r"^\d{10}$")

class ProfileForm(forms.ModelForm):
    name = forms.CharField(required=False)
    email = forms.EmailField()
    class Meta:
        model = Profile
        fields = ["photo", "phone", "address"]

class AdminProfileForm(ProfileForm):
    class Meta(ProfileForm.Meta):
        fields = ["photo", "phone", "address", "experience", "about"]

from .models import Feedback
class TripForm(forms.ModelForm):
    class Meta:
        model = Booking
        fields = ["travel_date", "adults", "children", "vehicle", "hotel", "room", "nights", "name", "address", "contact"]
        widgets = {"travel_date": forms.DateInput(attrs={"type": "date"}), "address": forms.Textarea(attrs={"rows": 2})}
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        for f in ("vehicle", "hotel", "room"): self.fields[f].required = False
        self.fields["adults"].min_value = 1
    def clean(self):
        d = super().clean()
        if d.get("adults", 0) < 1 or d.get("nights", 0) < 1: raise forms.ValidationError("Adults and nights must be at least 1.")
        if d.get("room") and d.get("hotel") and d["room"].hotel_id != d["hotel"].pk:
            self.add_error("room", "Pick a room from the selected hotel.")
        return d

class FeedbackForm(forms.ModelForm):
    rating = forms.ChoiceField(choices=[(i, f"{i} star{'s' if i > 1 else ''}") for i in range(5, 0, -1)])
    class Meta:
        model = Feedback
        fields = ["package", "rating", "comment", "photo"]
