from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    website = forms.CharField(required=False)  # honeypot: real people never fill this

    class Meta:
        model = Review
        fields = ["display_name", "rating", "body"]

    def clean_display_name(self):
        name = self.cleaned_data["display_name"].strip()
        if len(name) < 2:
            raise forms.ValidationError("Add your name so we know who to thank.")
        return name