from django.db import models


class ReportComparison(models.Model):
  created_at = models.DateTimeField(auto_now_add=True)
  old_report = models.FileField(upload_to="reports/")
  new_report = models.FileField(upload_to="reports/")
  old_name = models.CharField(max_length=255)
  new_name = models.CharField(max_length=255)

  class Meta:
    ordering = ["-created_at"]

  def __str__(self) -> str:
    return f"Comparaison {self.pk} - {self.created_at:%Y-%m-%d %H:%M}"

