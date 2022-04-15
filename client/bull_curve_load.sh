python3.8 http_client.py 10.2.12.118 3 5 & PID=$!
sleep 30s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 8 5 & PID=$!
sleep 60s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 15 5 & PID=$!
sleep 60s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 20 5 & PID=$!
sleep 60s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 15 5 & PID=$!
sleep 60s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 8 5 & PID=$!
sleep 60s
kill -HUP $PID

python3.8 http_client.py 10.2.12.118 3 5 & PID=$!
sleep 60s
kill -HUP $PID