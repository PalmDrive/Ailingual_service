# coding:utf-8
ECODE = type("ErrorCode", (), {})()

# media
ECODE.ERR_MEDIA_DOWNLOAD_FAILURE = (100003, "Media download error or timeout. Check your media address.")
ECODE.ERR_MEDIA_UNSUPPORTED_FORMAT = (100004, "Media's format is unsupported. Check your media format.")

# user
# 200000-200100
ECODE.ERR_USER_HAVE_APP_INFO = (200001, "app_info already exists")
ECODE.ERR_USER_NO_THAT_USER = (200002, "user not found")
ECODE.ERR_USER_NO_THAT_APP_INFO = (200003, "app_key and app_id mismatch")

