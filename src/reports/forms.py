from django import forms


class ReportUploadForm(forms.Form):
    old_report = forms.FileField(label="Ancien rapport (CSV)")
    new_report = forms.FileField(label="Nouveau rapport (CSV)")

