from django import forms


class CommentReportForm(forms.Form):
    reason = forms.CharField(
        widget=forms.Textarea(attrs={"class": "form-control", "rows": 3}),
        max_length=500,
        required=True,
        label="Reason for reporting",
    )
