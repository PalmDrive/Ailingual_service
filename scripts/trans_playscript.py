#coding:u8
fname="111.txt"
f = open(fname)

fdname ="111_dst.srt"
fdst = open(fdname,"w+")

index = 0

for i in f:
#    print i
    i = i.strip()
    i=i.decode("utf8")
    if not i.find("]") or len(i)<26:
        continue

    index+=1
    start = i[:13]    
    content = i[13:-13]
    end = i[-13:]
    
    start=start.replace(".",",")
    start=start.replace("]","0]")
    start= start.strip("[]")

    end=end.replace(".",",")
    end=end.replace("]","0]")
    end= end.strip("[]")
    
    print >> fdst, str(index)
    print >> fdst, start," --> ",end
    print >> fdst, content.encode("utf8")
    print >> fdst, ""
    
f.close()
fdst.close()
print "over"