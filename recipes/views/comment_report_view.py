# views.py
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, redirect
from django.views.decorators.http import require_POST

from recipes.forms import CommentReportForm
from recipes.models import Comment, CommentReport


@login_required
@require_POST
def report_comment(request):
    comment_id = request.POST.get("comment_id")
    comment = get_object_or_404(Comment, id=comment_id)

    # Prevent self-report
    if comment.user == request.user:
        messages.error(request, "You cannot report your own comment.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Bind form
    form = CommentReportForm(request.POST)
    if not form.is_valid():
        messages.error(request, "Please provide a valid reason for the report.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Prevent duplicate reports
    if CommentReport.objects.filter(comment=comment, reporter=request.user).exists():
        messages.info(request, "You have already reported this comment.")
        return redirect(request.META.get("HTTP_REFERER", "/"))

    # Create report
    CommentReport.objects.create(
        comment=comment, reporter=request.user, reason=form.cleaned_data["reason"]
    )
    messages.success(request, "Thank you — the report has been submitted.")
    return redirect(request.META.get("HTTP_REFERER", "/"))
