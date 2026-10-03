"""Admin pages inside the site UI (staff only): CRUD for packages, vehicles, hotels + bookings/payments."""
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.forms import modelform_factory
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.contrib.auth.models import User
from .forms import AdminProfileForm
from .models import *

staff_required = user_passes_test(lambda u: u.is_authenticated and u.is_staff, login_url="login")
MODELS = {"destinations": Destination, "feedback": Feedback, "packages": Package, "vehicles": Vehicle, "hotels": Hotel}

def _model(kind):
    if kind not in MODELS: raise Http404
    return MODELS[kind]

@staff_required
def dashboard(request):
    return render(request, "core/manage_dashboard.html", {
        "customers": User.objects.filter(is_staff=False).count(), "dests": Destination.objects.count(),
        "counts": [("Tour packages", "packages", Package.objects.count()), ("Vehicles", "vehicles", Vehicle.objects.count()),
                   ("Hotels", "hotels", Hotel.objects.count())],
        "bookings": Booking.objects.count(), "pending": Booking.objects.filter(status="Pending").count(),
        "payments": Payment.objects.count(), "recent": Booking.objects.order_by("-created")[:5]})

@staff_required
def items(request, kind):
    return render(request, "core/manage_list.html", {"items": _model(kind).objects.all().order_by("-pk"), "kind": kind})

@staff_required
def edit_item(request, kind, pk=None):
    Model = _model(kind)
    obj = get_object_or_404(Model, pk=pk) if pk else None
    Form = modelform_factory(Model, exclude=[])
    form = Form(request.POST or None, request.FILES or None, instance=obj)
    if form.is_valid():
        form.save(); messages.success(request, "Saved."); return redirect("manage_items", kind=kind)
    return render(request, "core/form.html", {"form": form, "multipart": True, "button": "Save",
                  "title": ("Edit " if obj else "Add ") + Model._meta.verbose_name})

@staff_required
def delete_item(request, kind, pk):
    obj = get_object_or_404(_model(kind), pk=pk)
    if request.method == "POST":
        obj.delete(); messages.success(request, "Deleted."); return redirect("manage_items", kind=kind)
    return render(request, "core/manage_delete.html", {"obj": obj, "kind": kind})

@staff_required
def bookings(request):
    qs = Booking.objects.select_related("user", "payment").order_by("-created")
    for f in ("kind", "status"):
        if request.GET.get(f): qs = qs.filter(**{f: request.GET[f]})
    return render(request, "core/manage_bookings.html", {"bookings": qs})

@staff_required
def booking_status(request, pk):
    b = get_object_or_404(Booking, pk=pk)
    if request.method == "POST" and request.POST.get("status") in ("Pending", "Confirmed", "Cancelled"):
        b.status = request.POST["status"]; b.save()
    return redirect("manage_bookings")

@staff_required
def payments(request):
    return render(request, "core/manage_payments.html", {"payments": Payment.objects.select_related("booking").order_by("-paid_at")})

@staff_required
def admin_profile(request):
    prof, _ = Profile.objects.get_or_create(user=request.user)
    form = AdminProfileForm(request.POST or None, request.FILES or None, instance=prof,
                            initial={"name": request.user.first_name, "email": request.user.email})
    if form.is_valid():
        form.save(); u = request.user; u.first_name = form.cleaned_data["name"]; u.email = form.cleaned_data["email"]; u.save()
        messages.success(request, "Profile saved."); return redirect("manage")
    return render(request, "core/form.html", {"form": form, "title": "Admin profile", "button": "Save profile", "multipart": True})

@staff_required
def customers(request):
    return render(request, "core/manage_customers.html", {"users": User.objects.filter(is_staff=False).select_related("profile").order_by("-date_joined")})
