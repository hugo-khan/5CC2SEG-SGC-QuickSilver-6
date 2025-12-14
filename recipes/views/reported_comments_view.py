from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import get_object_or_404, redirect, render

from recipes.models import Comment, CommentReport


@staff_member_required
def reported_comments_view(request):
    if request.method == "POST":
        if "delete_comment" in request.POST:
            comment_id = request.POST.get("comment_id")
            comment = get_object_or_404(Comment, id=comment_id)
            comment.delete()
            messages.success(request, "Comment deleted successfully.")

            # Dismiss report
        elif "dismiss_report" in request.POST:
            report_id = request.POST.get("report_id")
            report = get_object_or_404(CommentReport, id=report_id)
            report.delete()
            messages.success(request, "Report dismissed successfully.")

        return redirect("reported_comments")

    reports = CommentReport.objects.select_related("comment", "reporter").all()
    return render(request, "reported_comments.html", {"reports": reports})
