# coding:utf-8
ECODE = type("ErrorCode", (), {})()

# media
ECODE.ERR_MEDIA_DOWNLOAD_FAILURE = (100003, "Media download error or timeout. Check your media address.")
ECODE.ERR_MEDIA_UNSUPPORTED_FORMAT = (100004, "Media's format is unsupported. Check your media format.")

# user
# 200000-200100
ECODE.ERR_USER_HAVE_APP_INFO = (200001, "app_info already exists")
ECODE.ERR_USER_NO_THAT_USER = (200002, "user not found")
ECODE.ERR_USER_NO_THAT_APP_INFO = (200003, "app_key and app_id not exist")
ECODE.ERR_USER_APP_ID_APP_KEY_NOT_MATCH = (200004,"app_key or appid not match")
ECODE.ERR_COMPANY_NO_THAT_COMPANY = (200002, "company not found")

#transcript
#200500-200500
ECODE.CAPTION_EXISTS_TRANSCRIPT = (200500, "media exists timestamp transcript")