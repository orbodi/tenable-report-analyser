from django.http import Http404, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render

from .forms import ReportUploadForm
from .models import ReportComparison
from .tenable_compare import compare_reports


def upload_view(request):
    context = {}
    if request.method == "POST":
        form = ReportUploadForm(request.POST, request.FILES)
        if form.is_valid():
            old_report = form.cleaned_data["old_report"]
            new_report = form.cleaned_data["new_report"]

            # Sauvegarde de la comparaison pour historisation
            comparison = ReportComparison.objects.create(
                old_report=old_report,
                new_report=new_report,
                old_name=getattr(old_report, "name", "Ancien rapport"),
                new_name=getattr(new_report, "name", "Nouveau rapport"),
            )

            # Analyse immédiate pour l'affichage
            result = compare_reports(old_report, new_report)

            request.session["comparison_result"] = {
                "per_plugin_patched": result.per_plugin_patched,
                "per_plugin_not_patched": result.per_plugin_not_patched,
                "new_plugins_details": result.new_plugins_details,
            }

            return render(
                request,
                "reports/result.html",
                {
                    "per_plugin_patched": result.per_plugin_patched,
                    "per_plugin_not_patched": result.per_plugin_not_patched,
                    "new_plugins_details": result.new_plugins_details,
                    "comparison": comparison,
                },
            )
    else:
        form = ReportUploadForm()

    context["form"] = form
    context["sidebar_comparisons"] = ReportComparison.objects.all()[:10]
    return render(request, "reports/upload.html", context)


def result_view(request):
    data = request.session.get("comparison_result")
    if not data:
        return render(
            request,
            "reports/result.html",
            {
                "error": "Aucune comparaison en session.",
                "sidebar_comparisons": ReportComparison.objects.all()[:10],
            },
        )

    return render(
        request,
        "reports/result.html",
        {
            "per_plugin_patched": data["per_plugin_patched"],
            "per_plugin_not_patched": data["per_plugin_not_patched"],
            "new_plugins_details": data["new_plugins_details"],
            "sidebar_comparisons": ReportComparison.objects.all()[:10],
        },
    )


def history_view(request):
    comparisons = ReportComparison.objects.all()
    return render(
        request,
        "reports/history.html",
        {
            "comparisons": comparisons,
            "sidebar_comparisons": comparisons[:10],
        },
    )


def comparison_detail(request, pk: int):
    comparison = get_object_or_404(ReportComparison, pk=pk)

    # On relit les fichiers stockés pour recalculer les résultats
    with comparison.old_report.open("rb") as old_f, comparison.new_report.open("rb") as new_f:
        result = compare_reports(old_f, new_f)

    # On alimente aussi la session pour permettre l'export CSV
    request.session["comparison_result"] = {
        "per_plugin_patched": result.per_plugin_patched,
        "per_plugin_not_patched": result.per_plugin_not_patched,
        "new_plugins_details": result.new_plugins_details,
    }

    return render(
        request,
        "reports/result.html",
        {
            "per_plugin_patched": result.per_plugin_patched,
            "per_plugin_not_patched": result.per_plugin_not_patched,
            "new_plugins_details": result.new_plugins_details,
            "comparison": comparison,
            "sidebar_comparisons": ReportComparison.objects.all()[:10],
        },
    )


def delete_comparison(request, pk: int):
    comparison = get_object_or_404(ReportComparison, pk=pk)
    if request.method == "POST":
        comparison.delete()
        return redirect("reports:history")
    return redirect("reports:history")


def export_csv(request, kind: str) -> HttpResponse:
    """
    Exporte en CSV les résultats stockés en session.
    kind: 'patched' | 'not_patched' | 'new_plugins'
    """
    data = request.session.get("comparison_result")
    if not data:
        return HttpResponse(
            "Aucune comparaison disponible. Veuillez d'abord uploader deux rapports.",
            status=400,
            content_type="text/plain; charset=utf-8",
        )

    mapping = {
        "patched": ("per_plugin_patched", "patched_per_plugin.csv"),
        "not_patched": ("per_plugin_not_patched", "not_patched_per_plugin.csv"),
        "new_plugins": ("new_plugins_details", "new_plugins_per_plugin.csv"),
    }

    if kind not in mapping:
        raise Http404("Type d'export inconnu.")

    key, filename = mapping[kind]
    rows = data.get(key, [])

    response = HttpResponse(content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename=\"{filename}\"'

    import csv

    writer = csv.writer(response)
    writer.writerow(["Plugin ID", "CVE", "Host"])
    for item in rows:
        writer.writerow(
            [
                item.get("plugin_id", ""),
                item.get("cve", ""),
                item.get("host", ""),
            ]
        )

    return response

