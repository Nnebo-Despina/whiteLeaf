from django import forms
from django.contrib import messages
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views import View

from core.models import HotelInfo, PublishStatus, SiteImage, SiteText, slot_limit
from core.text_defaults import TEXT_DEFAULTS
from bookings.models import BookingRequest
from core.templatetags.site_tags import tel_link, wa_link
from reviews.models import Review
from rooms.models import Room

from .forms import SiteTextForm, StyledModelForm
from .mixins import StaffRequiredMixin
from .registry import BY_SLUG, SECTIONS


def _section(slug):
    try:
        return BY_SLUG[slug]
    except KeyError:
        raise Http404


def _ensure_texts():
    """Create a row for every editable text the site uses, so the list is never empty."""
    existing = set(SiteText.objects.values_list("key", flat=True))
    new = [SiteText(key=k, label=label, page=page, value=default)
           for k, (label, page, default) in TEXT_DEFAULTS.items() if k not in existing]
    if new:
        SiteText.objects.bulk_create(new)


def _form_class(model, fields, **kw):
    widgets = dict(kw.pop("widgets", {}))
    for f in model._meta.fields:
        if f.name in fields and f.get_internal_type() == "DateField":
            widgets.setdefault(f.name, forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"}))
    for f in model._meta.many_to_many:
        if f.name in fields:
            widgets.setdefault(f.name, forms.CheckboxSelectMultiple)
    return forms.modelform_factory(model, form=StyledModelForm, fields=fields, widgets=widgets, **kw)


def _describe(section, obj):
    """Turn a model instance into a row for the list page."""
    d = {"pk": obj.pk, "thumb": "", "title": str(obj), "subtitle": "", "status": None, "updated": getattr(obj, "updated_at", None)}
    s = section.slug
    if s == "text":
        d.update(subtitle=(obj.draft_value or obj.value)[:90], status=("draft", "Draft waiting") if obj.has_draft else ("live", "Published"))
    elif s == "images":
        d.update(subtitle=obj.get_slot_display(), thumb=obj.image.url if obj.image else "")
    elif s == "bookings":
        hotel_name = HotelInfo.load().name
        nights = f"{obj.nights} night{'s' if obj.nights != 1 else ''}"
        guests = f"{obj.adults} adult{'s' if obj.adults != 1 else ''}" + (f", {obj.children} child{'ren' if obj.children != 1 else ''}" if obj.children else "")
        d.update(
            title=f"{obj.name} · {obj.check_in:%d %b} – {obj.check_out:%d %b %Y}",
            subtitle=f"{obj.reference} · {obj.room_label} · {nights} · {guests} · {obj.phone}",
            status={"new": ("draft", "New"), "contacted": ("info", "Contacted"),
                    "confirmed": ("live", "Confirmed"), "cancelled": ("off", "Cancelled")}[obj.status],
            updated=obj.created_at, booking=True, raw_status=obj.status,
            call=tel_link(obj.phone),
            whatsapp=wa_link(obj.phone, f"Hello {obj.name}, this is {hotel_name} about your booking request {obj.reference}."),
        )
    elif s == "videos":
        d.update(subtitle=f"{obj.get_slot_display()} · {obj.video.name.rsplit('/', 1)[-1]}")
    elif s == "rooms":
        d.update(subtitle=f"₦{obj.price_per_night:,.0f} · {obj.get_category_display()} · {obj.get_availability_display()}", thumb=obj.cover_url)
    elif s == "tariffs":
        d.update(subtitle=f"{obj.items.count()} fees")
    elif s == "reviews":
        d.update(title=f"{obj.display_name} · {obj.rating}★", subtitle=obj.body[:90],
                 status={"pending": ("draft", "Pending"), "approved": ("live", "Approved"), "rejected": ("off", "Rejected")}[obj.status])
    elif s == "nearby":
        d.update(thumb=obj.image_url)
    elif s == "features":
        d.update(subtitle=obj.caption or obj.description[:90], thumb=obj.image_url)
    elif s == "faqs":
        d.update(subtitle=obj.answer[:90])
    elif s == "amenities":
        d.update(subtitle=obj.description)
    elif s == "facilities":
        d.update(subtitle=obj.icon)
    if d["status"] is None:
        if section.mode == "status":
            d["status"] = ("live", "Published") if obj.status == PublishStatus.PUBLISHED else ("draft", "Draft")
        else:
            d["status"] = ("live", "Showing") if getattr(obj, "is_published", True) else ("off", "Hidden")
    return d


class DashboardView(StaffRequiredMixin, View):
    def get(self, request):
        pending = [{"kind": "review", "pk": r.pk, "title": f"Review from {r.display_name}", "when": r.created_at,
                    "section": "reviews", "action": "approve", "label": "Approve", "icon": "message-square"}
                   for r in Review.objects.filter(status="pending")[:5]]
        pending = [{"kind": "booking", "pk": b.pk, "title": f"Booking: {b.name} ({b.check_in:%d %b})", "when": b.created_at,
                    "section": "bookings", "action": "contacted", "label": "Mark contacted", "icon": "calendar-check"}
                   for b in BookingRequest.objects.filter(status="new")[:6]] + pending
        pending += [{"kind": "text", "pk": t.pk, "title": f"Text: {t.label}", "when": t.updated_at,
                     "section": "text", "action": "publish", "label": "Publish", "icon": "type"}
                    for t in SiteText.objects.exclude(draft_value="") if t.has_draft][:5]
        pending += [{"kind": "image", "pk": i.pk, "title": f"Image: {i.title}", "when": i.updated_at,
                     "section": "images", "action": "publish", "label": "Publish", "icon": "image"}
                    for i in SiteImage.objects.filter(status="draft")[:5]]
        pending += [{"kind": "room", "pk": r.pk, "title": f"Room: {r.name}", "when": r.updated_at,
                     "section": "rooms", "action": "publish", "label": "Publish", "icon": "bed-double"}
                    for r in Room.objects.filter(status="draft")[:5]]
        stats = [("calendar-check", BookingRequest.objects.filter(status="new").count(), "New bookings"),
                 ("bed-double", Room.published.count(), "Rooms listed"),
                 ("message-square", Review.objects.filter(status="pending").count(), "Reviews to approve"),
                 ("file-clock", len([p for p in pending if p["kind"] != "booking"]), "Drafts waiting"),
                 ("image", SiteImage.objects.filter(status="published").count(), "Live images"),
                 ("message-circle", Review.objects.approved().count(), "Live reviews")]
        return render(request, "cms/dashboard.html", {"stats": stats, "pending": pending, "page": "dash", "sections": SECTIONS})


class SectionList(StaffRequiredMixin, View):
    def get(self, request, section):
        sec = _section(section)
        if sec.slug == "text":
            _ensure_texts()
        qs = sec.model.objects.all()
        status_tabs = None
        if sec.slug == "reviews":
            qs = qs.order_by("status", "-created_at")
        if sec.slug == "bookings":
            wanted = request.GET.get("status", "")
            counts = {v: sec.model.objects.filter(status=v).count() for v, _ in BookingRequest.Status.choices}
            status_tabs = [("", "All", sec.model.objects.count(), wanted == "")] + [
                (v, label, counts[v], wanted == v) for v, label in BookingRequest.Status.choices]
            if wanted in counts:
                qs = qs.filter(status=wanted)
        rows = [_describe(sec, o) for o in qs]
        ctx = {"sec": sec, "rows": rows, "page": sec.slug, "sections": SECTIONS, "status_tabs": status_tabs}
        if sec.slug == "images":
            used = {}
            for slot in SiteImage.objects.values_list("slot", flat=True):
                used[slot] = used.get(slot, 0) + 1
            ctx["free_slots"] = [label for value, label in SiteImage.Slot.choices if used.get(value, 0) < slot_limit(value)]
        return render(request, "cms/list.html", ctx)


class SectionEdit(StaffRequiredMixin, View):
    """Create (pk=None) or edit one item, with inline formsets for photos / amenities / fees."""

    def _build(self, request, sec, obj):
        if sec.mode == "text":
            initial = {"text": obj.draft_value or obj.value}
            return (SiteTextForm(request.POST or None, initial=initial), [])
        Form = sec.form or _form_class(sec.model, sec.fields)
        form = Form(request.POST or None, request.FILES or None, instance=obj)
        formsets = []
        for child, fields, heading in sec.inlines:
            FS = forms.inlineformset_factory(sec.model, child, form=StyledModelForm, fields=fields, extra=1, can_delete=True)
            formsets.append((heading, FS(request.POST or None, request.FILES or None, instance=obj, prefix=child.__name__.lower())))
        return form, formsets

    def _handle(self, request, section, pk=None):
        sec = _section(section)
        if pk is None and not sec.can_add:
            raise Http404
        obj = get_object_or_404(sec.model, pk=pk) if pk else sec.model()
        form, formsets = self._build(request, sec, obj)
        if request.method == "POST":
            action = request.POST.get("action", "save")
            ok = form.is_valid() and all(fs.is_valid() for _, fs in formsets)
            if ok:
                if sec.mode == "text":
                    text = form.cleaned_data["text"]
                    if action == "publish":
                        obj.value, obj.draft_value = text, ""
                    else:
                        obj.draft_value = text
                    obj.save()
                    messages.success(request, "Published" if action == "publish" else "Saved as draft")
                else:
                    obj = form.save(commit=False)
                    if sec.mode == "status":
                        obj.status = PublishStatus.PUBLISHED if action == "publish" else PublishStatus.DRAFT
                    elif sec.mode == "review" and action in ("approve", "reject"):
                        obj.status = "approved" if action == "approve" else "rejected"
                    obj.save()
                    form.save_m2m()
                    for _, fs in formsets:
                        fs.instance = obj
                        fs.save()
                    messages.success(request, {"publish": "Published", "draft": "Saved as draft", "approve": "Approved",
                                               "reject": "Rejected"}.get(action, "Saved"))
                return redirect("cms:list", section=sec.slug)
            messages.error(request, "Please fix the highlighted fields.")
        return render(request, "cms/form.html", {
            "sec": sec, "form": form, "formsets": formsets, "obj": obj if pk else None,
            "page": sec.slug, "sections": SECTIONS, "is_new": pk is None,
            "text_default": None,
        })

    def get(self, request, section, pk=None):
        return self._handle(request, section, pk)

    def post(self, request, section, pk=None):
        return self._handle(request, section, pk)


class SectionDelete(StaffRequiredMixin, View):
    def post(self, request, section, pk):
        sec = _section(section)
        if not sec.can_delete:
            raise Http404
        get_object_or_404(sec.model, pk=pk).delete()
        messages.success(request, "Deleted")
        return redirect("cms:list", section=sec.slug)


class SectionStatus(StaffRequiredMixin, View):
    """Quick publish / unpublish / approve / reject buttons on lists and the dashboard."""

    def post(self, request, section, pk):
        sec = _section(section)
        obj = get_object_or_404(sec.model, pk=pk)
        action = request.POST.get("action")
        if sec.mode == "text" and action == "publish":
            obj.publish()
        elif sec.mode == "status" and action in ("publish", "unpublish"):
            obj.status = PublishStatus.PUBLISHED if action == "publish" else PublishStatus.DRAFT
            obj.save()
        elif sec.mode == "review" and action in ("approve", "reject", "unpublish"):
            obj.status = {"approve": "approved", "reject": "rejected", "unpublish": "pending"}[action]
            obj.save()
        elif sec.mode == "booking" and action in ("new", "contacted", "confirmed", "cancelled"):
            obj.status = action
            obj.save()
        elif sec.mode == "bool" and action in ("publish", "unpublish"):
            obj.is_published = action == "publish"
            obj.save()
        else:
            raise Http404
        messages.success(request, {"publish": "Published", "unpublish": "Unpublished", "approve": "Approved",
                                   "reject": "Rejected", "new": "Marked as new", "contacted": "Marked as contacted",
                                   "confirmed": "Booking confirmed", "cancelled": "Booking cancelled"}[action])
        return redirect(request.POST.get("next") or reverse("cms:list", args=[sec.slug]))


class HotelEdit(StaffRequiredMixin, View):
    def _form(self, request):
        Form = _form_class(HotelInfo, ["name", "address", "phone", "whatsapp_number", "email", "opening_hours",
                                       "check_in_time", "check_out_time", "instagram_url", "facebook_url",
                                       "map_embed_url", "directions_url"],
                           widgets={"check_in_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"}),
                                    "check_out_time": forms.TimeInput(format="%H:%M", attrs={"type": "time"})})
        return Form(request.POST or None, instance=HotelInfo.objects.first())

    def get(self, request):
        return render(request, "cms/hotel.html", {"form": self._form(request), "page": "hotel", "sections": SECTIONS})

    def post(self, request):
        form = self._form(request)
        if form.is_valid():
            form.save()
            messages.success(request, "Hotel info updated")
            return redirect("cms:hotel")
        messages.error(request, "Please fix the highlighted fields.")
        return render(request, "cms/hotel.html", {"form": form, "page": "hotel", "sections": SECTIONS})
