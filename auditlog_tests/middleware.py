from auditlog.middleware import AuditlogMiddleware


class CustomAuditlogMiddleware(AuditlogMiddleware):
    """
    Custom Middleware to couple the request's user role to log items.
    """

    def get_extra_data(self, request):
        context_data = super().get_extra_data(request)
        context_data["role"] = "Role 1"
        return context_data
