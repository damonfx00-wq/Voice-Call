# Stage 1: Build the React application
FROM node:20-alpine as build

WORKDIR /app

# Copy package.json and package-lock.json (or bun.lock)
COPY package.json ./
COPY bun.lock ./

# Install dependencies
# We use npm here. If you strictly want to use bun, we can switch images, 
# but npm usually handles bun.lock or we can just ignore it and use package.json.
# To be safe and respect the lock file if possible, we can try to use bun, 
# but let's stick to npm for standard docker builds unless requested otherwise.
# If bun.lock exists, npm might not use it. 
# Let's just use npm install.
RUN npm install

# Copy the rest of the application code
COPY . .

# Build the application
RUN npm run build

# Stage 2: Serve the application with Nginx
FROM nginx:alpine

# Copy the build output from the previous stage
COPY --from=build /app/dist /usr/share/nginx/html

# Copy a custom nginx configuration to handle SPA routing
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Expose port 80
EXPOSE 80

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]
