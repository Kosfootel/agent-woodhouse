FROM nginx:alpine

# Copy built React static files to nginx html directory
COPY build/ /usr/share/nginx/html/

# Create custom nginx config that listens on port 8085
# API calls go directly to backend on host network
RUN echo 'server { \
    listen 8085; \
    server_name localhost; \
    root /usr/share/nginx/html; \
    index index.html; \
    location / { \
        try_files $uri $uri/ /index.html; \
    } \
    location /api { \
        proxy_pass http://192.168.50.30:8000; \
        proxy_set_header Host $host; \
        proxy_set_header X-Real-IP $remote_addr; \
        proxy_set_header Origin $http_origin; \
    } \
    error_page 500 502 503 504 /50x.html; \
    location = /50x.html { \
        root /usr/share/nginx/html; \
    } \
}' > /etc/nginx/conf.d/default.conf

# Expose dashboard port
EXPOSE 8085

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD wget --quiet --tries=1 --spider http://localhost:8085/ || exit 1

# Nginx runs automatically via the base image
CMD ["nginx", "-g", "daemon off;"]
