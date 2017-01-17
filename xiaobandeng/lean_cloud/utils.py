# coding:u8

# for calling leancloud api returns error.
def loop_until_return(n, f, *args, **kwargs):
    for i in range(n):
        print 'trying NO.%s time of %s(%s)' % (i, f, args)
        try:
            return f(*args, **kwargs)
        except Exception:
            pass
    else:
        print '----'*20
        print f,args,kwargs
        print 'tried '+str(n)+'times and failed'
        print '----'*20        
        