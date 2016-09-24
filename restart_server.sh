echo '---restarting---'
ps -ef|grep 'unix_socket=[1-5].socket' |awk '{print $2}' |xargs kill -9
source ./env/bin/activate
cd xiaobandeng 
nohup python server.py --unix_socket=1.socket &
nohup  python server.py --unix_socket=2.socket &
sleep 1
echo '----restart over--'
