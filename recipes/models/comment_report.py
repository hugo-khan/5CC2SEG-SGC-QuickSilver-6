from django.db import models
from django.contrib.auth.models import User # double check this
from .comment import Comment


class CommentReport(models.Model):
    # Fields
    comment = models.ForeignKey(Comment,on_delete=models.CASCADE,related_name="reports")
    created_at = models.DateTimeField(auto_now_add=True)
    reporter = models.ForeignKey(User,on_delete=models.CASCADE)
    reason = models.TextField(500)

    class Meta:
        ordering = ["-created_at"] #order
        unique_together = ("comment", "reporter") #stop same user spam reporting on one comment
