from django.utils.encoding import filepath_to_uri
from storages.backends.s3 import S3Storage
from storages.utils import clean_name


class SupabaseMediaStorage(S3Storage):
    """Supabase S3 storage whose files live under a folder inside the bucket.

    Files are written to  <bucket>/<location>/<name>  (e.g. media/media/site/photo.jpg),
    but the name kept in the database, and the public URL, stay prefix-free
    (site/photo.jpg), because SUPABASE_PUBLIC_MEDIA_DOMAIN already points inside that folder.
    """

    def url(self, name, parameters=None, expire=None, http_method=None):
        if self.custom_domain and not self.querystring_auth:
            return "{}//{}/{}".format(self.url_protocol, self.custom_domain, filepath_to_uri(clean_name(name)))
        return super().url(name, parameters=parameters, expire=expire, http_method=http_method)