# Use a lightweight Node.js image for serving the dashboard
FROM node:20-alpine

# Set the working directory inside the container
WORKDIR /app

# Copy the dashboard source code
COPY dashboard/package*.json ./
RUN npm install

COPY dashboard/ ./
RUN npm run build

# We no longer need global serve. Just run the local Node backend.

# Expose the port (Hugging Face standard is 7860)
EXPOSE 7860

# Serve the built dashboard using our secure backend
CMD ["node", "server.js"]
