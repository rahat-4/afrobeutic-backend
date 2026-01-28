# location / {
#     proxy_pass http://localhost:8000;
#     proxy_http_version 1.1;

#     # Add these missing headers
#     proxy_set_header X-Real-IP $remote_addr;
#     proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
#     proxy_set_header X-Forwarded-Proto $scheme;
#     proxy_set_header Host $host;

#     # Keep these
#     proxy_set_header Upgrade $http_upgrade;
#     proxy_set_header Connection 'upgrade';
#     proxy_cache_bypass $http_upgrade;

#     # Add timeout settings for webhooks
#     proxy_connect_timeout 60s;
#     proxy_send_timeout 60s;
#     proxy_read_timeout 60s;
# }
