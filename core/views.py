import io, uuid
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import FileResponse, Http404
from django.shortcuts import get_object_or_404, redirect, render
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from decimal import Decimal
from django.db.models import Q
from .forms import *
from .models import *

MODELS = {"package": Package, "vehicle": Vehicle, "hotel": Hotel}

def home(request):
    return render(request, "core/home.html", {"packages": Package.objects.filter(available=True)[:3],
        "vehicles": Vehicle.objects.filter(available=True)[:3], "hotels": Hotel.objects.filter(available=True)[:3],
        "dests": Destination.objects.filter(popular=True)[:5]})

def about(request): return render(request, "core/about.html")

def register(request):
    form = RegisterForm(request.POST or None)
    if form.is_valid():
        d = form.cleaned_data
        u = User.objects.create_user(username=d["email"], email=d["email"], password=d["password"])
        Profile.objects.create(user=u, phone=d["phone"])
        messages.success(request, "Account created. Please log in.")
        return redirect("login")
    return render(request, "core/form.html", {"form": form, "title": "Create your account", "button": "Register"})

def login_view(request):
    form = LoginForm(request.POST or None)
    if form.is_valid():
        u = authenticate(request, username=form.cleaned_data["username"], password=form.cleaned_data["password"])
        if u:
            login(request, u)
            return redirect(request.GET.get("next") or ("manage" if u.is_staff else "home"))
        form.add_error(None, "Phone/email or password is incorrect.")
    return render(request, "core/form.html", {"form": form, "title": "Log in", "button": "Log in", "forgot": True})

def listing(request, kind):
    qs = MODELS[kind].objects.filter(available=True)
    vt, cat, q = request.GET.get("type"), request.GET.get("cat"), request.GET.get("q")
    if kind == "vehicle" and vt: qs = qs.filter(vehicle_type=vt)
    if kind == "package":
        if cat: qs = qs.filter(category=cat)
        if q: qs = qs.filter(Q(title__icontains=q) | Q(destination__icontains=q))
    return render(request, "core/list.html", {"items": qs, "kind": kind, "cats": Package.CATS, "vtypes": Vehicle.TYPES})

def destinations(request):
    cat = request.GET.get("cat")
    qs = Destination.objects.filter(category=cat) if cat else Destination.objects.all()
    return render(request, "core/destinations.html", {"places": qs, "cats": Destination.CATS})

def package_detail(request, pk):
    p = get_object_or_404(Package, pk=pk)
    saved = request.user.is_authenticated and Wishlist.objects.filter(user=request.user, package=p).exists()
    return render(request, "core/package.html", {"p": p, "saved": saved, "reviews": p.feedback_set.select_related("user")})

@login_required
def toggle_wishlist(request, pk):
    obj, created = Wishlist.objects.get_or_create(user=request.user, package_id=pk)
    if not created: obj.delete()
    return redirect("package_detail", pk=pk)

@login_required
def book(request, kind, pk):
    if kind not in MODELS: raise Http404
    item = get_object_or_404(MODELS[kind], pk=pk, available=True)
    form = BookingForm(request.POST or None, initial={"contact": request.user.email})
    if form.is_valid():
        if kind == "package" and form.cleaned_data["members"] > item.seats:
            form.add_error("members", f"Only {item.seats} seats left.")
        else:
            b = form.save(commit=False)
            b.user, b.kind, b.item_id, b.item_name = request.user, kind, item.pk, str(item)
            b.total = item.unit_price() * b.members  # amount x members (or x days)
            b.save()
            return redirect("pay", pk=b.pk)
    return render(request, "core/book.html", {"form": form, "item": item, "kind": kind})

@login_required
def pay(request, pk):
    b = get_object_or_404(Booking, pk=pk, user=request.user)
    if hasattr(b, "payment"): return render(request, "core/paid.html", {"b": b})
    form = PaymentForm(request.POST or None, initial={"email": request.user.email})
    if form.is_valid():
        d = form.cleaned_data
        # TODO: replace with real PhonePe / Google Pay gateway call + callback verification
        Payment.objects.create(booking=b, method=d["method"], email=d["email"], phone=d["phone"],
                               amount=b.total, txn_id="DT" + uuid.uuid4().hex[:12].upper())
        b.status = "Confirmed"; b.save()
        if b.kind in ("package", "trip"):
            pk_ = Package.objects.get(pk=b.item_id); pk_.seats = max(0, pk_.seats - b.members); pk_.save()
        return render(request, "core/paid.html", {"b": b})
    return render(request, "core/pay.html", {"form": form, "b": b})

@login_required
def receipt_pdf(request, pk):
    p = get_object_or_404(Payment, booking_id=pk, booking__user=request.user)
    buf = io.BytesIO(); c = canvas.Canvas(buf, pagesize=A4); y = 780
    c.setFont("Helvetica-Bold", 18); c.drawString(60, y, "Dream Travel - Payment Receipt")
    c.setFont("Helvetica", 12)
    for line in (f"Transaction ID: {p.txn_id}", f"Booking: #{p.booking.id} - {p.booking.item_name}",
                 f"Name: {p.booking.name}", f"Quantity: {p.booking.members}", f"Method: {p.method}",
                 f"Amount paid: INR {p.amount}", f"Date: {p.paid_at:%d %b %Y, %I:%M %p}", f"Contact: {p.email} / {p.phone}"):
        y -= 26; c.drawString(60, y, line)
    c.save(); buf.seek(0)
    return FileResponse(buf, as_attachment=True, filename=f"receipt_{p.txn_id}.pdf")

@login_required
def dashboard(request):
    u = request.user
    return render(request, "core/dashboard.html", {"tab": request.GET.get("tab", "bookings"), "reviews": Feedback.objects.filter(user=u), "wishlist": Wishlist.objects.filter(user=u).select_related("package"),
        "bookings": Booking.objects.filter(user=u).order_by("-created"),
        "payments": Payment.objects.filter(booking__user=u).order_by("-paid_at")})

@login_required
def edit_profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    form = ProfileForm(request.POST or None, request.FILES or None, instance=prof,
                       initial={"name": request.user.first_name, "email": request.user.email})
    if form.is_valid():
        form.save(); request.user.first_name = form.cleaned_data["name"]; request.user.email = form.cleaned_data["email"]
        request.user.save(); messages.success(request, "Profile saved."); return redirect("dashboard")
    return render(request, "core/form.html", {"form": form, "title": "Edit profile", "button": "Save profile", "multipart": True})

@login_required
def trip_book(request, pk):
    pkg = get_object_or_404(Package, pk=pk, available=True)
    form = TripForm(request.POST or None, initial={"contact": request.user.email, "vehicle": request.GET.get("vehicle"), "hotel": request.GET.get("hotel")})
    if form.is_valid():
        b = form.save(commit=False); d = form.cleaned_data
        if d["adults"] + d["children"] > pkg.seats:
            form.add_error(None, f"Only {pkg.seats} seats left.")
        else:
            total = pkg.amount * d["adults"] + pkg.amount / 2 * d["children"]  # children pay half
            if d.get("vehicle"): total += d["vehicle"].amount * d["nights"]
            if d.get("room"): total += d["room"].price * d["nights"]
            elif d.get("hotel"): total += d["hotel"].amount * d["nights"]
            b.user, b.kind, b.item_id, b.item_name = request.user, "trip", pkg.pk, str(pkg)
            b.members, b.total = d["adults"] + d["children"], total.quantize(Decimal("0.01"))
            b.save(); return redirect("pay", pk=b.pk)
    return render(request, "core/book.html", {"form": form, "item": pkg, "kind": "trip"})

@login_required
def feedback(request):
    form = FeedbackForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        f = form.save(commit=False); f.user = request.user; f.save()
        messages.success(request, "Thanks for your feedback."); return redirect("feedback")
    return render(request, "core/feedback.html", {"form": form, "reviews": Feedback.objects.select_related("user", "package")[:10]})
