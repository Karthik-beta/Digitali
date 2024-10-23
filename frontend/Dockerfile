# Stage 1: Build the Angular application
FROM node:18 AS build

# Set the working directory to /app
WORKDIR /app

# Copy package.json and package-lock.json to /app
COPY sakai-ng/package*.json ./

# Install dependencies
RUN npm install --legacy-peer-deps

# Copy the entire Angular project into the container
COPY sakai-ng/ .

ARG API_URL=http://django:8000 

# Build the app with production configuration
RUN npm run build -- --configuration production --base-href=/ --deploy-url=/ --output-path=dist

# Replace the placeholder in environment.ts within the dist folder
RUN sed -i "s|USE_API_URL_FROM_DOCKER_BUILD|'${API_URL}'|g" dist/sakai-ng/main.js 

# Stage 2: Create the final Nginx image
FROM nginx:stable

# Copy the Nginx configuration file and SSL/TLS certificate and key files
COPY nginx/nginx.conf /etc/nginx/nginx.conf
COPY access_keys/digitali_self_signed.crt /etc/nginx/
COPY access_keys/digitali_private.key /etc/nginx/

# Copy the build output from the previous stage to replace the default Nginx contents
COPY --from=build /app/dist/sakai-ng /usr/share/nginx/html

# Expose port 80 and 443 for HTTP and HTTPS respectively
EXPOSE 80
EXPOSE 443

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]
