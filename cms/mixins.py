from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin


class StaffRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """Server-side guard for every dashboard view: logged in AND is_staff."""

    def test_func(self):
        return self.request.user.is_staff
