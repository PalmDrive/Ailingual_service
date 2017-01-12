# coding:u8

# for calling leancloud api returns error.
def loop_until_return(n, f, *args, **kwargs):
    for i in range(n):
        print 'trying NO.%s time of %s(%s)' % (i, f, args)
        try:
            return f(*args, **kwargs)
        except Exception:
            pass