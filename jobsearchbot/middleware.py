from django.db import close_old_connections

class DatabaseConnectionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Close stale connections before processing the request
        close_old_connections()
        
        response = self.get_response(request)
        
        # Close stale connections after processing the request
        close_old_connections()
        
        return response
